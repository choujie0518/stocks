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

def get_real_stock_data():
    # 擴大搜索到 14 天，確保一定能抓到像你表格中 3/5 就開始處置的股票
    today_dt = datetime.now()
    start_date = (today_dt - timedelta(days=14)).strftime('%Y-%m-%d')
    today = today_dt.strftime('%Y-%m-%d')
    
    base_url = "https://api.finmindtrade.com/api/v4/data"
    msg = "📊 【台股實時清單核對】\n"

    # --- 處置股核對 (對標你提供的表格) ---
    try:
        res_p = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={start_date}", timeout=25).json()
        if res_p.get('data'):
            df_p = pd.DataFrame(res_p['data'])
            # 核心邏輯：結束日期必須大於等於今天，才是「現在處置中」
            active = df_p[df_p['end_date'] >= today].sort_values('end_date')
            
            if not active.empty:
                msg += "\n🚫 處置中標的 (核對成功):\n"
                for _, row in active.iterrows():
                    msg += f"• {row['stock_id']} {row.get('stock_name', '')} (至 {row['end_date']})\n"
            else:
                msg += "\n🚫 目前無生效中之處置股\n"
        else:
            msg += "\n🚫 API 資料庫尚未同步最新處置名單\n"
    except:
        msg += "\n🚫 處置股連線異常\n"

    # --- 注意股 ---
    try:
        res_n = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={start_date}", timeout=25).json()
        if res_n.get('data'):
            df_n = pd.DataFrame(res_n['data'])
            last_date = df_n['date'].max()
            msg += f"\n⚠️ 最新注意股 (公告日: {last_date}):\n"
            # 抓出最新一次公告的所有股票
            latest_notices = df_n[df_n['date'] == last_date]
            for _, row in latest_notices.head(10).iterrows():
                msg += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
        else:
            msg += "\n⚠️ 近期無注意股公告資料\n"
    except:
        msg += "\n⚠️ 注意股連線異常\n"

    return msg

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID: return
    content = get_real_stock_data()
    now_str = datetime.now().strftime('%m/%d %H:%M')
    final_msg = f"{content}\n\n更新時間: {now_str}\n請注意投資風險！"
    send_line_push(final_msg)

if __name__ == "__main__":
    main()
