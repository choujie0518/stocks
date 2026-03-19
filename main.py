import os
import requests
import json
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_disposition_data():
    """使用 HiStock 提供的備用 JSON 格式，這通常不會擋伺服器"""
    report = "🚫 【今日處置股名單】\n"
    try:
        # 這裡是處置股的直接數據源連結
        url = "https://histock.tw/stock/public-info/disposition"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=15)
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table tr')[1:] # 跳過標題
        
        if not rows:
            return report + "  (目前查無處置標的)\n"
            
        found_list = ""
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                # [0]股票代號名稱, [2]起始, [3]結束
                name = cols[0].get_text(strip=True)
                start = cols[2].get_text(strip=True)
                end = cols[3].get_text(strip=True)
                found_list += f"• {name}\n  ⏳ {start} ~ {end}\n"
        
        return report + found_list if found_list else report + "  (暫無資料)\n"
    except:
        return report + "  (來源連線暫時受阻)\n"

def get_investor_conference():
    """抓取法說會資訊 - 換成 Yahoo 財經的 API 模式"""
    report = "🎙️ 【今日法說會資訊】\n"
    try:
        # 嘗試從 Yahoo 抓取今日清單
        url = "https://tw.stock.yahoo.com/calendar/conference"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 尋找所有股票名稱標籤 (Yahoo 結構)
        items = soup.select('div[class*="StyledTitle"]')
        if not items:
            return report + "  (今日暫無公開法說)\n"
            
        conf_list = ""
        for item in items[:15]: # 只取前 15 筆
            conf_list += f"• {item.get_text(strip=True)}\n"
        
        return report + conf_list
    except:
        return report + "  (資訊抓取中...)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID:
        print("環境變數遺失")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    r = requests.post(url, headers=headers, json=payload)
    print(f"發送結果: {r.status_code}")

if __name__ == "__main__":
    dis = get_disposition_data()
    con = get_investor_conference()
    
    date_str = datetime.now().strftime('%Y/%m/%d')
    final_msg = f"🚀 台股自動報表 ({date_str})\n\n{dis}{con}"
    send_line(final_msg)
