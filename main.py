import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 1. 從 GitHub Secrets 讀取金鑰 ---
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

def get_stock_data():
    """獲取『當下最新』與最近 3 日的注意/處置股"""
    today_dt = datetime.now()
    today = today_dt.strftime('%Y-%m-%d')
    three_days_ago = (today_dt - timedelta(days=3)).strftime('%Y-%m-%d')
    base_url = "https://api.finmindtrade.com/api/v4/data"
    
    report = ""
    
    # --- 1. 注意股：鎖定最新公告 ---
    report += "⚠️ 【最新注意股清單】\n"
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={three_days_ago}", timeout=20).json()
        if res.get('data'):
            df = pd.DataFrame(res['data'])
            # 取得資料庫中最新的日期 (可能是昨天傍晚或今天清晨)
            latest_date = df['date'].max()
            df_latest = df[df['date'] == latest_date]
            
            report += f"📍 公告日期: {latest_date}\n"
            for _, row in df_latest.iterrows():
                report += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
        else:
            report += "📍 目前暫無最新注意股公告\n"
    except:
        report += "📍 注意股資料讀取異常\n"

    # --- 2. 處置股：抓取『目前正在處置中』的股票 ---
    report += "\n🚫 【目前處置中股票】\n"
    try:
        # 處置股需要較長的範圍來判斷結束日期
        ten_days_ago = (today_dt - timedelta(days=10)).strftime('%Y-%m-%d')
        res = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={ten_days_ago}", timeout=20).json()
        if res.get('data'):
            df_p = pd.DataFrame(res['data'])
            # 篩選條件：處置結束日期 >= 今天
            df_active = df_p[df_p['end_date'] >= today].sort_values(by='end_date')
            
            if not df_active.empty:
                for _, row in df_active.iterrows():
                    report += f"• {row['stock_id']} (至 {row['end_date']})\n"
            else:
                report += "📍 目前無處置中之標的\n"
        else:
            report += "📍 目前查無處置資料\n"
    except:
        report += "📍 處置股資料連線異常\n"

    # --- 3. 法說會 ---
    report += "\n📅 【今日法說會預告】\n"
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockInvestorConference&start_date={today}", timeout=20).json()
        if res.get('data') and len(res['data']) > 0:
            df_c = pd.DataFrame(res['data'])
            stocks = df_c[['stock_id', 'stock_name']].drop_duplicates()
            for _, row in stocks.iterrows():
                report += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
        else:
            report += "今日無預定法說會。\n"
    except:
        report += "法說會資料暫時無法更新。\n"
        
    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("Error: Missing Secrets"); return

    report_content = get_stock_data()
    now_str = datetime.now().strftime('%m/%d %H:%M')
    final_msg = f"💡 台股早報 ({now_str})\n\n{report_content}\n祝投資順利！📈"
    
    status = send_line_push(final_msg)
    print(f"發送結束，狀態碼: {status}")

if __name__ == "__main__":
    main()
