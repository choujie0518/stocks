import os
import requests
import pandas as pd
from datetime import datetime

# --- 讀取 GitHub Secrets 的金鑰 ---
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

# --- 請把下面引號內的網址換成你剛才複製的 CSV 連結 ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSwV0nkehAeEtnuYWL2wkJjWNeKcdVgOpZGy4Bse_ONLYPihJjDgCINTbJpaeMIAxo8CtbKx0tT_1Bs/pub?output=csv"

def send_line_push(message):
    """發送推播至 LINE"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        requests.post(url, headers=headers, json=payload, timeout=15)
    except Exception as e:
        print(f"發送失敗: {e}")

def get_data_from_sheet():
    """讀取 Google 試算表資料"""
    try:
        # 讀取 CSV
        df = pd.read_csv(SHEET_CSV_URL, header=None)
        
        report = "📈 【台股自選監控報表】\n"
        report += "--------------------\n"
        
        # 逐行讀取股票資料 (假設 A:代碼, B:名稱, C:價格)
        for index, row in df.iterrows():
            code = str(row[0]).strip()
            # 如果 B 欄是手動打的中文，這裡就會抓到中文
            name = str(row[1]).strip() if len(row) > 1 else ""
            price = str(row[2]).strip() if len(row) > 2 else "--"
            
            # 格式化輸出
            report += f"• {code} {name} | 💰 {price}\n"
            
        return report
    except Exception as e:
        return f"❌ 讀取失敗: 請檢查 CSV 連結是否正確。\n錯誤訊息: {str(e)}"

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("錯誤：請檢查 GitHub Secrets 是否有設定 LINE_ACCESS_TOKEN 和 USER_ID")
        return
    
    # 抓取資料並組合訊息
    stock_content = get_data_from_sheet()
    now_str = datetime.now().strftime('%m/%d %H:%M')
    final_msg = f"💡 早安！今日台股快報 ({now_str})\n\n{stock_content}"
    
    # 執行推播
    send_line_push(final_msg)
    print("任務執行成功！")

if __name__ == "__main__":
    main()
