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

def get_yahoo_web_data():
    """直接解析 Yahoo 股市網頁，這是目前最穩定的方法"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    report = ""
    
    # 抓取注意股網頁
    try:
        url = "https://tw.stock.yahoo.com/stock-notice-list"
        res = requests.get(url, headers=headers, timeout=20)
        # 用簡單的正則表達式抓取股票代碼與名稱
        matches = re.findall(r'"symbol":"(\d+)","name":"([^"]+)"', res.text)
        if matches:
            report += "⚠️ 【最新注意股清單】\n"
            # 取得不重複的標的
            seen = set()
            for sym, name in matches[:15]:
                if sym not in seen:
                    report += f"• {sym} {name}\n"
                    seen.add(sym)
        else:
            report += "⚠️ 【注意股】網頁結構異動，請檢查\n"
    except:
        report += "⚠️ 【注意股】擷取連線失敗\n"

    # 抓取處置股網頁
    try:
        url = "https://tw.stock.yahoo.com/stock-disposition-list"
        res = requests.get(url, headers=headers, timeout=20)
        matches = re.findall(r'"symbol":"(\d+)","name":"([^"]+)"', res.text)
        if matches:
            report += "\n🚫 【最新處置股清單】\n"
            seen = set()
            for sym, name in matches[:10]:
                if sym not in seen:
                    report += f"• {sym} {name}\n"
                    seen.add(sym)
        else:
            report += "\n🚫 【處置股】目前暫無公告標的\n"
    except:
        report += "\n🚫 【處置股】擷取連線失敗\n"
        
    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID: return
    
    stock_report = get_yahoo_web_data()
    now_str = datetime.now().strftime('%m/%d %H:%M')
    
    final_msg = f"💡 台股即時報 ({now_str})\n\n{stock_report}\n\n來源：Yahoo 股市網頁解析"
    send_line_push(final_msg)

if __name__ == "__main__":
    main()
