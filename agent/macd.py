def calculate_ema(prices, days):
    if len(prices) < days:
        return [None] * len(prices)
    
    multiplier = 2 / (days + 1)
    
    # 前 days 天的簡單移動平均作為第一個 EMA
    sma = sum(prices[:days]) / days
    ema_list = [None] * (days - 1)
    ema_list.append(sma)
    
    last_ema = sma
    for price in prices[days:]:
        current_ema = (price - last_ema) * multiplier + last_ema
        ema_list.append(current_ema)
        last_ema = current_ema
        
    return ema_list

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    計算 MACD 指標
    回傳字典: {'dif': [], 'dea': [], 'osc': []}
    """
    if len(prices) < slow + signal:
        return None
        
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    dif = []
    for f, s in zip(ema_fast, ema_slow):
        if f is not None and s is not None:
            dif.append(f - s)
        else:
            dif.append(None)
            
    # 計算 DEA (DIF 的 signal 日 EMA)
    valid_dif = [x for x in dif if x is not None]
    if len(valid_dif) < signal:
        return None
        
    dea_valid = calculate_ema(valid_dif, signal)
    
    # 將 DEA 補上 None 以對齊原始長度
    dea = [None] * (len(dif) - len(dea_valid)) + dea_valid
    
    macd_osc = []
    for d, de in zip(dif, dea):
        if d is not None and de is not None:
            macd_osc.append((d - de) * 2) # 有些軟體會乘2，為了視覺化明顯
        else:
            macd_osc.append(None)
            
    return {
        "dif": dif,
        "dea": dea,
        "osc": macd_osc
    }

def get_macd_signal(prices):
    """
    判斷 MACD 的買賣訊號
    """
    macd_data = calculate_macd(prices)
    if not macd_data:
        return None
        
    osc = macd_data["osc"]
    if len(osc) < 2 or osc[-1] is None or osc[-2] is None:
        return None
        
    current_osc = osc[-1]
    prev_osc = osc[-2]
    
    # 柱狀圖由負轉正 -> 黃金交叉
    if prev_osc <= 0 and current_osc > 0:
        return "🟢 買進 (Buy) MACD 黃金交叉 (柱狀圖由負轉正)"
    # 柱狀圖由正轉負 -> 死亡交叉
    elif prev_osc >= 0 and current_osc < 0:
        return "🔴 賣出 (Sell) MACD 死亡交叉 (柱狀圖由正轉負)"
        
    return None
