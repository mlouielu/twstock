import requests
import logging
import time

def get_gemini_insight(token, stock_code, stock_name, price, signals, eval_dict=None):
    """
    透過 Gemini API 進行個股綜合分析 (Zero Dependency, pure requests)
    結合搜尋工具查詢近 3 天時事，並明確回答是否可以進場。
    """
    if not token:
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={token}"
    
    signals_text = "\n    - ".join(signals)
    
    eval_text = ""
    if eval_dict:
        verdict = eval_dict.get("verdict", "N/A")
        score = eval_dict.get("score", 0)
        rrr = eval_dict.get("rrr", 1.0)
        stop_loss = eval_dict.get("stop_loss", 0.0)
        eval_text = (f"\n    【量化進場系統初步評估】"
                     f"\n    - 評級: {verdict} (得分: {score}/100)"
                     f"\n    - 風報比: {rrr:.2f}"
                     f"\n    - 建議防守停損價: {stop_loss:.2f}")

    prompt = f"""
    你現在是一位專業的台股量化與基本面操盤手。
    請使用搜尋工具，查詢這檔股票「{stock_name}」近三天的最新重大新聞、法人動向或法說會消息。
    結合以下量化評估與技術訊號，請以極精簡、果斷、專業的文字回答以下三點（總字數嚴格限制在 80 個字以內）：
    1.【進場判定】：明確寫出「可進場」、「暫緩進場 (觀望)」、「逢低佈局」或「減碼避開」。
    2.【時事洞察】：新聞或基本面是否有催化劑或地雷？若與技術面矛盾請直接戳破。
    3.【實戰防守】：指引關鍵防守價位或明日操作節奏。

    【標的資訊】
    股票：{stock_code} {stock_name}
    今日收盤價：{price}{eval_text}

    【技術面與情境訊號】
    - {signals_text}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}]
    }
    
    max_retries = 3
    base_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=45)
            
            if response.status_code == 429:
                delay = base_delay * (2 ** (attempt - 1))
                logging.warning(f"Gemini API 觸發 Rate Limit (429)，等待 {delay} 秒後重試...")
                time.sleep(delay)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if "candidates" in data and len(data["candidates"]) > 0:
                insight = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                insight = insight.replace('**', '').replace('*', '')
                return insight
            else:
                logging.error(f"Gemini API 錯誤或無回傳內容: {data}")
                return "AI 分析暫時無法使用"
                
        except requests.exceptions.Timeout:
            logging.error(f"呼叫 Gemini API 發生超時錯誤 (第 {attempt}/{max_retries} 次)")
            if attempt < max_retries:
                time.sleep(base_delay * (2 ** (attempt - 1)))
            else:
                return "AI 分析連線失敗 (超時)"
        except requests.exceptions.RequestException as e:
            logging.error(f"呼叫 Gemini API 發生網路/請求錯誤: {e} (第 {attempt}/{max_retries} 次)")
            if attempt < max_retries:
                time.sleep(base_delay * (2 ** (attempt - 1)))
            else:
                return "AI 分析連線失敗"
                
    return "AI 分析連線失敗"

def get_market_macro_insight(token, market_stats):
    """
    透過 Gemini API 查詢台股與美股近期總經時事，產出 2 句話以內的大盤宏觀進場指引
    """
    if not token or not market_stats:
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={token}"
    
    market_verdict = market_stats.get("market_verdict", "觀望")
    bull_ratio = market_stats.get("bull_ratio_ma20", 50.0)
    suggested_exposure = market_stats.get("suggested_exposure", "50%")
    
    prompt = f"""
    你現在是一位台股資深首席策略分析師。
    請使用搜尋工具查詢近 24 小時美股走勢、外資期現貨籌碼、台積電或台股重要總經新聞。
    參考以下台股市場內部多空廣度統計：
    - 大盤量化環境判定：{market_verdict}
    - 站上月線標的比例：{bull_ratio:.1f}%
    - 建議資金配置水位：{suggested_exposure}

    請用兩句話（嚴格在 70 字以內），給出投資人明日「台股是否適合進場」的宏觀操作方針與核心風控叮嚀。
    語氣果斷專業，明確指出該偏多積極進場還是控制部位觀望。
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"googleSearch": {}}]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=40)
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                insight = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return insight.replace('**', '').replace('*', '')
    except Exception as e:
        logging.error(f"獲取大盤宏觀 AI 洞察失敗: {e}")
        
    return None

