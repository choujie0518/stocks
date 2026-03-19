import os
import requests
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_real_disposition():
    """強制校對版：解決代號重複、遺失中文名稱問題"""
    api_url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        data = res.json().get('data', [])
        
        # 使用 dict 進行物理去重：key = 代號
        stock_map = {}
        for row in data:
            if len(row) < 3: continue
            
            # 證交所 API 欄位：[0]日期, [1]代號, [2]名稱, [3]處置內容...
            date_range = str(row[0]).strip()
            code = str(row[1]).strip()
            name = str(row[2]).strip()
            
            # 只要代號相同，不論出現幾次，我們只保留一筆最完整的
            stock_map[code] = f"• {code} {name}\n  ⏳ {date_range}"
            
        if not stock_map:
            return "🚫 【今日處置股】\n  (今日暫無處置標的)\n"
            
        # 按照代號排序，看起來比較整齊
        sorted_report = [stock_map[k] for k in sorted(stock_map.keys())]
        return "🚫 【今日處置股名單】\n" + "\n".join(sorted_report) + "\n\n"
    except:
        return "🚫 【今日處置股】\n  (系統連線異常)\n\n"

def get_investor_conference():
    """法說會：改用公開資訊觀測站(MOPS)的替代API源，避開IP封鎖"""
    report_title = "🎙️ 【今日法說會資訊】\n"
    try:
        # 改用更穩定的 Anue 鉅亨 API
        today = datetime.now().strftime('%Y-%m-%d')
        api_url = f"https://api.cnyes.com/media/api/v1/news/calendar?date={today}"
        res = requests.get(api_url, timeout=15)
        items = res.json().get('data', {}).get('items', [])
        
        found = []
        for item in items:
            title = item.get('title', '')
            if '法說' in title:
                found.append(f"• {title}")
        
        if not found:
            return report_title + "  (今日暫無公開法說)\n"
        return report_title + "\n".join(found)
    except:
        return report_title + "  (資料讀取異常)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    dis_report = get_real_disposition()
    con_report = get_investor_conference()
    now = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 台股偵測報表 ({now})\n\n{dis_report}{con_report}")
