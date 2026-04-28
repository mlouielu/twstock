import os
import json
import time
import logging
from datetime import datetime, timedelta

# 將上層目錄加入 sys.path，以便確保能引入本機專案的 twstock
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import twstock
from twstock.analytics import BestFourPoint
from telegram_utils import send_telegram_message

# 設定 Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StrategyEngine:
    """
    模組化的策略引擎。未來的 V2 可以在這裡加入 MACD, RSI, KD 等擴充功能。
    """
    def __init__(self, stock):
        self.stock = stock
        self.results = []
        
    def run_best_four_point(self):
        """四大買賣點策略"""
        # 確保有足夠的資料可以計算均線 (至少需要幾天的數據)
        if len(self.stock.price) < 10:
            return None
        
        bfp = BestFourPoint(self.stock)
        result = bfp.best_four_point()
        
        if result:
            is_buy, reason = result
            action = "🟢 買進 (Buy)" if is_buy else "🔴 賣出 (Sell)"
            return f"[{action}] 四大買賣點: {reason}"
        return None

    def run_macd_strategy(self):
        """MACD 波段反轉點策略"""
        from macd import get_macd_signal
        # MACD 需要至少 35 天的資料
        signal = get_macd_signal(self.stock.price)
        return signal

    def run_rsi_kd_strategy(self):
        """RSI 與 KD 指標策略"""
        from tech_indicators import get_rsi_kd_signals
        if len(self.stock.price) < 15:
            return []
        signals = get_rsi_kd_signals(self.stock.price, self.stock.high, self.stock.low)
        return signals

    def run_financial_analyst_scenario(self):
        """財務分析師：風險與報酬情境分析 (Risk-Reward Scenario)"""
        if len(self.stock.price) < 20:
            return None
            
        prices = self.stock.price[-20:] # 近20日價格
        current_price = prices[-1]
        
        # 尋找近期支撐與壓力 (簡單以20日內最低與最高計算)
        support_price = min(prices)
        resistance_price = max(prices)
        
        if current_price <= support_price:
            # 避免除以零或無下行空間
            downside_risk_pct = 0.01
        else:
            downside_risk_pct = (current_price - support_price) / current_price
            
        if current_price >= resistance_price:
            upside_target_pct = 0.01
        else:
            upside_target_pct = (resistance_price - current_price) / current_price
            
        # 風報比 (Risk-Reward Ratio)
        if downside_risk_pct > 0:
            risk_reward_ratio = upside_target_pct / downside_risk_pct
        else:
            risk_reward_ratio = 999.0
            
        # 產生財務分析師風格的建議
        msg = (f"📊 [情境分析] 上行目標: {resistance_price:.1f} (+{upside_target_pct*100:.1f}%), "
               f"下行風險: {support_price:.1f} (-{downside_risk_pct*100:.1f}%), "
               f"風報比: {risk_reward_ratio:.2f}")
               
        # 嚴謹的財務建議：如果風報比大於 2.0，且停損在可控範圍內，才認為是好的潛在機會
        if risk_reward_ratio >= 2.0 and downside_risk_pct < 0.1:
            msg += " ➡️ **風報比優良，建議可考慮建倉**"
        elif downside_risk_pct >= 0.1:
            msg += " ➡️ **⚠️ 下行風險過大 (>10%)，建議觀望**"
            
        return msg

    def run_all(self):
        """執行所有掛載的策略，回傳觸發的訊號清單"""
        messages = []
        
        # 策略 1: 四大買賣點
        msg_bfp = self.run_best_four_point()
        if msg_bfp:
            messages.append(msg_bfp)
            
        # 策略 2: MACD 波段反轉
        msg_macd = self.run_macd_strategy()
        if msg_macd:
            messages.append(msg_macd)
            
        # 策略 3: RSI 與 KD 指標
        msgs_rsikd = self.run_rsi_kd_strategy()
        if msgs_rsikd:
            messages.extend(msgs_rsikd)
            
        # 策略 4: 財務分析師 - 情境與風報比分析
        msg_fa = self.run_financial_analyst_scenario()
        if msg_fa:
            messages.append(msg_fa)
        
        return messages

def load_config(config_path):
    if not os.path.exists(config_path):
        logging.error(f"找不到設定檔: {config_path}")
        return {"watchlist": []}
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_markdown_report(report_data):
    today = datetime.now().strftime("%Y-%m-%d")
    report_lines = [
        f"# 📈 台股代理人每日行動摘要 ({today})",
        "",
        "| 股票代號 | 股票名稱 | 最新收盤價 | 觸發訊號 |",
        "| -------- | -------- | ---------- | -------- |"
    ]
    
    has_action = False
    for item in report_data:
        code = item['code']
        name = item.get('name', 'N/A')
        price = item.get('price', 'N/A')
        signals = item['signals']
        
        if signals:
            has_action = True
            signal_str = "<br>".join(signals)
            ai_insight = item.get("ai_insight")
            if ai_insight:
                signal_str += f"<br><br>🤖 **AI 洞察**: {ai_insight}"
            report_lines.append(f"| {code} | {name} | {price} | {signal_str} |")
            
    if not has_action:
        report_lines.append("| - | - | - | 今日無觸發訊號的標的 |")
        
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*💡 這是一份自動生成的報告，僅供決策輔助，不構成任何投資建議。*")
    return "\n".join(report_lines)

def generate_telegram_report(report_data):
    """
    專為 Telegram HTML Parse Mode 設計的報告排版，
    因為 Telegram 不支援 Markdown 表格。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"📈 <b>台股代理人每日行動摘要 ({today})</b>\n"]
    
    has_action = False
    for item in report_data:
        code = item['code']
        name = item.get('name', 'N/A')
        price = item.get('price', 'N/A')
        signals = item['signals']
        
        if signals:
            has_action = True
            lines.append(f"🔹 <b>{code} {name}</b> (收盤: {price})")
            for sig in signals:
                # 處理原本為了 Markdown 表格加上的 <br> 與 **
                clean_sig = sig.replace('<br>', '\n  └ ').replace('**', '')
                lines.append(f"  └ {clean_sig}")
                
            ai_insight = item.get("ai_insight")
            if ai_insight:
                lines.append(f"  🤖 <b>AI 洞察</b>: {ai_insight}")
                
            lines.append("") # 股票與股票之間的空行
            
    if not has_action:
        lines.append("😴 今日無觸發訊號的標的\n")
        
    lines.append("💡 <i>這是一份自動生成的報告，僅供決策輔助，不構成任何投資建議。</i>")
    
    return "\n".join(lines)

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = load_config(config_path)
    watchlist = config.get("watchlist", [])
    
    if not watchlist:
        logging.warning("觀察清單為空。請在 config.json 裡面加入股票代號。")
        return

    logging.info(f"開始分析 {len(watchlist)} 檔股票...")
    
    report_data = []
    
    for idx, code in enumerate(watchlist):
        logging.info(f"正在抓取並分析 {code} ({idx+1}/{len(watchlist)})...")
        try:
            # 為了讓 MACD 有足夠的資料(>35天)，我們手動拉取近 60 天的資料，不使用預設的截斷邏輯
            stock = twstock.Stock(code, initial_fetch=False)
            before = datetime.now() - timedelta(days=60)
            stock.fetch_from(before.year, before.month)
            
            # 從 twstock 內建字典抓取股票名稱
            stock_info = twstock.codes.get(code)
            stock_name = stock_info.name if stock_info else "未知"
            
            latest_price = stock.price[-1] if stock.price else "N/A"
            
            # 丟入策略引擎計算
            engine = StrategyEngine(stock)
            signals = engine.run_all()
            
            # 🤖 Gemini AI 分析
            # 注意：使用者設定的環境變數可能包含全形字母，我們用通用的 GEMINI_API_TOKEN 或全形版本
            gemini_token = os.environ.get("GEMINI_API_TOKEN") or os.environ.get("ＧEMINI_API_TOKEN")
            ai_insight = None
            if gemini_token and signals:
                from gemini_utils import get_gemini_insight
                logging.info(f"正在呼叫 Gemini 分析 {code}...")
                ai_insight = get_gemini_insight(gemini_token, code, stock_name, latest_price, signals)
            
            report_data.append({
                "code": code,
                "name": stock_name,
                "price": latest_price,
                "signals": signals,
                "ai_insight": ai_insight
            })
            
        except Exception as e:
            logging.error(f"分析 {code} 時發生錯誤: {e}")
            
        # ⚠️ 這是最重要的安全防護: TWSE API 限制每 5 秒 3 個請求。
        # 由於為了 MACD 我們抓了近 60 天(約3個請求)，這裡強制休息 5 秒，確保絕對不會被 Ban。
        time.sleep(5.0)
        
    report_md = generate_markdown_report(report_data)
    
    # 儲存報告
    report_filename = f"report_{datetime.now().strftime('%Y%m%d')}.md"
    report_filepath = os.path.join(os.path.dirname(__file__), report_filename)
    
    with open(report_filepath, 'w', encoding='utf-8') as f:
        f.write(report_md)
        
    logging.info(f"🎉 報告生成完畢: {report_filepath}")
    
    # 同步輸出在終端機，滿足 PRD 的「3 分鐘內決定明天計畫」目標
    print("\n" + "="*60)
    print(report_md)
    print("="*60 + "\n")

    # 執行 Task 1: Telegram 推播
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("telegram_chat_id")
    if bot_token and chat_id:
        logging.info("準備發送 Telegram 推播...")
        report_tg = generate_telegram_report(report_data)
        send_telegram_message(bot_token, chat_id, report_tg)
    elif bot_token and not chat_id:
        logging.warning("⚠️ 有偵測到 TELEGRAM_BOT_TOKEN，但 config.json 中沒有 telegram_chat_id。")
        logging.warning("請先執行 `python agent/telegram_utils.py` 來找出您的 Chat ID，並填入設定檔。")

if __name__ == "__main__":
    main()
