def calculate_rsi(prices, period=14):
    """計算 RSI 相對強弱指標 (14日)"""
    if len(prices) < period + 1:
        return None
        
    gains = []
    losses = []
    
    # 計算每日漲跌幅
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        gains.append(change if change > 0 else 0)
        losses.append(abs(change) if change < 0 else 0)
        
    # 第一筆 RSI 使用簡單平均
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # 後續使用平滑移動平均 (Wilder's Smoothing)
    for i in range(period, len(prices)-1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
    if avg_loss == 0:
        return 100.0
        
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def calculate_kd(highs, lows, closes, period=9):
    """計算 KD 隨機指標 (9, 3, 3)"""
    if len(closes) < period:
        return None, None, None, None
        
    k_values = [50.0]
    d_values = [50.0]
    
    for i in range(period - 1, len(closes)):
        window_high = max(highs[i - period + 1 : i + 1])
        window_low = min(lows[i - period + 1 : i + 1])
        current_close = closes[i]
        
        if window_high == window_low:
            rsv = 50.0
        else:
            rsv = (current_close - window_low) / (window_high - window_low) * 100.0
            
        prev_k = k_values[-1]
        prev_d = d_values[-1]
        
        current_k = (2/3) * prev_k + (1/3) * rsv
        current_d = (2/3) * prev_d + (1/3) * current_k
        
        k_values.append(current_k)
        d_values.append(current_d)
        
    # 回傳當天與前一天的 K, D 以便判斷黃金交叉/死亡交叉
    return k_values[-1], d_values[-1], k_values[-2], d_values[-2]

def get_rsi_kd_signals(prices, highs, lows):
    signals = []
    
    # RSI 訊號判斷
    rsi = calculate_rsi(prices)
    if rsi is not None:
        if rsi < 30:
            signals.append(f"[🟢 買進 (Buy)] RSI 超賣區 ({rsi:.1f})")
        elif rsi > 70:
            signals.append(f"[🔴 賣出 (Sell)] RSI 超買區 ({rsi:.1f})")
            
    # KD 訊號判斷
    k, d, prev_k, prev_d = calculate_kd(highs, lows, prices)
    if k is not None and d is not None:
        # 黃金交叉: K從下方穿越D，且在低檔(通常小於20或30)
        if prev_k < prev_d and k > d and k < 30:
            signals.append(f"[🟢 買進 (Buy)] KD 於低檔 ({k:.1f}) 黃金交叉")
        # 死亡交叉: K從上方穿越D，且在高檔(通常大於70或80)
        elif prev_k > prev_d and k < d and k > 70:
            signals.append(f"[🔴 賣出 (Sell)] KD 於高檔 ({k:.1f}) 死亡交叉")
            
    return signals
