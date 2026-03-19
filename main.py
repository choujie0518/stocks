import os
import requests
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_disposition_fixed():
    """證交所 API 資料去重與中文名稱修正"""
    url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json()
        if 'data' not in data: return "🚫 【今日處置股】\n  (官方更新中)\n"
        
        # 使用 dictionary 確保代號 (item[1]) 絕對不重複
        stocks = {}
        for item in data['data']:
            code = item[1].strip()
            name = item[2].strip()
            date_range = item[0].strip()
            # 存入格式化字串
            stocks[code] = f"• {code} {name}\n  ⏳ {date_range}"
        
        report = "🚫 【今日處置股名單】\n"
        if not stocks: return report + "  (暫無資料)\n"
        
        # 將字典所有的 value 合併
        return report + "\n".join(stocks.values()) + "\n\n"
    except:
        return "🚫 【今日處置股】\n  (讀取異常)\n\n"

def get_investor_conf_fixed():
    """法說會：改用鉅亨網 API (這是目前對爬蟲最友善且準確的來源)"""
    report = "🎙️ 【今日法說會資訊】\n"
    try:
        # 抓取鉅亨網台股行事曆
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://api.cnyes.com/media/api/v1/news/calendar?date={today}"
        res = requests.get(url, timeout=15)
        data = res.json()
        
        found = []
        # 搜尋包含 '法說會' 字眼的事件
        if 'items' in data.get('data', {}):
            for item in data['data']['items']:
                title = item.get('title', '')
                if '法說' in title:
                    found.append(f"• {title}")
        
        if not found:
            return report + "  (今日暫無公開法說)\n"
        return report + "\n".join(found) + "\n"
    except:
        # 備用方案：若 API 失敗，返回一個友善訊息
        return report + "  (目前查無今日法說資訊)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    dis = get_disposition_fixed()
    con = get_investor_conf_fixed()
    now_head = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股偵測報表】 {now_head}\n\n{dis}{con}")
