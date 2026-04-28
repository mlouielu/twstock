#!/bin/bash

# 取得腳本所在的絕對路徑
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TWSTOCK_DIR="$(dirname "$SCRIPT_DIR")"

# 強制載入使用者的環境變數 (包含 GEMINI_API_TOKEN 與 TELEGRAM_BOT_TOKEN)
# cron 預設不會載入 .bashrc，所以我們手動 source 它
source ~/.bashrc

# 切換到專案根目錄
cd "$TWSTOCK_DIR"

# 建立 log 檔
LOG_FILE="$SCRIPT_DIR/cron.log"

echo "--------------------------------------------------" >> "$LOG_FILE"
echo "開始執行每日台股代理人: $(date)" >> "$LOG_FILE"

# 執行 python 腳本
# 注意: 這裡我們假設 python 在你的環境中能直接被調用
python agent/main.py >> "$LOG_FILE" 2>&1

echo "執行完畢: $(date)" >> "$LOG_FILE"
