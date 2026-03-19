import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_data(url, title_name):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if not table: return f"⚠️ {title_name}: 暫無資料\n"
        
        rows = table.find_all('tr')
        report = f"【{title_name}】\n"
        # 抓取前 8 筆確保訊息不會過長被 LINE 擋掉
        for row in rows[1:9]: 
            cols = row.find_all('td')
            if len(cols) >= 2:
                stock = cols[0].get_text(strip=True) # 代號名稱
                info = cols[1].get_text(strip=True)  # 日期或說明
                report += f"• {stock}\n  📅 {info}\n"
        return report + "\n"
    except:
        return f"❌ {title_name}抓取失敗\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    # 1. 處置股頁面
    disposition = get_data("https://histock.tw/stock/public.aspx", "🚫 今日處置股")
    # 2. 注意股頁面
    notice = get_data("https://histock.tw/stock/public.aspx?m=1", "⚠️ 今日注意股")
    # 3. 法說會頁面 (從 HiStock 財經行事曆抓取)
    investor = get_data("https://histock.tw/stock/mktcalendar.aspx", "🎙️ 今日法說會")
    
    now = datetime.now().strftime('%m/%d %H:%M')
    final_report = f"💡 台股自動化報表 ({now})\n\n{disposition}{notice}{investor}"
    send_line(final_report)
