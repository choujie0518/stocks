import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# 讀取金鑰
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=payload, timeout=15)

def get_pro_stock_report():
    today_dt = datetime.now()
    today_str = today_dt.strftime('%Y-%m-%d')
    # 暴力抓取過去 30 天，確保絕對能覆蓋所有正在生效的處置股
    start_date = (today_dt - timedelta(days=30)).strftime('%Y-%m-%d')
    
    base_url = "https://api.finmindtrade.com/api/v4/data"
    report = "📋 【台股專業版：生效中清單】\n"
    
    # 1. 處置股核對 (對標官網名單)
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={start_date}", timeout=30).json()
        if res.get('data'):
            df = pd.DataFrame(res['data'])
            # 關鍵邏輯：只顯示「今天還沒結束」的處置標的
            active_df = df[df['end_date'] >= today_str].sort_values('end_date')
            if not active_df.empty:
                report += "\n🚫 【處置股生效中】\n"
                for _, row in active_df.iterrows():
                    report += f"• {row['stock_id']} {row.get('stock_name','')} (至 {row['end_date']})\n"
            else:
                report += "\n🚫 目前無生效中處置標的\n"
        else:
            report += "\n🚫 處置資料暫時無法更新\n"
    except:
        report += "\n🚫 處置資料庫連線超時\n"

    # 2. 注意股核對 (抓取最近 5 天內的所有公告)
    try:
        notice_start = (today_dt - timedelta(days=5)).strftime('%Y-%m-%d')
        res_n = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={notice_start}", timeout=30).json()
        if res_n.get('data'):
            df_n = pd.DataFrame(res_n['data'])
            # 抓出最新的一個公告日
            latest_day = df_n['date'].max()
            report += f"\n⚠️ 【最新注意股公告】({latest_day})\n"
            latest_list = df_n[df_n['date'] == latest_day]
            for _, row in latest_list.iterrows():
                report += f"• {row['stock_id']} {row.get('stock_name','')}\n"
        else:
            report += "\n⚠️ 近日暫無注意股公告\n"
    except:
        report += "\n⚠️ 注意股資料庫連線超時\n"

    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID: return
    content = get_pro_stock_report()
    now_str = datetime.now().strftime('%m/%d %H:%M')
    final_msg = f"{content}\n\n數據同步時間: {now_str}\n※ 資訊以證交所最終公告為準"
    send_line_push(final_msg)

if __name__ == "__main__":
    main()
