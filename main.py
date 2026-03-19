import os
import requests
import pandas as pd
from datetime import datetime

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSwV0nkehAeEtnuYWL2wkJjWNeKcdVgOpZGy4Bse_ONLYPihJjDgCINTbJpaeMIAxo8CtbKx0tT_1Bs/pub?output=csv" # 務必確認這是發布後的連結

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload, timeout=15)

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("❌ 環境變數缺失")
        return

    try:
        # 讀取 CSV
        df = pd.read_csv(SHEET_CSV_URL, header=None)
        
        if df.empty:
            content = "⚠️ 讀取成功，但 CSV 內容是空的！請檢查試算表。"
        else:
            content = "📈 【即時報表內容】\n"
            for _, row in df.iterrows():
                content += f"• {row[0]} {row[1]} | {row[2]}\n"
    except Exception as e:
        content = f"❌ CSV 讀取失敗，請檢查網址或發布狀態。\n錯誤原因: {str(e)}"

    now_str = datetime.now().strftime('%m/%d %H:%M')
    send_line_push(f"💡 測試推播 ({now_str})\n\n{content}")
    print("發送程序已完成")

if __name__ == "__main__":
    main()
