import requests
import logging

def get_gemini_insight(token, stock_code, stock_name, price, signals):
    """
    透過 Gemini API 進行個股綜合分析 (Zero Dependency, pure requests)
    """
    if not token:
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={token}"
    
    # 組合給 Gemini 的 Prompt
    signals_text = "\n    - ".join(signals)
    prompt = f"""
    你現在是一位專業的台股量化與基本面分析師。
    請使用搜尋工具，查詢這檔股票「{stock_name}」近三天的最新重大新聞或法說會消息。
    結合以下代理人給出的技術面量化訊號，以及你搜尋到的最新時事，用「兩句話（嚴格限制在 50 個字以內）」給出明天開盤的操作建議或風險提示。
    語氣要果斷、冷靜，如果新聞面與技術面有矛盾請直接點出。

    【標的資訊】
    股票：{stock_code} {stock_name}
    今日收盤價：{price}

    【代理人觸發的技術面訊號】
    - {signals_text}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}]
    }
    
    import time
    max_retries = 3
    base_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            # 增加 timeout 到 45 秒，並加入指數退避重試機制
            response = requests.post(url, json=payload, timeout=45)
            
            # 處理 429 Rate Limit
            if response.status_code == 429:
                delay = base_delay * (2 ** (attempt - 1))
                logging.warning(f"Gemini API 觸發 Rate Limit (429)，等待 {delay} 秒後重試...")
                time.sleep(delay)
                continue
                
            response.raise_for_status()
            
            data = response.json()
            
            if "candidates" in data and len(data["candidates"]) > 0:
                insight = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                # 移除 Markdown 標籤以配合 Telegram 顯示
                insight = insight.replace('**', '').replace('*', '')
                return insight
            else:
                logging.error(f"Gemini API 錯誤或無回傳內容: {data}")
                return "AI 分析暫時無法使用"
                
        except requests.exceptions.Timeout:
            logging.error(f"呼叫 Gemini API 發生超時錯誤 (第 {attempt}/{max_retries} 次)")
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                time.sleep(delay)
            else:
                return "AI 分析連線失敗 (超時)"
        except requests.exceptions.RequestException as e:
            logging.error(f"呼叫 Gemini API 發生網路/請求錯誤: {e} (第 {attempt}/{max_retries} 次)")
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                time.sleep(delay)
            else:
                return "AI 分析連線失敗"
                
    return "AI 分析連線失敗"
