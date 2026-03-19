import os
import requests
import pandas as pd
from datetime import datetime

# 讀取金鑰
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    try:
        requests.post(url, headers=headers, json=payload, timeout=15)
    except:
        pass

def get_yahoo_stock_data():
    """從 Yahoo 股市 API 獲取注意股與處置股"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    report = "⚠️ 【Yahoo 股市即時清單】\n"
    
    try:
        # 1. 抓取注意股 (Yahoo 的 API 介面)
        notice_url = "https://tw.stock.yahoo.com/_json/stock-notice-list"
        res_n = requests.get(notice_url, headers=headers, timeout=20).json()
        
        # Yahoo 資料結構通常在 'list' 欄位
        notices = res_n.get('list', [])
        if notices:
            report += "📍 最新注意股:\n"
            for item in notices[:12]: # 顯示前 12 筆
                report += f"• {item.get('symbol', '')} {item.get('name', '')}\n"
        else:
            report += "📍 注意股: 暫無最新公告\n"

        # 2. 抓取處置股
        disposition_url = "https://tw.stock.yahoo.com/_json/stock-disposition-list"
        res_d = requests.get(disposition_url, headers=headers, timeout=20).json()
        
        dispositions = res_d.get('list', [])
        if dispositions:
            report += "\n🚫 目前處置中:\n"
            for item in dispositions[:10]:
                report += f"• {item.get('symbol', '')} {item.get('name', '')} ({item.get('endDate', '期間內')})\n"
        else:
            report += "\n🚫 處置股: 目前無標的\n"
            
    except Exception as e:
        report += f"\n❌ Yahoo 資料源擷取異常，請手動確認"
        
    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID: return
    
    # 執行 Yahoo 抓取任務
    stock_content = get_yahoo_stock_data()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    final_msg = f"💡 台股早報 ({now_str})\n\n{stock_content}\n\n來源：Yahoo 股市即時同步"
    
    send_line_push(final_msg)

if __name__ == "__main__":
    main()
