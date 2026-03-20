import os
import requests
import datetime

# 從 GitHub Secrets 讀取
FINMIND_TOKEN = os.getenv("FINMIND_API_TOKEN")
LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_finmind_data(dataset, data_id=None):
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": dataset,
        "token": FINMIND_TOKEN
    }
    if data_id:
        params["data_id"] = data_id
    
    # 取得今天日期
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    params["start_date"] = today
    
    try:
        res = requests.get(url, params=params, timeout=20)
        return res.json().get("data", [])
    except:
        return []

def get_report():
    # 1. 處置股 (從 TaiwanStockPrice 檢查處置狀態或公告)
    # 註：FinMind 的處置資訊通常在 'TaiwanStockPrice' 的 'remark' 或是專門的 'TaiwanStockAnnouncement'
    report = "🚫 【今日處置股名單】\n"
    
    # 這裡我們用最準的「公告」數據集
    announcements = get_finmind_data("TaiwanStockAnnouncement")
    
    found_dis = False
    for item in announcements:
        content = item.get("type", "")
        if "處置" in content:
            code = item.get("stock_id", "")
            date = item.get("date", "")
            report += f"• {code} (公告日: {date})\n"
            found_dis = True
            
    if not found_dis:
        report += "  (今日 API 尚未更新處置公告)\n"

    # 2. 法說會 (從股東大會/法說會數據集抓取)
    report += "\n🎙️ 【今日法說會資訊】\n"
    conferences = get_finmind_data("TaiwanStockConference") # FinMind 專屬法說數據集
    
    if conferences:
        for con in conferences:
            report += f"• {con.get('stock_id')} {con.get('stock_name')}\n  ⏰ 時間: {con.get('start_time')}\n"
    else:
        report += "  (今日暫無登記法說)\n"
        
    return report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    if not FINMIND_TOKEN:
        send_line("❌ 錯誤：未設定 FINMIND_API_TOKEN")
    else:
        final_msg = get_report()
        date_str = datetime.datetime.now().strftime('%Y/%m/%d')
        send_line(f"🛡️ FinMind 專業報表 ({date_str})\n\n{final_msg}")
