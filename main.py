import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 1. 從 GitHub Secrets 讀取金鑰 ---
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    """發送推播至 LINE 官方帳號"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        return res.status_code
    except Exception as e:
        print(f"LINE 發送異常: {e}")
        return 500

def get_stock_data():
    """使用 FinMind API 獲取注意股、處置股與法說會"""
    # 計算日期：包含今天與過去 3 天，確保資訊不遺漏
    today_dt = datetime.now()
    today = today_dt.strftime('%Y-%m-%d')
    three_days_ago = (today_dt - timedelta(days=3)).strftime('%Y-%m-%d')
    
    base_url = "https://api.finmindtrade.com/api/v4/data"
    report = ""
    
    # 1. 抓取注意股 (過去 3 天內最新的公告)
    report += "⚠️ 【注意/處置股清單】\n"
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={three_days_ago}", timeout=20).json()
        if res.get('data'):
            df = pd.DataFrame(res['data'])
            latest_date = df['date'].max()
            df_latest = df[df['date'] == latest_date]
            report += f"📍最新注意股 ({latest_date}):\n"
            for _, row in df_latest.head(15).iterrows():
                report += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
        else:
            report += "📍注意股: 近三日無新增\n"
    except:
        report += "📍注意股: 資料連線異常\n"

    # 2. 抓取處置股 (目前還在處置期間內的)
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={three_days_ago}", timeout=20).json()
        if res.get('data'):
            df_p = pd.DataFrame(res['data'])
            # 過濾出今天還在處置期的股票
            df_active = df_p[df_p['end_date'] >= today]
            if not df_active.empty:
                report += "\n🚫處置股 (處置期間內):\n"
                for _, row in df_active.head(10).iterrows():
                    report += f"• {row['stock_id']} (至 {row['end_date']})\n"
            else:
                report += "\n🚫處置股: 目前無標的\n"
        else:
            report += "\n🚫處置股: 目前無標的\n"
    except:
        report += "\n🚫處置股: 資料連線異常\n"

    # 3. 抓取法說會 (僅限今日)
    report += "\n📅 【今日法說會預告】\n"
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockInvestorConference&start_date={today}", timeout=20).json()
        if res.get('data'):
            df_c = pd.DataFrame(res['data'])
            df_today = df_c[df_c['date'] == today]
            if not df_today.empty:
                stocks = df_today[['stock_id', 'stock_name']].drop_duplicates()
                for _, row in stocks.iterrows():
                    report += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
            else:
                report += "今日無預定法說會。\n"
        else:
            report += "今日無預定法說會。\n"
    except:
        report += "法說會資料連線異常。\n"
        
    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("Missing Tokens"); return
    
    # 組合訊息
    report_content = get_stock_data()
    final_msg = f"💡 台股早報 ({datetime.now().strftime('%m/%d')})\n\n{report_content}\n祝投資順利！📈"
    
    # 發送
    status = send_line_push(final_msg)
    print(f"任務結束，發送狀態: {status}")

if __name__ == "__main__":
    main()
