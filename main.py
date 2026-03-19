import os
import requests
import pandas as pd
from datetime import datetime, timedelta

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload, timeout=15)

def get_stock_data():
    today_dt = datetime.now()
    # 擴大搜索範圍至過去 7 天，確保一定有資料
    search_start = (today_dt - timedelta(days=7)).strftime('%Y-%m-%d')
    today = today_dt.strftime('%Y-%m-%d')
    
    base_url = "https://api.finmindtrade.com/api/v4/data"
    report = ""
    
    # 1. 注意股 (抓取最近 7 天內所有的公告)
    report += "⚠️ 【最新注意股清單】\n"
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={search_start}", timeout=20).json()
        if res.get('data'):
            df = pd.DataFrame(res['data'])
            # 取得最新的一天公告日期
            latest_date = df['date'].max()
            df_latest = df[df['date'] == latest_date]
            report += f"📍 最新公告日: {latest_date}\n"
            for _, row in df_latest.iterrows():
                report += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
        else: report += "📍 暫無注意股資料\n"
    except: report += "📍 注意股讀取失敗\n"

    # 2. 處置股 (抓取『目前處置中』的標的)
    report += "\n🚫 【處置中標的】\n"
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={search_start}", timeout=20).json()
        if res.get('data'):
            df_p = pd.DataFrame(res['data'])
            # 篩選出『今天』還在處置期內的股票
            df_active = df_p[df_p['end_date'] >= today].sort_values(by='end_date')
            if not df_active.empty:
                for _, row in df_active.iterrows():
                    report += f"• {row['stock_id']} (至 {row['end_date']})\n"
            else: report += "📍 目前無處置中標的\n"
        else: report += "📍 查無處置資料\n"
    except: report += "📍 處置股讀取失敗\n"

    # 3. 法說會 (今日)
    report += "\n📅 【今日法說預告】\n"
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockInvestorConference&start_date={today}", timeout=20).json()
        if res.get('data'):
            for i in res['data']:
                report += f"• {i['stock_id']} {i.get('stock_name', '')}\n"
        else: report += "今日無預定法說會。\n"
    except: report += "法說會連線異常。\n"
    
    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID: return
    content = get_stock_data()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    final_msg = f"💡 台股早報 ({now_str})\n\n{content}\n祝投資順利！📈"
    send_line_push(final_msg)

if __name__ == "__main__":
    main()
