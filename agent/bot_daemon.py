import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import twstock
from main import StrategyEngine, load_config
from entry_evaluator import EntryEvaluator
from gemini_utils import get_gemini_insight
from telegram_utils import send_telegram_message
from db_utils import get_cached_stock, get_open_positions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_config(config_path, config):
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def handle_command(text, bot_token, chat_id):
    parts = text.strip().split()
    cmd = parts[0].lower()
    
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = load_config(config_path)
    watchlist = config.get("watchlist", [])
    
    if cmd in ['/help', '/start']:
        msg = (
            "🤖 <b>台股智能助理指令清單</b>\n\n"
            "/list - 查看目前觀察名單\n"
            "/add [代號] - 加入觀察名單 (例: <code>/add 2330</code>)\n"
            "/remove [代號] - 移除觀察名單 (例: <code>/remove 2330</code>)\n"
            "/analyze [代號] - 即時進場指引分析 (例: <code>/analyze 2330</code>)\n"
            "/portfolio - 查看目前虛擬持倉績效"
        )
        send_telegram_message(bot_token, chat_id, msg)
        
    elif cmd == '/list':
        msg = f"📋 <b>目前觀察名單 ({len(watchlist)} 檔)</b>\n" + ", ".join(watchlist)
        send_telegram_message(bot_token, chat_id, msg)
        
    elif cmd == '/add':
        if len(parts) < 2:
            send_telegram_message(bot_token, chat_id, "請提供股票代號，例如: <code>/add 2330</code>")
            return
        code = parts[1]
        if code in watchlist:
            send_telegram_message(bot_token, chat_id, f"⚠️ <b>{code}</b> 已經在觀察名單中了！")
        else:
            watchlist.append(code)
            config["watchlist"] = watchlist
            save_config(config_path, config)
            send_telegram_message(bot_token, chat_id, f"✅ 已成功將 <b>{code}</b> 加入觀察名單。")
            
    elif cmd == '/remove':
        if len(parts) < 2:
            send_telegram_message(bot_token, chat_id, "請提供股票代號，例如: <code>/remove 2330</code>")
            return
        code = parts[1]
        if code in watchlist:
            watchlist.remove(code)
            config["watchlist"] = watchlist
            save_config(config_path, config)
            send_telegram_message(bot_token, chat_id, f"🗑️ 已將 <b>{code}</b> 從觀察名單移除。")
        else:
            send_telegram_message(bot_token, chat_id, f"⚠️ <b>{code}</b> 不在觀察名單中。")
            
    elif cmd == '/portfolio':
        open_positions = get_open_positions()
        if not open_positions:
            send_telegram_message(bot_token, chat_id, "💼 <b>目前無持倉。</b>")
            return
            
        msg = "💼 <b>目前虛擬投資組合狀態</b>\n\n"
        for p_code, p_data in open_positions.items():
            p_price = p_data["buy_price"]
            before = datetime.now() - timedelta(days=10)
            try:
                stock = get_cached_stock(p_code, before.year, before.month)
                curr_price = stock.price[-1] if stock.price else None
                if curr_price is not None:
                    roi = (curr_price - p_price) / p_price * 100
                    msg += f"• {p_code}: 買入 {p_price:.2f} ➡️ 目前 {curr_price:.2f} (<b>{roi:+.2f}%</b>)\n"
                else:
                    msg += f"• {p_code}: 買入 {p_price:.2f} ➡️ 目前 N/A\n"
            except Exception as e:
                msg += f"• {p_code}: 抓取失敗 ({e})\n"
                
        send_telegram_message(bot_token, chat_id, msg)
        
    elif cmd == '/analyze':
        if len(parts) < 2:
            send_telegram_message(bot_token, chat_id, "請提供股票代號，例如: <code>/analyze 2330</code>")
            return
        code = parts[1]
        send_telegram_message(bot_token, chat_id, f"⏳ 正在分析 <b>{code}</b> 進場指引，請稍候...")
        
        try:
            before = datetime.now() - timedelta(days=120)
            stock = get_cached_stock(code, before.year, before.month)
            stock_info = twstock.codes.get(code)
            stock_name = stock_info.name if stock_info else "未知"
            latest_price = stock.price[-1] if stock.price else "N/A"
            
            evaluator = EntryEvaluator(stock)
            eval_result = evaluator.evaluate()
            signals = eval_result.get("signals", [])
            
            gemini_token = os.environ.get("GEMINI_API_TOKEN") or os.environ.get("ＧEMINI_API_TOKEN")
            ai_insight = None
            if gemini_token and signals:
                ai_insight = get_gemini_insight(gemini_token, code, stock_name, latest_price, signals, eval_dict=eval_result)
                
            badge = eval_result.get("verdict_badge", "🟡 建議觀望")
            score = eval_result.get("score", 50)
            rrr = eval_result.get("rrr", 1.0)
            entry_s = eval_result.get("suggested_entry", "")
            sl = eval_result.get("stop_loss", 0.0)
            target = eval_result.get("upside_target", 0.0)
            
            msg = (f"🎯 <b>{code} {stock_name} 進場指引分析</b>\n"
                   f"────────────────────\n"
                   f"⚡ <b>是否可進場</b>: <b>{badge}</b>\n"
                   f"📊 <b>進場評分</b>: <code>{score}/100</code> | <b>風報比</b>: <code>{rrr:.2f}</code>\n"
                   f"💰 <b>最新收盤</b>: {latest_price}\n"
                   f"🎯 <b>進場策略</b>: {entry_s}\n"
                   f"🛡️ <b>防守停損</b>: {sl:.2f} ➡️ <b>目標價</b>: {target:.2f}\n\n")
            
            if signals:
                msg += "<b>技術面與情境訊號:</b>\n"
                for sig in signals:
                    clean_sig = sig.replace('**', '')
                    msg += f"• {clean_sig}\n"
                    
            if ai_insight:
                msg += f"\n🤖 <b>AI 實戰洞察:</b>\n{ai_insight}"
                
            send_telegram_message(bot_token, chat_id, msg)
            
        except Exception as e:
            logging.error(f"分析失敗: {e}", exc_info=True)
            send_telegram_message(bot_token, chat_id, f"❌ 分析 <b>{code}</b> 時發生錯誤: {str(e)}")

def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logging.error("找不到 TELEGRAM_BOT_TOKEN 環境變數")
        return
        
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = load_config(config_path)
    allowed_chat_id = config.get("telegram_chat_id")
    
    if not allowed_chat_id:
        logging.error("找不到 telegram_chat_id。請確保 config.json 中有設定，避免機器人被陌生人使用。")
        return
        
    offset = None
    timeout = 30
    
    logging.info("🤖 台股智能助理 (Telegram Bot Daemon) 已啟動，等待指令中...")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            params = {"timeout": timeout, "allowed_updates": ["message"]}
            if offset:
                params["offset"] = offset
                
            resp = requests.get(url, params=params, timeout=timeout + 5)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("ok"):
                for update in data.get("result", []):
                    update_id = update["update_id"]
                    offset = update_id + 1
                    
                    message = update.get("message")
                    if not message or "text" not in message:
                        continue
                        
                    chat_id = message["chat"]["id"]
                    text = message["text"]
                    
                    # 安全機制：只回應授權的 chat_id
                    if str(chat_id) != str(allowed_chat_id):
                        logging.warning(f"拒絕來自未授權 Chat ID 的請求: {chat_id}")
                        continue
                        
                    if text.startswith("/"):
                        logging.info(f"收到指令: {text}")
                        handle_command(text, bot_token, chat_id)
                        
        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.RequestException as e:
            logging.error(f"網路連線錯誤: {e}")
            time.sleep(5)
        except Exception as e:
            logging.error(f"未預期的錯誤: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
