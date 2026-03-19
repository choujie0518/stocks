import os
import requests
import json
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_disposition():
    """直接呼叫證交所後台 JSON 接口，避開網頁阻擋"""
    url = "https://www.twse.com.tw/zh/announcement/punish.html" # 雖然是html，我們模擬合法來源
    api_url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json" # 真正的API
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        data = res.json()
        if 'data' not in data or not data['data']:
            return "🚫 【今日處置股】\n  (暫無資料或證交所尚未公布)\n"
        
        report = "🚫 【今日處置股名單】\n"
        # 證交所 API 資料結構: [日期, 證券代號, 證券名稱, 處置內容...]
        for item in data['data'][:12]: # 取前 12 筆
            date_range = item[0] # 這就是起訖日
            stock = f"{item[1]} {item[2]}" # 代號 + 名稱
            report += f"• {stock}\n  ⏳ {date_range}\n"
        return report + "\n"
    except:
        return "🚫 【今日處置股】\n  (資料源連線異常)\n"

def get_conferences():
    """改用法說會專用穩定來源"""
    url = "https://mops.twse.com.tw/mops/web/t100sb02_1" # 公開資訊觀測站
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # 這裡改用一個更通用的財經接口
        res = requests.get("https://histock.tw/stock/mktcalendar.aspx", headers=headers, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        
        today = datetime.now().strftime('%m/%d')
        report = "🎙️ 【今日法說會資訊】\n"
        
        # 尋找頁面中所有的 a tag，只要包含代號的文字
        found = False
        items = soup.select('.cal-item a')
        for item in items:
            text = item.get_text(strip=True)
            if "(" in text and ")" in text: # 通常代號會長這樣 (2330)
                report += f"• {text}\n"
                found = True
        
        return report if found else "🎙️ 【今日法說會】\n  (今日暫無排定或資料更新中)\n"
    except:
        return "🎙️ 【今日法說會】\n  (抓取異常)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    content = get_disposition() + get_conferences()
    date_head = datetime.now().strftime('%Y-%m-%d')
    send_line(f"🚀 【台股自動化偵測】 {date_head}\n\n{content}")
