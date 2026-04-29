import os
import requests
import logging

def get_telegram_chat_id(token):
    """
    透過 getUpdates API 嘗試獲取最近對話的 Chat ID。
    使用者必須先在 Telegram 上傳送任何訊息給該 Bot，這個函數才能抓到。
    """
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("ok") and data.get("result"):
            # 取出最後一筆對話的 chat_id
            last_update = data["result"][-1]
            chat_id = last_update["message"]["chat"]["id"]
            chat_title = last_update["message"]["chat"].get("first_name", "Unknown")
            return chat_id, chat_title
        else:
            return None, None
    except Exception as e:
        logging.error(f"獲取 Telegram Chat ID 失敗: {e}")
        return None, None

def send_telegram_message(token, chat_id, text):
    """
    傳送 Markdown 格式的訊息到指定的 Telegram Chat ID。
    """
    if not token or not chat_id:
        logging.warning("未設定 Telegram Token 或 Chat ID，略過推播。")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Telegram 每個訊息限制 4096 字元，但某些編碼可能會超過，改用更保守的 3000 字元上限
    limit = 3000
    chunks = []
    current_chunk = ""
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 > limit:
            if current_chunk:
                chunks.append(current_chunk)
            # 防禦性程式設計：如果單行就超過 limit，強制切斷
            if len(line) > limit:
                for i in range(0, len(line), limit):
                    chunks.append(line[i:i+limit] + "\n")
                current_chunk = ""
            else:
                current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk)
        
    all_success = True
    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                logging.error(f"Telegram 推播失敗，狀態碼: {response.status_code}, 回應: {response.text}")
                all_success = False
        except Exception as e:
            logging.error(f"傳送 Telegram 訊息發生例外錯誤: {e}")
            all_success = False
            
    if all_success:
        logging.info("✅ Telegram 報表推播成功！")
        return True
    return False

if __name__ == "__main__":
    # 測試腳本：用來幫助使用者找出 Chat ID
    logging.basicConfig(level=logging.INFO)
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ 錯誤：找不到環境變數 TELEGRAM_BOT_TOKEN。")
        print("請確保您已經在 ~/.bashrc 中設定並 source。")
    else:
        print("🔍 正在嘗試獲取 Telegram Chat ID...")
        print("⚠️ 提示：請先打開 Telegram，找到您的 Bot 並隨便發送一句話 (例如 'hello')，否則這裡會抓不到。")
        
        chat_id, name = get_telegram_chat_id(bot_token)
        if chat_id:
            print(f"✅ 成功找到！")
            print(f"使用者/群組名稱: {name}")
            print(f"Chat ID: {chat_id}")
            print(f"👉 請將 {chat_id} 填入 config.json 的 'telegram_chat_id' 欄位中。")
        else:
            print("❌ 找不到對話紀錄。請確認您已經對 Bot 發送過訊息，然後再試一次。")
