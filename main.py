import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_disposition_stocks():
    """抓取處置股及其正確起訖日期"""
    url = "https://www.twse.com.tw/zh/announcement/punish.html" # 證交所官方
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 尋找表格內容
        table = soup.find('table')
        if not table: return "🚫 【今日處置股】\n  (今日暫無處置標的或尚未更新)\n"
        
        rows = table.find_all('tr')
        report = "🚫 【今日處置股名單】\n"
        count = 0
        for row in rows[1:]: # 跳過標題
            cols = row.find_all('td')
            if len(cols) >= 3:
                date_range = cols[0].get_text(strip=True) # 起訖日期
                stock_info = cols[1].get_text(strip=True) + " " + cols[2].get_text(strip=True) # 代號+名稱
                report += f"• {stock_info}\n  ⏳ {date_range}\n"
                count += 1
            if count >= 15: break # 限制長度
        return report + "\n"
    except:
        return "❌ 處置股抓取失敗，請檢查網路。\n"

def get_investor_conference():
    """抓取今日法說會 (切換至 Yahoo 財經源，資訊較即時)"""
    url = "https://tw.stock.yahoo.com/calendar/conference"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 抓取清單項
        items = soup.find_all('li', class_='List(n)')
        report = "🎙️ 【今日法說會資訊】\n"
        found = False
        for item in items:
            text = item.get_text(strip=True)
            # 簡單過濾代號與名稱
            report += f"• {text}\n"
            found = True
        
        if not found:
            # 備用方案：抓取表格類型的法說
            titles = soup.select('div[class*="StyledTitle"]')
            for t in titles:
                report += f"• {t.get_text(strip=True)}\n"
                found = True
                
        return report if found else "🎙️ 【今日法說會】\n  (今日暫無公開法說資訊)\n"
    except:
        return "🎙️ 【今日法說會】\n  (抓取異常)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    dis_report = get_disposition_stocks()
    con_report = get_investor_conference()
    
    # 台灣時間顯示
    now = datetime.now().strftime('%Y/%m/%d')
    final_msg = f"🚀 台股自動報表 ({now})\n\n{dis_report}{con_report}"
    send_line(final_msg)
