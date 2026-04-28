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
    
    stock = twstock.Stock(code, initial_fetch=False)
    today = datetime.now()
    
    # 往回抓歷史資料
    stock.raw_data = []
    stock.data = []
    
    start_month = today.month - months
    start_year = today.year
    while start_month <= 0:
        start_month += 12
        start_year -= 1
        
    for y, m in stock._month_year_iter(start_month, start_year, today.month, today.year):
        logging.info(f"抓取 {y}/{m:02d}...")
        stock.raw_data.append(stock.fetcher.fetch(y, m, stock.sid))
        stock.data.extend(stock.raw_data[-1]["data"])
        time.sleep(3.0) # 嚴格遵守速率限制防 Ban
        
    total_days = len(stock.price)
    logging.info(f"資料抓取完成，總交易日數: {total_days}")
    
    if total_days < 60:
        logging.error("資料不足以回測。")
        return
        
    holding = False
    buy_price = 0
    buy_date = None
    trades = []
    
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
            # 判斷是否賣出 (技術指標賣出 或 強制停損 10%)
            stop_loss = (current_price - buy_price) / buy_price <= -0.10
            
            if sell_signals or stop_loss:
                reason = "停損出場" if stop_loss else "技術面賣出"
                profit_pct = (current_price - buy_price) / buy_price * 100
                trades.append({
                    "buy_date": buy_date,
                    "buy_price": buy_price,
                    "sell_date": current_date,
                    "sell_price": current_price,
                    "profit_pct": profit_pct,
                    "reason": reason
                })
                holding = False
                logging.info(f"[{current_date}] 賣出 {code} @ {current_price} (獲利: {profit_pct:.2f}%) - {reason}")
                
        else:
            # 判斷是否買進 (有買進訊號 且 財務分析師沒有要求觀望)
            if buy_signals and not wait_signals:
                holding = True
                buy_price = current_price
                buy_date = current_date
                logging.info(f"[{current_date}] 買進 {code} @ {current_price}")
                
    # 迴圈結束，如果手上還有持股，強制平倉結算
    if holding:
        current_date = stock.date[-1].strftime("%Y-%m-%d")
        current_price = stock.price[-1]
        profit_pct = (current_price - buy_price) / buy_price * 100
        trades.append({
            "buy_date": buy_date,
            "buy_price": buy_price,
            "sell_date": current_date,
            "sell_price": current_price,
            "profit_pct": profit_pct,
            "reason": "回測結束強制平倉"
        })
        logging.info(f"[{current_date}] 賣出 {code} @ {current_price} (獲利: {profit_pct:.2f}%) - 回測結束強制平倉")

    # 輸出統計結果
    wins = [t for t in trades if t["profit_pct"] > 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    total_profit = sum(t["profit_pct"] for t in trades)
    
    print("\n" + "="*50)
    print(f"📊 {code} 歷史回測報告 ({months} 個月)")
    print(f"策略：四大買賣點 + MACD + RSI + KD + 財務風報比過濾 + 10%停損")
    print("="*50)
    print(f"總交易次數: {len(trades)}")
    if trades:
        print(f"勝率: {win_rate:.1f}%")
        print(f"累計報酬率: {total_profit:.2f}% (單利計算)")
        print("="*50)
        for t in trades:
            status = "✅ 獲利" if t['profit_pct'] > 0 else "❌ 虧損"
            print(f"{status} | 買: {t['buy_date']} ({t['buy_price']}) -> 賣: {t['sell_date']} ({t['sell_price']}) | 報酬: {t['profit_pct']:.2f}% | {t['reason']}")
    else:
        print("這段期間內沒有觸發任何符合嚴格條件的交易。")

if __name__ == "__main__":
    # 預設回測 0050 過去 12 個月
    import sys
    target_code = sys.argv[1] if len(sys.argv) > 1 else "0050"
    target_months = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    run_backtest(target_code, target_months)
