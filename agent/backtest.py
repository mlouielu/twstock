import os
import time
import logging
from datetime import datetime

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import twstock
from main import StrategyEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MockStock(twstock.analytics.Analytics):
    """
    用來切片歷史資料，模擬過去某一天的股票狀態，
    餵給 StrategyEngine 進行回測計算。
    """
    def __init__(self, full_stock, end_idx):
        self.price = full_stock.price[:end_idx]
        self.high = full_stock.high[:end_idx]
        self.low = full_stock.low[:end_idx]
        self.date = full_stock.date[:end_idx]
        self.capacity = full_stock.capacity[:end_idx]
        self.turnover = full_stock.turnover[:end_idx]
        self.open = full_stock.open[:end_idx]
        self.close = full_stock.close[:end_idx]
        self.change = full_stock.change[:end_idx]
        self.transaction = full_stock.transaction[:end_idx]

def run_backtest(code, months=12):
    logging.info(f"開始回測 {code}，抓取過去 {months} 個月的歷史資料...")
    
    today = datetime.now()
    start_month = today.month - months
    start_year = today.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1
        
    # 改用帶有資料庫快取的模組
    from db_utils import get_cached_stock
    stock = get_cached_stock(code, start_year, start_month)
        
    total_days = len(stock.price)
    logging.info(f"資料抓取完成，總交易日數: {total_days}")
    
    if total_days < 60:
        logging.error("資料不足以回測。")
        return
        
    holding = False
    buy_price = 0
    buy_shares = 0
    buy_date = None
    trades = []
    highest_price_since_buy = 0
    initial_stop_loss_price = 0
    
    # 部位控管設定
    total_capital = 1000000
    risk_pct = 0.01
    
    # 從第 60 天開始回測 (讓 MACD 和長均線有足夠數據)
    for i in range(60, total_days + 1):
        mock_stock = MockStock(stock, i)
        current_date = mock_stock.date[-1].strftime("%Y-%m-%d")
        current_price = mock_stock.price[-1]
        
        # 呼叫主程式的策略引擎
        engine = StrategyEngine(mock_stock)
        signals = engine.run_all()
        
        # 簡易的訊號解析 (實務上可以改成回傳 dict)
        buy_signals = [msg for msg in signals if "買進" in msg]
        sell_signals = [msg for msg in signals if "賣出" in msg]
        wait_signals = [msg for msg in signals if "建議觀望" in msg]
        
        if holding:
            if current_price > highest_price_since_buy:
                highest_price_since_buy = current_price
                
            # 判斷是否觸發初始停損 (買入價 - 1.5 * ATR)
            stop_loss_hit = current_price < initial_stop_loss_price
            
            # 判斷是否觸發移動停利 (獲利狀態下，跌破 10 日均線出場)
            ma10 = sum(mock_stock.price[-10:]) / 10
            trailing_stop_hit = current_price < ma10 and current_price > buy_price
            
            if stop_loss_hit or trailing_stop_hit or sell_signals:
                if stop_loss_hit:
                    reason = "ATR 初始停損出場"
                elif trailing_stop_hit:
                    reason = "跌破 10 日線移動停利"
                else:
                    reason = "技術面賣出"
                    
                profit_per_share = current_price - buy_price
                trade_profit = profit_per_share * buy_shares * 0.995 # 扣除 0.5% 交易摩擦成本
                profit_pct = (current_price - buy_price) / buy_price * 100 - 0.5
                total_capital += trade_profit
                
                trades.append({
                    "buy_date": buy_date,
                    "buy_price": buy_price,
                    "buy_shares": buy_shares,
                    "sell_date": current_date,
                    "sell_price": current_price,
                    "profit_pct": profit_pct,
                    "profit_amount": trade_profit,
                    "reason": reason
                })
                holding = False
                logging.info(f"[{current_date}] 賣出 {code} @ {current_price} (獲利金額: {trade_profit:.0f} 元, {profit_pct:.2f}%) - {reason}")
                
        else:
            ma20 = sum(mock_stock.price[-20:]) / 20
            
            # 判斷是否買進 (有多頭排列 MA20之上 + 買進訊號 + 無風險過濾)
            if buy_signals and current_price > ma20 and not wait_signals:
                holding = True
                buy_price = current_price
                buy_date = current_date
                highest_price_since_buy = current_price
                
                # 取得 ATR 以設定動態停損與部位控管
                from tech_indicators import calculate_atr
                atr = calculate_atr(mock_stock.price, mock_stock.high, mock_stock.low, period=14)
                if atr:
                    initial_stop_loss_price = buy_price - 1.5 * atr
                    sl_dist = 1.5 * atr
                else:
                    initial_stop_loss_price = buy_price * 0.90 # 降級保護
                    sl_dist = buy_price * 0.10
                    
                risk_amount = total_capital * risk_pct
                buy_shares = int(risk_amount / sl_dist) if sl_dist > 0 else 0
                max_shares = int(total_capital / current_price)
                buy_shares = min(buy_shares, max_shares)
                    
                logging.info(f"[{current_date}] 買進 {code} @ {current_price} (數量: {buy_shares} 股, 停損設於 {initial_stop_loss_price:.1f})")
                
    # 迴圈結束，如果手上還有持股，強制平倉結算
    if holding:
        current_date = stock.date[-1].strftime("%Y-%m-%d")
        current_price = stock.price[-1]
        profit_per_share = current_price - buy_price
        trade_profit = profit_per_share * buy_shares * 0.995 # 扣除 0.5% 交易摩擦成本
        profit_pct = (current_price - buy_price) / buy_price * 100 - 0.5
        total_capital += trade_profit
        
        trades.append({
            "buy_date": buy_date,
            "buy_price": buy_price,
            "buy_shares": buy_shares,
            "sell_date": current_date,
            "sell_price": current_price,
            "profit_pct": profit_pct,
            "profit_amount": trade_profit,
            "reason": "回測結束強制平倉"
        })
        logging.info(f"[{current_date}] 賣出 {code} @ {current_price} (獲利金額: {trade_profit:.0f} 元, {profit_pct:.2f}%) - 回測結束強制平倉")

    # 輸出統計結果
    wins = [t for t in trades if t["profit_pct"] > 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    total_profit = sum(t["profit_pct"] for t in trades)
    
    print("\n" + "="*50)
    print(f"📊 {code} 歷史回測報告 ({months} 個月)")
    print(f"策略：多維共振 (MA20濾網+四大買賣點/MACD/RSI/KD) + 財務風報比過濾 + ATR停損 + MA10移動停利")
    print(f"部位控管：起始資金 100 萬，單筆風險 {risk_pct*100}%")
    print("="*50)
    print(f"總交易次數: {len(trades)}")
    if trades:
        print(f"勝率: {win_rate:.1f}%")
        print(f"期末總資產: {total_capital:.0f} 元 (總獲利: {total_capital - 1000000:.0f} 元)")
        print("="*50)
        for t in trades:
            status = "✅ 獲利" if t['profit_pct'] > 0 else "❌ 虧損"
            print(f"{status} | 買: {t['buy_date']} ({t['buy_price']}x{t['buy_shares']}股) -> 賣: {t['sell_date']} ({t['sell_price']}) | 報酬: {t['profit_amount']:.0f} 元 ({t['profit_pct']:.2f}%) | {t['reason']}")
    else:
        print("這段期間內沒有觸發任何符合嚴格條件的交易。")

if __name__ == "__main__":
    # 預設回測 0050 過去 12 個月
    import sys
    target_code = sys.argv[1] if len(sys.argv) > 1 else "0050"
    target_months = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    run_backtest(target_code, target_months)
