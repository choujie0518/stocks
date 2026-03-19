import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# --- 設定 ---
LINE_TOKEN = os.getenv("+2CR+GgiuG6KeEQunMSDhuOhRgh4YUvY4o6p06aTOGWXUlAel96y1kCKZDe40uHzJJleppcbd00EOzV7HuXKU6jhzSJoHKk117MZc/HC7TOrakfyuNcukMtI9mzhfkxw6W+tn/HdaAl0iBWg4tFYRwdB04t89/1O/w1cDnyilFU=")
USER_ID = os.getenv("U65997d63aa5d6021411de4c8e1e9e9c0")

def get_real_data():
    # 偽裝成瀏覽器，避免被擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = "https://histock.tw/stock/public.aspx" # 處置股頁面
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        # 用 BeautifulSoup 解析表格
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table') # 抓第一個表格
        
        if not table:
            return "⚠️ 暫時抓不到表格資料，可能是網站改版。"
        
        rows = table.find_all('tr')
        report = "🚫 【今日最新處置股】\n--------------------\n"
        
        # 抓取前 10 筆資料
        for row in rows[1:11]: # 跳過標題列
            cols = row.find_all('td')
            if len(cols) >= 2:
                code_name = cols[0].get_text(strip=True) # 代號名稱
                date_range = cols[1].get_text(strip=True) # 處置期間
                report += f"• {code_name}\n  ⏳ {date_range}\n"
        
        return report
    except Exception as e:
        return f"❌ 抓取失敗: {str(e)}"

def send_line(msg):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

def main():
    if not LINE_TOKEN or not USER_ID:
        print("環境變數錯誤")
        return

    content = get_real_data()
    now_str = datetime.now().strftime('%m/%d %H:%M')
    final_msg = f"💡 台股自動報報 ({now_str})\n\n{content}"
    
    send_line(final_msg)
    print("發送成功！")

if __name__ == "__main__":
    main()
