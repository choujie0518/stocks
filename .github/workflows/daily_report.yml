import os
import requests
import pandas as pd
from datetime import datetime

# --- 設定區 ---
# GitHub Actions 會自動填入這兩個環境變數
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    res = requests.post(url, headers=headers, json=payload)
    return res.status_code

def get_notice_and_disposition():
    """抓取證交所最新注意及處置股 (加上 Headers 偽裝)"""
    # 偽裝成一般的 Chrome 瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    notice_url = "https://www.twse.com.tw/zh/api/noticeData?response=json"
    punish_url = "https://www.twse.com.tw/zh/api/punishData?response=json"
    
    msg = "⚠️ 【注意/處置股清單】\n"
    
    try:
        # 1. 抓取注意股
        res_n_raw = requests.get(notice_url, headers=headers, timeout=15)
        if res_n_raw.status_code == 200:
            res_n = res_n_raw.json()
            if res_n.get('stat') == 'OK' and res_n.get('data'):
                msg += "📍注意股:\n"
                for i in res_n['data'][:10]:
                    msg += f"• {i[1]} {i[2]}\n"
            else:
                msg += "📍注意股: 今日無新增\n"
        else:
            msg += f"📍注意股: 證交所拒絕訪問 (HTTP {res_n_raw.status_code})\n"

        # 2. 抓取處置股
        res_p_raw = requests.get(punish_url, headers=headers, timeout=15)
        if res_p_raw.status_code == 200:
            res_p = res_p_raw.json()
            if res_p.get('stat') == 'OK' and res_p.get('data'):
                msg += "\n🚫處置股 (處備中):\n"
                for i in res_p['data'][:8]:
                    msg += f"• {i[1]} {i[2]} ({i[3]})\n"
            else:
                msg += "\n🚫處置股: 目前無標的\n"
        else:
            msg += f"\n🚫處置股: 抓取失敗 (HTTP {res_p_raw.status_code})\n"
            
    except Exception as e:
        msg += f"\n❌ 系統連線異常: {e}\n"
        
    return msg

def get_investor_conference():
    """抓取當日法說會 (FinMind API)"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInvestorConference&start_date={today}"
    
    msg = "\n📅 【今日法說會預告】\n"
    try:
        res = requests.get(url, timeout=15).json()
        if res.get('msg') == 'success' and res.get('data'):
            df = pd.DataFrame(res['data'])
            df_today = df[df['date'] == today]
            if not df_today.empty:
                # 排除重複代號並列出
                stocks = df_today[['stock_id', 'stock_name']].drop_duplicates()
                for _, row in stocks.iterrows():
                    msg += f"• {row['stock_id']} {row.get('stock_name', '')}\n"
            else:
                msg += "今日無預定法說會。"
        else:
            msg += "今日無預定法說會。"
    except:
        msg += "法說會資料暫時無法更新。"
        
    return msg

def main():
    print(f"[{datetime.now()}] 啟動台股早報任務...")
    
    # 組合訊息
    report = f"💡 台股早報 ({datetime.now().strftime('%m/%d')})\n\n"
    report += get_notice_and_disposition()
    report += get_investor_conference()
    report += "\n祝投資順利！📈"
    
    # 發送 LINE
    if LINE_ACCESS_TOKEN and USER_ID:
        status = send_line_push(report)
        print(f"LINE 發送狀態碼: {status}")
    else:
        print("錯誤: 找不到 LINE Token 或 User ID，請檢查 GitHub Secrets 設定。")

if __name__ == "__main__":
    main()
