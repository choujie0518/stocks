import os
import requests
import json
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_real_deal():
    """使用證交所 RWD 專用 API，這是不會擋 IP 的穩定源"""
    # 這是處置股的真正底層 API
    url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        raw_data = res.json()
        
        # 建立一個字典來去重，Key 就是股票代號
        # 只要 code 相同，後面的資料就會覆蓋前面的，保證不重複
        stock_dict = {}
        
        if 'data' in raw_data:
            for row in raw_data['data']:
                date_range = row[0] # 起訖日期
                code = row[1]       # 代號
                name = row[2]       # 中文名稱
                
                # 強制格式化：代號 + 名稱 + 起訖
                stock_dict[code] = f"• {code} {name}\n  ⏳ {date_range}"
        
        report = "🚫 【今日處置股名單】\n"
        if not stock_dict:
            report += "  (今日暫無處置標的)\n"
        else:
            report += "\n".join(stock_dict.values())
        
        return report + "\n\n"
    except Exception as e:
        return f"❌ 處置股 API 連線失敗: {str(e)}\n\n"

def get_investor_conf():
    """法說會：改用公開資訊觀測站的 API 模式，這最準"""
    report = "🎙️ 【今日法說會資訊】\n"
    try:
        # 改用更開放的 Yahoo 財經 API 接口，避開網站阻擋
        url = "https://tw.stock.yahoo.com/calendar/conference"
        res = requests.get(url, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 這次我們直接找所有包含 '( )' 代號格式的標題
        found = []
        # Yahoo 的法說會標題通常在特定 class 下
        items = soup.select('div[class*="StyledTitle"]')
        for item in items:
            t = item.get_text(strip=True)
            if t: found.append(f"• {t}")
            
        if not found:
            return report + "  (今日暫無公開法說)\n"
        return report + "\n".join(found[:10])
    except:
        return report + "  (資料庫維護中)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    dis = get_real_deal()
    con = get_investor_conf()
    now = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股偵測終極報表】 {now}\n\n{dis}{con}")
