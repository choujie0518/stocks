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
    today_str = today_dt.strftime('%Y-%m-%d')
    # 這裡很關鍵：強迫抓取過去 20 天，不讓 API 的延遲害我們抓不到資料
    start_date = (today_dt - timedelta(days=20)).strftime('%Y-%m-%d')
    
    base_url = "https://api.finmindtrade.com/api/v4/data"
    msg = ""

    # 1. 抓取處置股 (對標你截圖中的 3/19 旺宏、欣興等)
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={start_date}", timeout=30).json()
        if res.get('data'):
            df = pd.DataFrame(res['data'])
            # 排除掉重複公告，只抓最新狀態，且「結束日期」必須在今天或之後
            df['end_date'] = pd.to_datetime(df['end_date']).dt.strftime('%Y-%m-%d')
            active = df[df['end_date'] >= today_str].drop_duplicates(subset=['stock_id'], keep='last')
            
            if not active.empty:
                msg += "🚫 【處置生效中標的】\n"
                for _, row in active.iterrows():
                    msg += f"• {row['stock_id']} {row.get('stock_name','')} (至 {row['end_date']})\n"
            else:
                msg += "🚫 目前查無生效中之處置股\n"
        else:
            msg += "🚫 處置股 API 同步延遲中\n"
    except:
        msg += "🚫 處置股連線超時\n"

    # 2. 抓取注意股 (抓最近兩次有資料的公告日)
    try:
        res_n = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={start_date}", timeout=30).json()
        if res_n.get('data'):
            df_n = pd.DataFrame(res_n['data'])
            last_date = df_n['date'].max()
            msg += f"\n⚠️ 【最新注意股公告】({last_date})\n"
            latest_notices = df_n[df_n['date'] == last_date]
            for _, row in latest_notices.iterrows():
                msg += f"• {row['stock_id']} {row.get('stock_name','')}\n"
        else:
            msg += "\n⚠️ 目前查無注意股公告\n"
    except:
        msg += "\n⚠️ 注意股連線超時\n"

    return msg

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID: return
    
    content = get_stock_data()
    now_str = datetime.now().strftime('%m/%d %H:%M')
    
    # 最終訊息
    final_msg = f"💡 台股自動報 ({now_str})\n\n{content}\n\n來源：FinMind 數據庫同步"
    
    send_line_push(final_msg)

if __name__ == "__main__":
    main()
