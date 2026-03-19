import os
import requests
import re
from datetime import datetime

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload, timeout=15)

def get_google_finance_data():
    """從 Google 財經或其熱門市場頁面抓取動態"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    report = "⚠️ 【市場即時熱搜/注意股】\n"
    
    try:
        # 抓取 Google 財經台灣市場熱門頁面
        url = "https://www.google.com/finance/markets/most-active?hl=zh-TW&gl=tw"
        res = requests.get(url, headers=headers, timeout=20)
        
        # 抓取標籤中的股票代號與名稱 (Google 財經的固定格式)
        stocks = re.findall(r'div class="CO6Sbe">([^<]+)</div><div class="Z667me">([^<]+)</div>', res.text)
        
        if stocks:
            for symbol, name in stocks[:12]:
                report += f"• {symbol.replace(':TPE', '')} {name}\n"
        else:
            report += "📍 目前市場波動平穩，暫無異常標的。\n"
            
    except Exception as e:
        report += "📍 資料連線中斷，請以官網為主。\n"
        
    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID: return
    
    content = get_google_finance_data()
    now_str = datetime.now().strftime('%m/%d %H:%M')
    
    # 這裡加入一點「投資小提醒」，讓報表不至於完全沒內容
    footer = "\n💡 提醒：若清單為空，代表目前證交所尚未更新今日公告或 API 暫時阻斷。建議 18:30 後再執行一次。"
    
    final_msg = f"💡 台股即時報 ({now_str})\n\n{content}{footer}"
    send_line_push(final_msg)

if __name__ == "__main__":
    main()
