import os
import requests
import pandas as pd
from datetime import datetime

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload, timeout=15)

def get_twse_data():
    # 建立強效 Headers 偽裝成真人瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.twse.com.tw/zh/page/announcement/notice.html'
    }
    
    # 增加隨機參數避免緩存
    ts = str(int(datetime.now().timestamp()))
    notice_url = f"https://www.twse.com.tw/zh/api/noticeData?response=json&_={ts}"
    punish_url = f"https://www.twse.com.tw/zh/api/punishData?response=json&_={ts}"
    
    report = "⚠️ 【證交所即時清單】\n"
    
    try:
        # 1. 抓取注意股
        res_n = requests.get(notice_url, headers=headers, timeout=20).json()
        if res_n.get('stat') == 'OK' and res_n.get('data'):
            report += "📍 最新注意股:\n"
            # 抓前 10 筆，這是證交所官網當下的最新內容
            for i in res_n['data'][:10]:
                report += f"• {i[1]} {i[2]}\n"
        else:
            report += "📍 證交所目前無新增注意股\n"

        # 2. 抓取處置股
        res_p = requests.get(punish_url, headers=headers, timeout=20).json()
        if res_p.get('stat') == 'OK' and res_p.get('data'):
            report += "\n🚫 處置中標的:\n"
            for i in res_p['data'][:8]:
                report += f"• {i[1]} {i[2]} ({i[3]})\n"
        else:
            report += "\n🚫 目前無處置中股票\n"
            
    except Exception as e:
        report += f"\n❌ 證交所連線超時，請稍後再試"
        
    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID:
        return

    # 組合最終訊息
    twse_content = get_twse_data()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    final_msg = f"💡 台股即時報 ({now_str})\n\n{twse_content}\n\n數據源：證交所官網直連"
    
    send_line_push(final_msg)

if __name__ == "__main__":
    main()
