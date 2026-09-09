import sqlite3
import os
import time
import logging
from datetime import datetime, timedelta
import twstock
from twstock.stock import DATATUPLE as Data

DB_PATH = os.path.join(os.path.dirname(__file__), 'twstock_cache.db')

def _connect():
    """統一建立資料庫連線，啟用 WAL 模式與 10 秒等鎖逾時"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_db():
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_prices (
            code TEXT,
            date TIMESTAMP,
            capacity INTEGER,
            turnover INTEGER,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            change REAL,
            transaction_count INTEGER,
            PRIMARY KEY (code, date)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            buy_date TIMESTAMP,
            buy_price REAL,
            sell_date TIMESTAMP,
            sell_price REAL,
            status TEXT,
            profit_pct REAL
        )
    ''')
    try:
        cursor.execute("ALTER TABLE portfolio ADD COLUMN buy_shares INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def sync_portfolio_from_json():
    """
    從 portfolio.json 同步使用者的真實投資部位至 SQLite portfolio 表
    """
    json_path = os.path.join(os.path.dirname(__file__), 'portfolio.json')
    if not os.path.exists(json_path):
        return
    try:
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        init_db()
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio WHERE status = 'OPEN'")
        now_dt = datetime.now()
        for item in items:
            code = item["code"]
            buy_price = float(item.get("buy_price", 0.0))
            buy_shares = int(item.get("buy_shares", 0))
            cursor.execute('''
                INSERT INTO portfolio (code, buy_date, buy_price, buy_shares, status)
                VALUES (?, ?, ?, ?, 'OPEN')
            ''', (code, now_dt, buy_price, buy_shares))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"同步 portfolio.json 失敗: {e}")

def get_open_positions():
    init_db()
    # 優先從使用者設定的 portfolio.json 同步真實庫存
    sync_portfolio_from_json()
    conn = sqlite3.connect(DB_PATH, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    cursor.execute("SELECT code, buy_date, buy_price, buy_shares FROM portfolio WHERE status = 'OPEN'")
    rows = cursor.fetchall()
    conn.close()
    result = {}
    for row in rows:
        dt = row[1]
        if isinstance(dt, str):
            dt = datetime.strptime(dt.split('.')[0], "%Y-%m-%d %H:%M:%S")
        result[row[0]] = {"buy_date": dt, "buy_price": row[2], "buy_shares": row[3]}
    return result

def record_buy(code, buy_date, buy_price, buy_shares):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO portfolio (code, buy_date, buy_price, buy_shares, status)
        VALUES (?, ?, ?, ?, 'OPEN')
    ''', (code, buy_date, buy_price, buy_shares))
    conn.commit()
    conn.close()

def record_sell(code, sell_date, sell_price):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, buy_price FROM portfolio WHERE code = ? AND status = 'OPEN' ORDER BY id DESC LIMIT 1", (code,))
    row = cursor.fetchone()
    if row:
        record_id, buy_price = row
        profit_pct = (sell_price - buy_price) / buy_price * 100
        cursor.execute('''
            UPDATE portfolio 
            SET sell_date = ?, sell_price = ?, status = 'CLOSED', profit_pct = ?
            WHERE id = ?
        ''', (sell_date, sell_price, profit_pct, record_id))
        conn.commit()
    conn.close()

def save_to_db(code, data_list):
    if not data_list:
        return
    conn = _connect()
    cursor = conn.cursor()
    
    records = []
    for d in data_list:
        records.append((
            code,
            d.date,
            d.capacity,
            d.turnover,
            d.open,
            d.high,
            d.low,
            d.close,
            d.change,
            d.transaction
        ))
        
    # 使用 INSERT OR IGNORE 確保相同日期的資料不會重複
    cursor.executemany('''
        INSERT OR IGNORE INTO daily_prices 
        (code, date, capacity, turnover, open, high, low, close, change, transaction_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', records)
    
    conn.commit()
    conn.close()

def get_from_db(code, start_date):
    conn = sqlite3.connect(DB_PATH, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, capacity, turnover, open, high, low, close, change, transaction_count
        FROM daily_prices
        WHERE code = ? AND date >= ?
        ORDER BY date ASC
    ''', (code, start_date))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        dt = row[0]
        # 處理 SQLite TIMESTAMP 可能回傳字串的問題
        if isinstance(dt, str):
            dt = datetime.strptime(dt.split('.')[0], "%Y-%m-%d %H:%M:%S")
            
        result.append(Data(
            date=dt,
            capacity=row[1],
            turnover=row[2],
            open=row[3],
            high=row[4],
            low=row[5],
            close=row[6],
            change=row[7],
            transaction=row[8],
            note=""
        ))
    return result

def get_cached_stock(code, start_year, start_month):
    """
    自動利用 SQLite 快取補齊資料，並回傳配置好的 twstock.Stock 物件
    """
    init_db()
    
    start_date = datetime(start_year, start_month, 1)
    
    # 建立空的 Stock 物件
    stock = twstock.Stock(code, initial_fetch=False)
    
    today = datetime.now()
    
    # 檢查哪些月份在資料庫中是缺少的
    months_to_fetch = []
    conn = _connect()
    cursor = conn.cursor()
    
    for y, m in stock._month_year_iter(start_month, start_year, today.month, today.year):
        is_current_month = (y == today.year and m == today.month)
        
        # 檢查該月份在資料庫中是否有任何一天的資料
        cursor.execute('''
            SELECT 1 FROM daily_prices 
            WHERE code = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            LIMIT 1
        ''', (code, str(y), f"{m:02d}"))
        
        if is_current_month or not cursor.fetchone():
            months_to_fetch.append((y, m))
            
    conn.close()
        
    new_data = []
    for y, m in months_to_fetch:
        logging.info(f"[資料庫] 從 TWSE 同步 {code} ({y}/{m:02d}) 的資料...")
        try:
            fetch_result = stock.fetcher.fetch(y, m, stock.sid)
            if fetch_result and 'data' in fetch_result:
                new_data.extend(fetch_result['data'])
            # 嚴格遵守 API 速率限制
            time.sleep(3.0)
        except Exception as e:
            logging.error(f"抓取 {y}/{m} 失敗: {e}")
            
    if new_data:
        save_to_db(code, new_data)
        
    # 從資料庫撈出完整區間資料並寫入物件
    final_data = get_from_db(code, start_date)
    stock.data = final_data
    
    return stock

def get_offline_stock(code, days=120):
    """
    純粹從 SQLite 本地資料庫讀取資料，零網路請求，適用於即時 Telegram 指令
    """
    init_db()
    start_date = datetime.now() - timedelta(days=days)
    final_data = get_from_db(code, start_date)
    stock = twstock.Stock(code, initial_fetch=False)
    stock.data = final_data
    return stock

