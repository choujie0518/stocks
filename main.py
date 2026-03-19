import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 環境變數 ---
LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line(msg):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload, timeout=15)

def get_stock_data():
    # 使用不需要登入的公開 API 數據源
    base_url = "https://api.finmindtrade.com/api/v4/data"
    today = datetime.now().strftime('%Y-%m-%d')
    # 抓取過去 7 天的資料確保涵蓋最新公告
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    report = f"🚀 【台股自動化偵測報表】 {today}\n"
    
    # 1. 抓取處置股
    try:
        res_dis = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={start_date}").json()
        df_dis = pd.DataFrame(res_dis['data'])
        if not df_dis.empty:
            # 篩選出今天還在處置期間的
            active_dis = df_dis[df_dis['end_date'] >= today]
            report += "\n🚫 【處置股名單】\n"
            for _, row in active_dis.iterrows():
                report += f"• {row['stock_id']} (至 {row['end_date']})\n"
        else:
            report += "\n🚫 目前無處置股資料\n"
    except:
        report += "\n🚫 處置股數據讀取失敗\n"

    # 2. 抓取注意股
    try:
        res_not = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={start_date}").json()
        df_not = pd.DataFrame(res_not['data'])
        if not df_not.empty:
            # 抓出最新一天的公告內容
            latest_date = df_not['date'].max()
            today_notices = df_not[df_not['date'] == latest_date]
            report += f"\n⚠️ 【最新注意股】({latest_date})\n"
            for _, row in today_notices.iterrows():
                report += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
    except:
        report += "\n⚠️ 注意股數據讀取失敗\n"

    return report

def main():
    if not LINE_TOKEN or not USER_ID:
        print("缺少金鑰，請檢查 GitHub Secrets")
        return

    # 執行自動抓取
    content = get_stock_data()
    
    # 發送 LINE
    send_line(content)
    print("✅ 自動化任務已執行完成並送出推播")

if __name__ == "__main__":
    main()
