import os
import requests
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_disposition_final():
    """抓取證交所 API 並進行去重與中文名稱解析"""
    api_url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        data = res.json()
        if 'data' not in data: return "🚫 【今日處置股】\n  (官方 API 暫無回應)\n"
        
        # 建立一個字典來去重，Key 用股票代號
        unique_stocks = {}
        for item in data['data']:
            date_range = item[0]  # 起訖日期
            code = item[1]        # 股票代號
            name = item[2]        # 股票名稱 (之前漏掉這個欄位)
            
            # 只保留每支股票最新的一筆資訊
            if code not in unique_stocks:
                unique_stocks[code] = f"• {code} {name}\n  ⏳ {date_range}"
        
        if not unique_stocks:
            return "🚫 【今日處置股】\n  (目前查無標的)\n"
            
        report = "🚫 【今日處置股名單】\n" + "\n".join(unique_stocks.values())
        return report + "\n\n"
    except:
        return "🚫 【今日處置股】\n  (連線異常)\n\n"

def get_conferences_final():
    """法說會：改用另一個更穩定的解析邏輯"""
    report = "🎙️ 【今日法說會資訊】\n"
    try:
        # 換成一個資訊彙整更直接的頁面
        url = "https://histock.tw/stock/mktcalendar.aspx"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        
        today = datetime.now().strftime('%m/%d')
        found = []
        
        # 遍歷所有包含股票資訊的區塊
        for item in soup.select('.cal-item'):
            text = item.get_text(strip=True)
            # 如果文字中包含今日日期，且看起來像公司名稱(有括號代號)
            if today in text and "(" in text:
                # 清理掉多餘的日期字眼，只留名稱代號
                clean_text = text.replace(today, "").strip()
                found.append(f"• {clean_text}")
        
        if not found:
            return report + "  (今日暫無公開法說)\n"
        
        return report + "\n".join(found[:15]) + "\n"
    except:
        return report + "  (資料讀取中...)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    content = get_disposition_final() + get_conferences_final()
    now_str = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股偵測報表】 {now_str}\n\n{content}")
