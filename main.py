import os
import requests
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_clean_disposition():
    """證交所 API 強效去重與格式化"""
    url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        if 'data' not in data: return "🚫 【今日處置股】\n  (官方更新中)\n"
        
        # 關鍵去重邏輯：使用 dict，鍵值為代號，確保 3054 這種重複項只留最後一筆
        final_list = {}
        for row in data['data']:
            code = str(row[1]).strip()
            name = str(row[2]).strip()
            duration = str(row[0]).strip()
            # 存入字典：這會自動覆蓋掉重複的代號
            final_list[code] = f"• {code} {name}\n  ⏳ {duration}"
        
        if not final_list: return "🚫 【今日處置股】\n  (今日無資料)\n"
        
        report = "🚫 【今日處置股名單】\n"
        return report + "\n".join(final_list.values()) + "\n\n"
    except:
        return "❌ 處置股讀取失敗\n\n"

def get_investor_conf_robust():
    """法說會：改用最原始的文字特徵比對法"""
    report = "🎙️ 【今日法說會資訊】\n"
    try:
        # 改用公開資訊較集中的財經新聞源
        url = "https://tw.stock.yahoo.com/calendar/conference"
        res = requests.get(url, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 針對 Yahoo 結構抓取所有可能標題
        titles = soup.select('div[class*="StyledTitle"]')
        found = []
        for t in titles:
            text = t.get_text(strip=True)
            if text: found.append(f"• {text}")
            
        if not found: return report + "  (今日暫無或尚未更新)\n"
        return report + "\n".join(found[:10])
    except:
        return report + "  (讀取異常)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    dis = get_clean_disposition()
    con = get_investor_conf_robust()
    now_date = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股偵測終極報表】 {now_date}\n\n{dis}{con}")
