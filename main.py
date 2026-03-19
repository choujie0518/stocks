import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_wantgoo_data():
    """從玩股網精準抓取處置股與起訖日"""
    url = "https://www.wantgoo.com/stock/public-info/disposition"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 抓取表格中所有股票行
        table = soup.find('table')
        if not table: return "🚫 【今日處置股】\n  (無法讀取表格，請稍後再試)\n"
        
        rows = table.find_all('tr')[1:] # 跳過表頭
        report = "🚫 【今日處置股名單】\n"
        found = False
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                stock_info = cols[0].get_text(strip=True) # 代號名稱
                start_date = cols[2].get_text(strip=True) # 起始日期
                end_date = cols[3].get_text(strip=True)   # 結束日期
                report += f"• {stock_info}\n  ⏳ {start_date} ~ {end_date}\n"
                found = True
        return report + "\n" if found else "🚫 今日暫無處置股資料\n"
    except Exception as e:
        return f"❌ 處置股讀取異常\n"

def get_yahoo_investor():
    """抓取今日法說會 (改用 HiStock 備用源以確保數據)"""
    url = "https://histock.tw/stock/mktcalendar.aspx"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        today_str = datetime.now().strftime('%m/%d')
        report = "🎙️ 【今日法說會資訊】\n"
        # 尋找包含今日日期的所有連結文字
        found = False
        for link in soup.select('a[title*="法說會"]'):
            parent_text = link.find_parent('div').get_text() if link.find_parent('div') else ""
            if today_str in parent_text or "今日" in parent_text:
                report += f"• {link.get_text(strip=True)}\n"
                found = True
        
        if not found:
            # 暴力搜尋所有 td
            for td in soup.find_all('td'):
                if "法說會" in td.get_text() and today_str in td.get_text():
                    report += f"• {td.get_text(strip=True).replace('法說會', '')}\n"
                    found = True
                    
        return report + "\n" if found else "🎙️ 【今日法說會】\n  (今日暫無或尚未更新)\n"
    except:
        return "🎙️ 法說會抓取異常\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    dis_report = get_wantgoo_data()
    con_report = get_yahoo_investor()
    
    now = datetime.now().strftime('%Y/%m/%d')
    final_msg = f"🚀 台股自動報表 ({now})\n\n{dis_report}{con_report}"
    send_line(final_msg)
