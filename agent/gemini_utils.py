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
    
    try:
        # 增加 timeout 到 30 秒，避免 Gemini API 回應較慢時發生 Read timed out
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        
        if "candidates" in data and len(data["candidates"]) > 0:
            insight = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            # 移除 Markdown 標籤以配合 Telegram 顯示
            insight = insight.replace('**', '').replace('*', '')
            return insight
        else:
            logging.error(f"Gemini API 錯誤或無回傳內容: {data}")
            return "AI 分析暫時無法使用"
            
    except Exception as e:
        logging.error(f"呼叫 Gemini API 發生錯誤: {e}")
        return "AI 分析連線失敗"
