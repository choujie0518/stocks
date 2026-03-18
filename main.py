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

def get_stock_data():
    """使用 FinMind API 獲取注意股、處置股、法說會"""
    today = datetime.now().strftime('%Y-%m-%d')
    base_url = "https://api.finmindtrade.com/api/v4/data"
    
    report = ""
    
    # 1. 抓取注意股
    report += "⚠️ 【注意/處置股清單】\n"
    try:
        # FinMind 的注意股資料集名稱為 TaiwanStockNotice
        res = requests.get(f"{base_url}?dataset=TaiwanStockNotice&start_date={today}", timeout=20).json()
        if res.get('data'):
            report += "📍注意股:\n"
            for i in res['data'][:10]:
                report += f"• {i['stock_id']} {i.get('stock_name', '')}\n"
        else:
            report += "📍注意股: 今日無新增或查無資料\n"
    except:
        report += "📍注意股: 暫時無法連線\n"

    # 2. 抓取處置股
    try:
        # FinMind 的處置股資料集名稱為 TaiwanStockDisposition
        res = requests.get(f"{base_url}?dataset=TaiwanStockDisposition&start_date={today}", timeout=20).json()
        if res.get('data'):
            report += "\n🚫處置股 (處置中):\n"
            for i in res['data'][:8]:
                report += f"• {i['stock_id']} ({i['start_date']}~{i['end_date']})\n"
        else:
            report += "\n🚫處置股: 目前無標的\n"
    except:
        report += "\n🚫處置股: 擷取異常\n"

    # 3. 抓取法說會
    report += "\n📅 【今日法說會預告】\n"
    try:
        res = requests.get(f"{base_url}?dataset=TaiwanStockInvestorConference&start_date={today}", timeout=20).json()
        if res.get('data'):
            df = pd.DataFrame(res['data'])
            df_today = df[df['date'] == today]
            if not df_today.empty:
                stocks = df_today[['stock_id', 'stock_name']].drop_duplicates()
                for _, row in stocks.iterrows():
                    report += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
            else:
                report += "今日無預定法說會。\n"
        else:
            report += "今日無預定法說會。\n"
    except:
        report += "法說會資料暫時無法更新。\n"
        
    return report

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("Missing Tokens"); return
    
    header_text = f"💡 台股早報 ({datetime.now().strftime('%m/%d')})\n\n"
    content = get_stock_data()
    footer_text = "\n祝投資順利！📈"
    
    final_msg = header_text + content + footer_text
    status = send_line_push(final_msg)
    print(f"發送狀態: {status}")

if __name__ == "__main__":
    main()
