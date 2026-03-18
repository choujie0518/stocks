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
    """使用 FinMind API 獲取最近 3 天的注意股、處置股及當日法說會"""
    # 計算日期：今天與三天前 (確保跨週末也能抓到週五資料)
    today_dt = datetime.now()
    today = today_dt.strftime('%Y-%m-%d')
    three_days_ago = (today_dt - timedelta(days=3)).strftime('%Y-%m-%d')
    
    base_url = "https://api.finmindtrade.com/api/v4/data"
    report = ""
    
    # --- 1. 抓取注意股 (過去 3 天) ---
    report += "⚠️ 【注意/處置股清單】\n"
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={three_days_ago}", timeout=20).json()
        if res.get('data'):
            # 使用 DataFrame 處理，只留最新日期
            df = pd.DataFrame(res['data'])
            latest_date = df['date'].max()
            df_latest = df[df['date'] == latest_date]
            
            report += f"📍最新注意股 ({latest_date}):\n"
            for _, row in df_latest.head(15).iterrows():
                report += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
        else:
            report += "📍注意股: 近三日無新增標的\n"
    except:
        report += "📍注意股: 擷取異常\n"

    # --- 2. 抓取處置股 (目前處置中) ---
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={three_days_ago}", timeout=20).json()
        if res.get('data'):
