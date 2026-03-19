import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

LINE_TOKEN = os.getenv("+2CR+GgiuG6KeEQunMSDhuOhRgh4YUvY4o6p06aTOGWXUlAel96y1kCKZDe40uHzJJleppcbd00EOzV7HuXKU6jhzSJoHKk117MZc/HC7TOrakfyuNcukMtI9mzhfkxw6W+tn/HdaAl0iBWg4tFYRwdB04t89/1O/w1cDnyilFU=")
USER_ID = os.getenv("U65997d63aa5d6021411de4c8e1e9e9c0")

def get_real_data():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    url = "https://histock.tw/stock/public.aspx"
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if not table: return "⚠️ 目前網站數據結構有變，請檢查來源。"
        rows = table.find_all('tr')
        report = "🚫 【台股最新處置股】\n"
        for row in rows[1:11]: # 取前 10 筆
            cols = row.find_all('td')
            if len(cols) >= 2:
                report += f"• {cols[0].get_text(strip=True)}\n  ⏳ {cols[1].get_text(strip=True)}\n"
        return report
    except Exception as e:
        return f"❌ 數據抓取失敗: {str(e)}"

def send_line(msg):
    # 這裡加入偵錯檢查
    if not LINE_TOKEN or not USER_ID:
        print(f"❌ 錯誤：找不到環境變數！TOKEN長度: {len(str(LINE_TOKEN))}, ID長度: {len(str(USER_ID))}")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    
    response = requests.post(url, headers=headers, json=payload)
    # 把 LINE 的回覆印出來
    print(f"📡 LINE 伺服器回覆: {response.status_code} - {response.text}")

if __name__ == "__main__":
    content = get_real_data()
    now = datetime.now().strftime('%m/%d %H:%M')
    send_line(f"💡 自動報報 ({now})\n\n{content}")
