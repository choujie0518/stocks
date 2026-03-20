import os
import requests
import datetime

FINMIND_TOKEN = os.getenv("FINMIND_API_TOKEN")
LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_finmind_data(dataset, days_back=0):
    """取得資料，若當天沒資料可調整回溯天數"""
    url = "https://api.finmindtrade.com/api/v4/data"
    # 計算日期：今天扣除 days_back 天
    target_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    params = {
        "dataset": dataset,
        "token": FINMIND_TOKEN,
        "start_date": target_date
    }
    
    try:
        res = requests.get(url, params=params, timeout=20)
        data = res.json().get("data", [])
        return data, target_date
    except:
        return [], target_date

def get_report():
    report = ""
    
    # --- 1. 處置股公告 (回溯抓取最新的一筆公告日) ---
    dis_report = "🚫 【最新處置股公告】\n"
    for i in range(5): # 最多往回找 5 天
        data, date_str = get_finmind_data("TaiwanStockAnnouncement", days_back=i)
        found = [item for item in data if "處置" in item.get("type", "")]
        if found:
            dis_report += f"📅 公告日期: {date_str}\n"
            for item in found:
                dis_report += f"• {item.get('stock_id')} (詳情請見官網)\n"
            break
    else:
        dis_report += "  (近 5 日無新處置公告)\n"
    
    # --- 2. 法說會資訊 (回溯找最近有登記的一天) ---
    conf_report = "\n🎙️ 【近期法說會資訊】\n"
    for i in range(7): # 法說會通常較稀疏，往回找 7 天
        data, date_str = get_finmind_data("TaiwanStockConference", days_back=i)
        if data:
            conf_report += f"📅 資訊日期: {date_str}\n"
            for con in data:
                conf_report += f"• {con.get('stock_id')} {con.get('stock_name')}\n"
            break
    else:
        conf_report += "  (近期無登記法說資訊)\n"
        
    return dis_report + conf_report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    if not FINMIND_TOKEN:
        send_line("❌ 錯誤：請在 Secrets 設定 FINMIND_API_TOKEN")
    else:
        content = get_report()
        send_line(f"🛡️ FinMind 智能回溯報表\n\n{content}")
