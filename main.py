import os
import requests
import pandas as pd
from datetime import datetime

# 讀取金鑰
LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSwV0nkehAeEtnuYWL2wkJjWNeKcdVgOpZGy4Bse_ONLYPihJjDgCINTbJpaeMIAxo8CtbKx0tT_1Bs/pub?output=csv" # 務必確認這是發布後的連結

def debug_line(msg):
    """這是一個會印出錯誤原因的發送函式"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"--- LINE API 狀態碼: {response.status_code} ---")
    print(f"--- LINE API 回傳內容: {response.text} ---")
    return response.status_code

def main():
    print(f"--- 開始執行任務 {datetime.now()} ---")
    
    if not LINE_TOKEN or not USER_ID:
        print("❌ 錯誤：找不到環境變數！請檢查 GitHub Secrets 設定。")
        return

    try:
        df = pd.read_csv(SHEET_URL, header=None)
        if df.empty:
            content = "⚠️ 試算表是空的"
        else:
            # 抓前五筆資料測試
            content = "📈 資料測試：\n" + df.head(5).to_string(index=False, header=False)
    except Exception as e:
        content = f"❌ CSV 讀取失敗: {e}"

    print(f"--- 準備發送內容 ---\n{content}")
    
    status = debug_line(f"💡 自動報測試\n{content}")
    
    if status == 200:
        print("✅ LINE 發送成功！請檢查手機。")
    else:
        print("❌ LINE 發送失敗，請看上方回傳內容。")

if __name__ == "__main__":
    main()
