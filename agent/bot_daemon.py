import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import twstock
from main import StrategyEngine, load_config, generate_telegram_report
from entry_evaluator import EntryEvaluator, MarketRegimeEvaluator
from gemini_utils import get_gemini_insight
from telegram_utils import send_telegram_message
from db_utils import get_cached_stock, get_open_positions, get_offline_stock

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
            "🤖 <b>台股智能操盤助理 (實戰獲利導向)</b>\n\n"
            "⚡ <b>實戰獲利決策指令:</b>\n"
            "/action (或 /today) - ⚡ 今日 3 秒操盤決策卡 (買進/停利/停損總結)\n"
            "/top - 🚀 今日高勝率精選標的 (嚴選分數最高與最佳風報比)\n"
            "/alerts - 🚨 持倉警報器 (過熱停利、破線停損警戒名單)\n"
            "/portfolio - 💼 查看持倉損益分級與各股現值\n"
            "/analyze [代號] - 🎯 查詢個股進場/防守/停利規劃 (例: <code>/analyze 2330</code>)\n\n"
            "📋 <b>監控清單管理指令:</b>\n"
            "/list - 查看目前監控名單\n"
            "/add [代號] - 加入監控名單 (例: <code>/add 2330</code>)\n"
            "/remove [代號] - 移除監控名單 (例: <code>/remove 2330</code>)"
        )
        send_telegram_message(bot_token, chat_id, msg)
        
    elif cmd == '/list':
        msg = f"📋 <b>目前監控名單 ({len(watchlist)} 檔)</b>\n" + ", ".join(watchlist)
        send_telegram_message(bot_token, chat_id, msg)
        
    elif cmd == '/add':
        if len(parts) < 2:
            send_telegram_message(bot_token, chat_id, "請提供股票代號，例如: <code>/add 2330</code>")
            return
        code = parts[1]
        if code in watchlist:
            send_telegram_message(bot_token, chat_id, f"⚠️ <b>{code}</b> 已經在監控名單中了！")
        else:
            watchlist.append(code)
            config["watchlist"] = watchlist
            save_config(config_path, config)
            send_telegram_message(bot_token, chat_id, f"✅ 已成功將 <b>{code}</b> 加入監控名單。")
            
    elif cmd == '/remove':
        if len(parts) < 2:
            send_telegram_message(bot_token, chat_id, "請提供股票代號，例如: <code>/remove 2330</code>")
            return
        code = parts[1]
        if code in watchlist:
            watchlist.remove(code)
            config["watchlist"] = watchlist
            save_config(config_path, config)
            send_telegram_message(bot_token, chat_id, f"🗑️ 已將 <b>{code}</b> 從監控名單移除。")
        else:
            send_telegram_message(bot_token, chat_id, f"⚠️ <b>{code}</b> 不在監控名單中。")
            
    elif cmd in ['/action', '/today']:
        send_telegram_message(bot_token, chat_id, "⏳ 正在生成今日 3 秒操盤決策卡與實戰獲利指引，請稍候...")
        try:
            report_data = []
            open_positions = get_open_positions()
            for code in watchlist:
                stock = get_offline_stock(code, days=120)
                stock_info = twstock.codes.get(code)
                stock_name = stock_info.name if stock_info else "未知"
                latest_price = stock.price[-1] if stock.price else "N/A"
                evaluator = EntryEvaluator(stock)
                eval_result = evaluator.evaluate()
                signals = eval_result.get("signals", [])
                report_data.append({
                    "code": code,
                    "name": stock_name,
                    "price": latest_price,
                    "eval": eval_result,
                    "signals": signals
                })
            regime = MarketRegimeEvaluator(report_data).evaluate_market()
            action_msg = generate_telegram_report(report_data, regime, open_positions)
            send_telegram_message(bot_token, chat_id, action_msg)
        except Exception as e:
            logging.error(f"/action 執行失敗: {e}", exc_info=True)
            send_telegram_message(bot_token, chat_id, f"❌ 生成今日行動卡失敗: {e}")

    elif cmd == '/top':
        send_telegram_message(bot_token, chat_id, "⏳ 正在掃描全市場最高勝率與風報比之進場標的...")
        try:
            candidates = []
            for code in watchlist:
                stock = get_offline_stock(code, days=120)
                stock_info = twstock.codes.get(code)
                stock_name = stock_info.name if stock_info else "未知"
                latest_price = stock.price[-1] if stock.price else "N/A"
                if latest_price == "N/A":
                    continue
                evaluator = EntryEvaluator(stock)
                ev = evaluator.evaluate()
                if ev.get("score", 0) >= 60 and ev.get("rrr", 0) >= 1.2:
                    candidates.append({
                        "code": code,
                        "name": stock_name,
                        "price": latest_price,
                        "eval": ev
                    })
            candidates.sort(key=lambda x: (x["eval"].get("score", 0), x["eval"].get("rrr", 0)), reverse=True)
            
            if not candidates:
                send_telegram_message(bot_token, chat_id, "😴 <b>今日市場無符合高勝率 (評分>=60且風報比>=1.2) 之進場標的，建議保留現金觀望。</b>")
                return
                
            msg = "🚀 <b>【今日高勝率精選進場標的 TOP】</b>\n────────────────────\n"
            for p in candidates[:3]:
                ev = p["eval"]
                curr_p = p["price"]
                sl = ev.get("stop_loss", 0.0)
                target = ev.get("upside_target", 0.0)
                rrr = ev.get("rrr", 1.0)
                score = ev.get("score", 0)
                entry_s = ev.get("suggested_entry", "分批進場")
                badge = ev.get("verdict_badge", "🟢 可進場")
                down_pct = (sl - curr_p) / curr_p * 100 if curr_p else 0.0
                up_pct = (target - curr_p) / curr_p * 100 if curr_p else 0.0
                
                msg += (
                    f"🔹 <b>{p['code']} {p['name']}</b> (現價: {curr_p})\n"
                    f"  ├ 評級: <b>{badge}</b> (評分: <code>{score}</code>)\n"
                    f"  ├ 🎯 <b>策略</b>: {entry_s}\n"
                    f"  ├ 🛡️ 防守: <code>{sl:.2f}</code> ({down_pct:.1f}%) ➡️ 🏆 目標: <code>{target:.2f}</code> ({up_pct:+.1f}%)\n"
                    f"  └ ⚖️ <b>風報比</b>: <b>{rrr:.2f}</b> (每承擔 1 元風險，期望賺取 {rrr:.2f} 元)\n\n"
                )
            send_telegram_message(bot_token, chat_id, msg)
        except Exception as e:
            logging.error(f"/top 執行失敗: {e}", exc_info=True)
            send_telegram_message(bot_token, chat_id, f"❌ 查詢失敗: {e}")

    elif cmd == '/alerts':
        open_positions = get_open_positions()
        if not open_positions:
            send_telegram_message(bot_token, chat_id, "💼 目前無持倉，無警報。")
            return
            
        send_telegram_message(bot_token, chat_id, "⏳ 正在檢視持倉過熱停利與破線停損警報...")
        try:
            take_profit_items = []
            stop_loss_items = []
            
            for p_code, p_data in open_positions.items():
                p_price = p_data["buy_price"]
                p_shares = p_data.get("buy_shares", 0)
                stock = get_offline_stock(p_code, days=120)
                s_info = twstock.codes.get(p_code)
                stock_name = s_info.name if s_info else "未知"
                curr_price = stock.price[-1] if stock.price else None
                
                if curr_price is not None:
                    cost = p_price * p_shares
                    m_val = curr_price * p_shares
                    profit_amt = m_val - cost
                    roi = (profit_amt / cost * 100) if cost > 0 else 0.0
                    
                    ev = EntryEvaluator(stock).evaluate()
                    score = ev.get('score', 50)
                    sl = ev.get('stop_loss', 0.0)
                    verdict = ev.get('verdict', '')
                    signals = ev.get('signals', [])
                    signals_str = " ".join(signals)
                    
                    # 停利條件
                    if roi >= 20.0 and ("死亡交叉" in signals_str or "超買" in signals_str):
                        take_profit_items.append(f"• 💰 <b>{p_code} {stock_name}</b>: 現價 {curr_price:.2f} (<b>{roi:+.2f}%</b>, {profit_amt:+,.0f}元)\n  └ ⚠️ <i>高檔KD死叉/超買，建議獲利入袋 1/2！</i>")
                    elif roi >= 100.0:
                        take_profit_items.append(f"• 💰 <b>{p_code} {stock_name}</b>: 現價 {curr_price:.2f} (<b>{roi:+.2f}%</b>, {profit_amt:+,.0f}元)\n  └ ⚠️ <i>波段獲利已翻倍，建議分批減碼落袋為安！</i>")
                        
                    # 停損/減碼條件
                    if ("不宜" in verdict or "嚴禁" in verdict or score < 42 or curr_price < sl) and roi < 0:
                        stop_loss_items.append(f"• 🛑 <b>{p_code} {stock_name}</b>: 現價 {curr_price:.2f} (<b>{roi:+.2f}%</b>, {profit_amt:+,.0f}元)\n  └ ⚠️ <i>跌破防守價 ({sl:.2f}) 或空頭排列，建議減碼防守！</i>")
                    elif ("不宜" in verdict or "嚴禁" in verdict or score < 42) and roi < 5.0:
                        stop_loss_items.append(f"• 🛑 <b>{p_code} {stock_name}</b>: 現價 {curr_price:.2f} (<b>{roi:+.2f}%</b>, {profit_amt:+,.0f}元)\n  └ ⚠️ <i>動能不足偏弱，建議縮減部位回收資金！</i>")
                        
            if not take_profit_items and not stop_loss_items:
                send_telegram_message(bot_token, chat_id, "🎉 <b>目前持倉全部健康！無觸發停損或過熱停利警報。</b>")
                return
                
            msg = "🚨 <b>【持倉獲利管理與風控警報清單】</b>\n────────────────────\n"
            if take_profit_items:
                msg += "💰 <b>建議獲利了結部位 (Take Profit):</b>\n" + "\n".join(take_profit_items) + "\n\n"
            if stop_loss_items:
                msg += "🛑 <b>建議停損減碼部位 (Stop Loss):</b>\n" + "\n".join(stop_loss_items) + "\n\n"
                
            send_telegram_message(bot_token, chat_id, msg)
        except Exception as e:
            logging.error(f"/alerts 執行失敗: {e}", exc_info=True)
            send_telegram_message(bot_token, chat_id, f"❌ 警報檢查失敗: {e}")
            
    elif cmd == '/portfolio':
        open_positions = get_open_positions()
        if not open_positions:
            send_telegram_message(bot_token, chat_id, "💼 <b>目前無持倉。</b>")
            return
            
        send_telegram_message(bot_token, chat_id, "⏳ 正在彙整持倉損益與分級狀態...")
        
        warn_lines = []
        winner_lines = []
        steady_lines = []
        total_cost = 0.0
        total_market_val = 0.0
        
        for p_code, p_data in open_positions.items():
            p_price = p_data["buy_price"]
            p_shares = p_data.get("buy_shares", 0)
            s_info = twstock.codes.get(p_code)
            stock_name = s_info.name if s_info else "未知"
            
            try:
                stock = get_offline_stock(p_code, days=120)
                curr_price = stock.price[-1] if stock.price else None
                if curr_price is not None:
                    cost = p_price * p_shares
                    m_val = curr_price * p_shares
                    total_cost += cost
                    total_market_val += m_val
                    profit_amt = m_val - cost
                    roi = (profit_amt / cost * 100) if cost > 0 else 0.0
                    
                    ev = EntryEvaluator(stock).evaluate()
                    badge = ev.get('verdict_badge', '')
                    sl = ev.get('stop_loss', 0.0)
                    signals = ev.get('signals', [])
                    signals_str = " ".join(signals)
                    
                    item_text = f"• <b>{p_code} {stock_name}</b>: {p_price:.2f} ➡️ {curr_price:.2f} ({p_shares:,}股, <b>{roi:+.2f}%</b>, {profit_amt:+,.0f}元)"
                    
                    if (roi >= 20.0 and ("死亡交叉" in signals_str or "超買" in signals_str)) or roi >= 100.0:
                        warn_lines.append(f"{item_text} [💰 <b>停利警戒</b>]")
                    elif ("不宜" in ev.get('verdict', '') or curr_price < sl) and roi < 0:
                        warn_lines.append(f"{item_text} [🛑 <b>破線停損</b>]")
                    elif roi >= 15.0:
                        winner_lines.append(f"{item_text} [🏃‍♂️ <b>強勢續抱</b>]")
                    else:
                        steady_lines.append(f"{item_text} [{badge}]")
                else:
                    steady_lines.append(f"• <b>{p_code} {stock_name}</b>: 買入 {p_price:.2f} ➡️ 目前 N/A ({p_shares:,}股)")
            except Exception as e:
                steady_lines.append(f"• <b>{p_code} {stock_name}</b>: 抓取失敗 ({e})")
                
        total_profit = total_market_val - total_cost
        total_roi = (total_profit / total_cost * 100) if total_cost > 0 else 0.0
        
        msg = (
            f"💼 <b>實際持倉投資組合狀態 (共 {len(open_positions)} 檔)</b>\n"
            f"💰 總成本: <b>{total_cost:,.0f} 元</b> | 總現值: <b>{total_market_val:,.0f} 元</b>\n"
            f"📈 總未實現損益: <b>{total_roi:+.2f}% ({total_profit:+,.0f} 元)</b>\n"
            f"────────────────────\n"
        )
        if warn_lines:
            msg += "🚨 <b>需關注調節部位 (停利/停損):</b>\n" + "\n".join(warn_lines) + "\n\n"
        if winner_lines:
            msg += "💎 <b>獲利奔馳部位 (續抱):</b>\n" + "\n".join(winner_lines) + "\n\n"
        if steady_lines:
            msg += "📋 <b>平穩部位:</b>\n" + "\n".join(steady_lines)
            
        send_telegram_message(bot_token, chat_id, msg)
        
    elif cmd == '/analyze':
        if len(parts) < 2:
            send_telegram_message(bot_token, chat_id, "請提供股票代號，例如: <code>/analyze 2330</code>")
            return
        code = parts[1]
        send_telegram_message(bot_token, chat_id, f"⏳ 正在分析 <b>{code}</b> 進場指引與獲利規劃...")
        
        try:
            stock = get_offline_stock(code, days=120)
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
            
            down_pct = (sl - latest_price) / latest_price * 100 if isinstance(latest_price, (int, float)) and latest_price > 0 else 0.0
            up_pct = (target - latest_price) / latest_price * 100 if isinstance(latest_price, (int, float)) and latest_price > 0 else 0.0
            
            msg = (
                f"🎯 <b>{code} {stock_name} 實戰獲利決策指引</b>\n"
                f"────────────────────\n"
                f"⚡ <b>操盤決策</b>: <b>{badge}</b> (評分: <code>{score}/100</code>)\n"
                f"💰 <b>最新收盤</b>: <code>{latest_price}</code>\n"
                f"🎯 <b>進場規劃</b>: {entry_s}\n"
                f"🛡️ <b>防守停損</b>: <code>{sl:.2f}</code> ({down_pct:.1f}%)\n"
                f"🏆 <b>目標停利</b>: <code>{target:.2f}</code> ({up_pct:+.1f}%)\n"
                f"⚖️ <b>潛在風報比</b>: <b>{rrr:.2f}</b> (每承擔 1 元風險，期望賺取 {rrr:.2f} 元)\n\n"
            )
            
            if signals:
                msg += "<b>關鍵訊號:</b>\n"
                for sig in signals[:4]:
                    clean_sig = sig.replace('**', '')
                    msg += f"• {clean_sig}\n"
                    
            if ai_insight:
                msg += f"\n🤖 <b>首席 AI 實戰洞察:</b>\n{ai_insight}"
                
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
