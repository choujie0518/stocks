import os
import requests
import pandas as pd
from datetime import datetime

# 讀取金鑰
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        return res.status_code
    except:
        return 500

def get_notice_and_disposition():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.twse.com.tw/zh/page/announcement/notice.html'
    }
    ts = str(int(datetime.now().timestamp()))
    notice_url = f"https://www.twse.com.tw/zh/api/noticeData?response=json&_={ts}"
    punish_url = f"https://www.twse.com.tw/zh/api/punishData?response=json&_={ts}"
    
    msg = "⚠️ 【注意/處置股清單】\n"
    
    try:
        # 1. 注意股
        res_n = requests.get(notice_url, headers=headers, timeout=20).json()
        if res_n.get('stat') == 'OK' and res_n.get('data'):
            msg += "📍注意股:\n"
            for i in res_n['data'][:10]:
                msg += f"• {i[1]} {i[2]}\n"
        else:
            msg += "📍注意股: 今日無新增\n"

        # 2. 處置股
        res_p = requests.get(punish_url, headers=headers, timeout=20).json()
        if res_p.get('stat') == 'OK' and res_p.get('data'):
            msg += "\n🚫處置股 (處置中):\n"
            for i in res_p['data'][:8]:
                msg += f"• {i[1]} {i[2]} ({i[3]})\n"
        else:
            msg += "\n🚫處置股: 無\n"
    except:
        msg += "📍資料擷取失敗，請檢查證交所連線\n"
        
    return msg

def get_investor_conference():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInvestorConference&start_date={today}"
    msg = "\n📅 【今日法說會預告】\n"
    try:
        res = requests.get(url, timeout=20).json()
        if res.get('msg') == 'success' and res.get('data'):
            df = pd.DataFrame(res['data'])
            df_today = df[df['date'] == today]
            if not df_today.empty:
                stocks = df_today[['stock_id', 'stock_name']].drop_duplicates()
                for _, row in stocks.iterrows():
                    msg += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
            else:
                msg += "今日無預定法說會。\n"
        else:
            msg += "今日無預定法說會。\n"
    except:
        msg += "法說會資料暫時無法更新。\n"
    return msg

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("Missing Tokens"); return
    
    report = f"💡 台股早報 ({datetime.now().strftime('%m/%d')})\n\n"
    report += get_notice_and_disposition()
    report += get_investor_conference()
    report += "\n祝投資順利！📈"
    
    status = send_line_push(report)
    print(f"發送狀態: {status}")

if __name__ == "__main__":
    main()
