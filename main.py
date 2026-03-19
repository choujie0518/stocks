import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_stock_report(url, title, type_filter):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if not table: return f"【{title}】\n  (今日官網尚未更新)\n"
        
        rows = table.find_all('tr')
        content = f"【{title}】\n"
        count = 0
        for row in rows[1:]:
            cols = row.find_all('td')
            # 根據 HiStock 頁面邏輯，過濾注意(m=1)或處置(預設)
            if len(cols) >= 2:
                stock_info = cols[0].get_text(strip=True)
                date_info = cols[1].get_text(strip=True)
                content += f"• {stock_info}\n  📅 {date_info}\n"
                count += 1
            if count >= 10: break # 避免訊息過長
        return content + "\n"
    except:
        return f"❌ {title}連線異常\n"

def get_investor_conference():
    # 專門爬取法說會行事曆
    url = "https://histock.tw/stock/mktcalendar.aspx"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 尋找當天日期標籤下的公司
        today_str = datetime.now().strftime('%m/%d')
        report = "🎙️ 【今日法說會重點】\n"
        items = soup.find_all('div', class_='cal-item') # 假設結構
        found = False
        for item in items:
            if today_str in item.get_text():
                report += f"• {item.get_text(strip=True)}\n"
                found = True
        return report if found else "🎙️ 【今日法說會】\n  (今日暫無排定法說)\n"
    except:
        return "🎙️ 【今日法說會】\n  (抓取失敗，請檢查網路)\n"

def send_line(msg):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    # 處置股
    dis_report = get_stock_report("https://histock.tw/stock/public.aspx", "🚫 今日處置股", "dis")
    # 注意股 (參數 m=1)
    not_report = get_stock_report("https://histock.tw/stock/public.aspx?m=1", "⚠️ 今日注意股", "not")
    # 法說會
    con_report = get_investor_conference()
    
    now = datetime.now().strftime('%Y/%m/%d %H:%M')
    final_msg = f"🚀 台股自動化報表 ({now})\n\n{dis_report}{not_report}{con_report}"
    send_line(final_msg)
