import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 讀取金鑰 ---
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

def get_stable_data():
    today_dt = datetime.now()
    # 抓取範圍擴大到 10 天，確保即便更新延遲也一定有資料
    start_date = (today_dt - timedelta(days=10)).strftime('%Y-%m-%d')
    today = today_dt.strftime('%Y-%m-%d')
    
    base_url = "https://api.finmindtrade.com/api/v4/data"
    report = "⚠️ 【台股注意/處置最新清單】\n"
    
    # 1. 注意股：抓取最近一次的完整公告
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={start_date}", timeout=25).json()
        if res.get('data'):
            df = pd.DataFrame(res['data'])
            last_date = df['date'].max() # 找到資料庫裡最新的公告日
            df_last = df[df['date'] == last_date]
            report += f"\n📍 注意股 (公告日:{last_date}):\n"
            for _, row in df_last.head(15).iterrows():
                report += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
        else:
            report += "\n📍 注意股: 查無近期公告\n"
    except:
        report += "\n📍 注意股: 資料擷取暫時中斷\n"

    # 2. 處置股：抓取目前生效中的清單
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={start_date}", timeout=25).json()
        if res.get('data'):
            df_p = pd.DataFrame(res['data'])
            # 過濾出到今天為止還沒結束處置的股票
            active = df_p[df_p['end_date'] >= today].sort_values('end_date')
            if not active.empty:
                report += "\n🚫 處置中 (生效期內):\n"
                for _, row in active.iterrows():
                    report += f"• {row['stock_id']} (至 {row['end_date']})\n"
            else:
                report += "\n🚫 處置股: 目前無生效標的\n"
        else:
            report += "\n🚫 處置股: 查無資料\n"
    except:
        report += "\n🚫 處置股: 連線異常\n"

    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID: return
    
    content = get_stable_data()
    now_str = datetime.now().strftime('%m/%d %H:%M')
    final_msg = f"💡 台股早報 ({now_str})\n\n{content}\n數據源：FinMind 穩定供應"
    
    send_line_push(final_msg)

if __name__ == "__main__":
    main()
