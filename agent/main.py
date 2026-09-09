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
from entry_evaluator import EntryEvaluator, MarketRegimeEvaluator

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

def generate_markdown_report(report_data, market_stats=None):
    today = datetime.now().strftime("%Y-%m-%d")
    report_lines = [
        f"# 📈 台股代理人每日行動與進場指引 ({today})",
        ""
    ]
    
    # ── 1. 總體大盤進場指引 ─────────────────────────────
    if market_stats:
        m_verdict = market_stats.get("market_verdict", "🟡 觀望等待")
        can_enter = market_stats.get("can_enter_market", False)
        can_enter_text = "🟢 **可以進場** (擇優分批佈局)" if can_enter else "🔴 **暫緩進場** (嚴控持股風險)"
        suggested_exp = market_stats.get("suggested_exposure", "30% ~ 50%")
        bull_ma20 = market_stats.get("bull_ratio_ma20", 0.0)
        bull_ma60 = market_stats.get("bull_ratio_ma60", 0.0)
        buy_cnt = market_stats.get("buy_count", 0)
        wait_cnt = market_stats.get("wait_count", 0)
        sell_cnt = market_stats.get("sell_count", 0)
        summary = market_stats.get("summary", "")
        macro_ai = market_stats.get("macro_ai_insight")
        
        report_lines.extend([
            "## 🎯 每日股市總體進場指引 (Market Entry Guidance)",
            "| 評估項目 | 評定狀態 | 說明與具體指引 |",
            "| :--- | :--- | :--- |",
            f"| **今日大盤進場環境** | **{m_verdict}** | **{can_enter_text}** |",
            f"| **建議資金持倉水位** | **{suggested_exp}** | 依市場氛圍動態控管資金，嚴設防守點 |",
            f"| **市場多空廣度** | **{bull_ma20:.0f}% 站上月線** | 季線之上: {bull_ma60:.0f}% ／ 可進場: {buy_cnt} 檔 ／ 觀望: {wait_cnt} 檔 ／ 減碼: {sell_cnt} 檔 |",
            "",
            f"> 💡 **操盤總結**: {summary}"
        ])
        
        if macro_ai:
            report_lines.extend([
                f"> 🤖 **首席 AI 宏觀洞察**: {macro_ai}"
            ])
        report_lines.append("")
        
        # ── 2. 今日精選可進場標的推薦專區 ─────────────────────
        report_lines.append("## 🚀 今日精選【可進場標的推薦專區】")
        top_picks = market_stats.get("top_picks", [])
        if top_picks:
            report_lines.extend([
                "| 股票代號/名稱 | 最新收盤 | 進場評級 | 評分 | 風報比 | 建議進場策略 | 防守停損價 | 上行目標價 | 核心理由 |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
            ])
            for p in top_picks:
                p_code = p["code"]
                p_name = p.get("name", "N/A")
                p_price = p.get("price", "N/A")
                ev = p.get("eval", {})
                badge = ev.get("verdict_badge", "🟢 可進場")
                score = ev.get("score", 0)
                rrr = ev.get("rrr", 1.0)
                entry_s = ev.get("suggested_entry", "分批進場")
                sl = ev.get("stop_loss", 0.0)
                target = ev.get("upside_target", 0.0)
                reasons_s = "、".join(ev.get("reasons", [])[:2])
                report_lines.append(
                    f"| **{p_code} {p_name}** | {p_price} | {badge} | {score} | {rrr:.2f} | {entry_s} | {sl:.2f} | {target:.2f} | {reasons_s} |"
                )
        else:
            report_lines.append("> 🛡️ **今日市場無符合嚴格標準 (評分>=65且無一票否決) 之進場標的，建議多看少做、保留現金。**")
            
        report_lines.append("")
        
    # ── 3. 全體觀察名單進場決策儀表板 ────────────────────────
    report_lines.extend([
        "## 📊 全體觀察名單進場決策儀表板",
        "| 股票代號 | 股票名稱 | 最新收盤 | 是否可進場 | 評分 | 風報比 | 建議進場 / 防守點 | 關鍵技術訊號與 AI 洞察 |",
        "| -------- | -------- | -------- | ---------- | ---- | ------ | ------------------ | ---------------------- |"
    ])
    
    for item in report_data:
        code = item['code']
        name = item.get('name', 'N/A')
        price = item.get('price', 'N/A')
        ev = item.get('eval', {})
        badge = ev.get('verdict_badge', '🟡 觀望')
        score = ev.get('score', 50)
        rrr = ev.get('rrr', 1.0)
        entry_s = ev.get('suggested_entry', '觀望')
        sl = ev.get('stop_loss', 0.0)
        target = ev.get('upside_target', 0.0)
        signals = item.get('signals', [])
        ai_insight = item.get("ai_insight")
        
        detail_lines = []
        if signals:
            detail_lines.append("<br>".join(signals))
        if ai_insight:
            detail_lines.append(f"<br>🤖 **AI 洞察**: {ai_insight}")
            
        detail_str = "".join(detail_lines) if detail_lines else "無特殊訊號"
        plan_str = f"🎯 進場: {entry_s}<br>🛡️ 防守: {sl:.2f} ➡️ 目標: {target:.2f}"
        
        report_lines.append(f"| {code} | {name} | {price} | **{badge}** | {score} | {rrr:.2f} | {plan_str} | {detail_str} |")
        
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*💡 這是一份自動生成的報告，僅供決策輔助，不構成任何投資建議。*")
    return "\n".join(report_lines)

def generate_telegram_report(report_data, market_stats=None):
    """
    專為 Telegram HTML Parse Mode 設計的高資訊密度推播排版
    清晰呈現：今日總體進場指引、推薦進場標的、各股進場燈號
    """
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"🎯 <b>台股代理人每日股市指引 ({today})</b>\n"]
    
    if market_stats:
        m_verdict = market_stats.get("market_verdict", "🟡 觀望等待")
        can_enter = market_stats.get("can_enter_market", False)
        can_enter_str = "🟢 <b>可以進場 (擇優佈局)</b>" if can_enter else "🔴 <b>暫緩進場 (保守防禦)</b>"
        suggested_exp = market_stats.get("suggested_exposure", "30% ~ 50%")
        bull_ma20 = market_stats.get("bull_ratio_ma20", 0.0)
        buy_cnt = market_stats.get("buy_count", 0)
        wait_cnt = market_stats.get("wait_count", 0)
        sell_cnt = market_stats.get("sell_count", 0)
        macro_ai = market_stats.get("macro_ai_insight")
        
        lines.append(f"⚡ <b>【今日總體進場指引】</b>")
        lines.append(f"• <b>大盤環境</b>: {m_verdict}")
        lines.append(f"• <b>進場指引</b>: {can_enter_str}")
        lines.append(f"• <b>建議水位</b>: <code>{suggested_exp}</code>")
        lines.append(f"• <b>多空廣度</b>: {bull_ma20:.0f}% 站上月線 (可進場: {buy_cnt} / 觀望: {wait_cnt} / 減碼: {sell_cnt})")
        
        if macro_ai:
            lines.append(f"• 🤖 <b>AI 總經</b>: <i>{macro_ai}</i>")
            
        lines.append("")
        
        # 精選進場標的
        top_picks = market_stats.get("top_picks", [])
        lines.append(f"🚀 <b>【今日精選可進場標的】</b>")
        if top_picks:
            for p in top_picks[:5]:
                ev = p.get("eval", {})
                lines.append(f"🔹 <b>{p['code']} {p.get('name', '')}</b> (收盤: {p.get('price', '')})")
                lines.append(f"  └ 評級: <b>{ev.get('verdict_badge', '')}</b> (評分: {ev.get('score', 0)}, 風報比: {ev.get('rrr', 1.0):.2f})")
                lines.append(f"  └ 🎯 策略: {ev.get('suggested_entry', '')}")
                lines.append(f"  └ 🛡️ 防守: {ev.get('stop_loss', 0.0):.2f} ➡️ 目標: {ev.get('upside_target', 0.0):.2f}")
                ai_in = p.get("ai_insight")
                if ai_in:
                    lines.append(f"  └ 🤖 AI: {ai_in}")
                lines.append("")
        else:
            lines.append("😴 今日無符合嚴選進場標準的標的，建議空手或觀望。\n")
            
    # 全體觀察股速查燈號
    lines.append("📋 <b>【觀察股進場燈號一覽】</b>")
    for item in report_data:
        ev = item.get("eval", {})
        badge = ev.get("verdict_badge", "🟡 觀望")
        score = ev.get("score", 50)
        rrr = ev.get("rrr", 1.0)
        lines.append(f"• {item['code']} {item.get('name', '')}: <b>{badge}</b> ({score}分, 風報比: {rrr:.2f})")
        
    lines.append("\n💡 <i>這是一份自動生成的報告，僅供決策輔助，不構成任何投資建議。</i>")
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
    
    # 載入目前的虛擬持倉
    from db_utils import get_open_positions, record_buy, record_sell
    open_positions = get_open_positions()
    
    gemini_token = os.environ.get("GEMINI_API_TOKEN") or os.environ.get("ＧEMINI_API_TOKEN")
    
    for idx, code in enumerate(watchlist):
        logging.info(f"正在抓取並分析 {code} ({idx+1}/{len(watchlist)})...")
        try:
            # 拉取近 120 天資料，確保有足夠的交易日數計算季線 (MA60) 與趨勢健康度
            from db_utils import get_cached_stock
            before = datetime.now() - timedelta(days=120)
            stock = get_cached_stock(code, before.year, before.month)
            
            stock_info = twstock.codes.get(code)
            stock_name = stock_info.name if stock_info else "未知"
            latest_price = stock.price[-1] if stock.price else "N/A"
            
            # 使用全新 EntryEvaluator 進行全面量化進場裁決
            evaluator = EntryEvaluator(stock)
            eval_result = evaluator.evaluate()
            signals = eval_result.get("signals", [])
            
            # 績效追蹤模組邏輯（對齊嚴謹的進場與出場規則）
            if latest_price != "N/A" and stock.date:
                today_date = stock.date[-1]
                can_enter = eval_result.get("can_enter", False)
                verdict = eval_result.get("verdict", "")
                stop_loss = eval_result.get("stop_loss", 0.0)
                score = eval_result.get("score", 50)
                
                # 平倉條件：被評為不宜進場/嚴禁進場、分數低於45、或跌破防守停損價
                should_sell = ("不宜" in verdict) or ("嚴禁" in verdict) or (score < 45) or (latest_price < stop_loss)
                
                if code in open_positions:
                    if should_sell:
                        record_sell(code, today_date, latest_price)
                        p_shares = open_positions[code].get("buy_shares", 0)
                        profit = (latest_price - open_positions[code]["buy_price"]) * p_shares * 0.995
                        signals.append(f"✅ [虛擬平倉] 以 {latest_price} 賣出 (觸發防守或評級降級，預估獲利: {profit:.0f} 元)")
                        del open_positions[code]
                else:
                    # 建倉條件：嚴格符合 can_enter (分數>=65且無一票否決)
                    if can_enter:
                        total_capital = config.get("total_capital", 1000000)
                        risk_pct = config.get("risk_per_trade_pct", 1.0) / 100.0
                        risk_amount = total_capital * risk_pct
                        
                        from tech_indicators import calculate_atr
                        atr = calculate_atr(stock.price, stock.high, stock.low, period=14)
                        if atr:
                            sl_dist = 1.5 * atr
                        else:
                            sl_dist = latest_price * 0.05
                            
                        buy_shares = int(risk_amount / sl_dist) if sl_dist > 0 else 0
                        max_shares = int(total_capital / latest_price)
                        buy_shares = min(buy_shares, max_shares)
                        
                        if buy_shares > 0:
                            record_buy(code, today_date, latest_price, buy_shares)
                            signals.append(f"✅ [虛擬建倉] 以 {latest_price} 買進 (進場評分: {score}，建議: {buy_shares} 股)")
                            open_positions[code] = {"buy_price": latest_price, "buy_shares": buy_shares}
            
            # 🤖 Gemini AI 分析 (傳入 eval_result 以獲得明確進場判定)
            ai_insight = None
            if gemini_token and signals:
                from gemini_utils import get_gemini_insight
                logging.info(f"正在呼叫 Gemini 分析 {code}...")
                ai_insight = get_gemini_insight(gemini_token, code, stock_name, latest_price, signals, eval_dict=eval_result)
            
            report_data.append({
                "code": code,
                "name": stock_name,
                "price": latest_price,
                "eval": eval_result,
                "signals": signals,
                "ai_insight": ai_insight
            })
            
        except Exception as e:
            logging.error(f"分析 {code} 時發生錯誤: {e}", exc_info=True)
            
        time.sleep(1.0)
        
    # ── 全市場大盤進場環境評估 ──────────────────────────────
    regime_evaluator = MarketRegimeEvaluator(report_data)
    market_stats = regime_evaluator.evaluate_market()
    
    # 呼叫 Gemini 產出大盤宏觀 AI 洞察
    if gemini_token:
        try:
            from gemini_utils import get_market_macro_insight
            logging.info("正在呼叫 Gemini 進行大盤宏觀進場環境分析...")
            macro_ai = get_market_macro_insight(gemini_token, market_stats)
            market_stats["macro_ai_insight"] = macro_ai
        except Exception as e:
            logging.warning(f"大盤宏觀 AI 分析略過: {e}")
            
    report_md = generate_markdown_report(report_data, market_stats)
    
    # 附加虛擬投資組合狀態 (Markdown)
    portfolio_text = "\n### 💼 虛擬投資組合狀態\n"
    if not open_positions:
        portfolio_text += "目前無持倉。\n"
    else:
        portfolio_text += "| 股票代號 | 買進價格 | 目前價格 | 持有股數 | 未實現損益 |\n| -------- | -------- | -------- | -------- | ---------- |\n"
        for p_code, p_data in open_positions.items():
            p_price = p_data["buy_price"]
            p_shares = p_data.get("buy_shares", 0)
            curr_price = next((item['price'] for item in report_data if item['code'] == p_code), p_price)
            if curr_price != "N/A":
                roi = (curr_price - p_price) / p_price * 100
                profit_amt = (curr_price - p_price) * p_shares
                portfolio_text += f"| {p_code} | {p_price:.2f} | {curr_price:.2f} | {p_shares} | {roi:+.2f}% ({profit_amt:+.0f}元) |\n"
            else:
                portfolio_text += f"| {p_code} | {p_price:.2f} | N/A | {p_shares} | N/A |\n"
    report_md = report_md.replace("---\n*💡", portfolio_text + "\n---\n*💡")
    
    # 儲存報告
    report_filename = f"report_{datetime.now().strftime('%Y%m%d')}.md"
    report_filepath = os.path.join(os.path.dirname(__file__), report_filename)
    
    with open(report_filepath, 'w', encoding='utf-8') as f:
        f.write(report_md)
        
    logging.info(f"🎉 報告生成完畢: {report_filepath}")
    
    print("\n" + "="*60)
    print(report_md)
    print("="*60 + "\n")

    # Telegram 推播
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("telegram_chat_id")
    if bot_token and chat_id:
        logging.info("準備發送 Telegram 推播...")
        report_tg = generate_telegram_report(report_data, market_stats)
        
        # 附加虛擬投資組合狀態 (Telegram HTML)
        portfolio_tg = "\n💼 <b>虛擬投資組合狀態</b>\n"
        if not open_positions:
            portfolio_tg += "目前無持倉。\n"
        else:
            for p_code, p_data in open_positions.items():
                p_price = p_data["buy_price"]
                p_shares = p_data.get("buy_shares", 0)
                curr_price = next((item['price'] for item in report_data if item['code'] == p_code), p_price)
                if curr_price != "N/A":
                    roi = (curr_price - p_price) / p_price * 100
                    profit_amt = (curr_price - p_price) * p_shares
                    portfolio_tg += f"• {p_code}: {p_price:.2f} ➡️ {curr_price:.2f} ({p_shares}股, <b>{roi:+.2f}%</b>, {profit_amt:+.0f}元)\n"
                else:
                    portfolio_tg += f"• {p_code}: {p_price:.2f} ➡️ N/A\n"
        report_tg = report_tg.replace("💡 <i>", portfolio_tg + "\n💡 <i>")
        
        send_telegram_message(bot_token, chat_id, report_tg)
    elif bot_token and not chat_id:
        logging.warning("⚠️ 有偵測到 TELEGRAM_BOT_TOKEN，但 config.json 中沒有 telegram_chat_id。")

if __name__ == "__main__":
    main()

