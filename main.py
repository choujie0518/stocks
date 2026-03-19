import os
import requests
import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_mapping():
    """從股價 API 獲取代號/名稱對照，這比單純抓處置股 API 穩定得多"""
    mapping = {}
    try:
        # 使用證交所每日收盤行情作為名稱庫，這是不會變動的穩定源
        url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_AVG_ALL"
        res = requests.get(url, timeout=10)
        for item in res.json():
            mapping[item['Code']] = item['Name']
    except: pass
    return mapping

def get_data():
    names = get_mapping()
    # 1. 抓取處置股
    dis_msg = "🚫 【今日處置股名單】\n"
    try:
        res = requests.get("https://www.twse.com.tw/rwd/zh/announcement/punish?response=json", timeout=10)
        data = res.json().get('data', [])
        stocks = {}
        for row in data:
            code = str(row[1]).strip()
            # 強制對照名稱，若找不到則顯示原始欄位
            name = names.get(code, str(row[2]).strip())
            # 確保不會抓到「第一次處置」這種廢話
            if "處置" in name or "撮合" in name:
                name = names.get(code, "未知")
            stocks[code] = f"• {code} {name}\n  ⏳ {row[0]}"
        
        if not stocks: dis_msg += "  (今日暫無標的)\n"
        else: dis_msg += "\n".join([stocks[k] for k in sorted(stocks.keys())])
    except: dis_msg += "  (處置股讀取失敗)\n"

    # 2. 抓取法說會 (改用對爬蟲最友善的來源)
    con_msg = "\n\n🎙️ 【今日法說會資訊】\n"
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        # 改用 Anue API 的穩定接口
        res = requests.get(f"https://api.cnyes.com/media/api/v1/news/calendar?date={today}", timeout=10)
        events = res.json().get('data', {}).get('items', [])
        found = [f"• {e['title']}" for e in events if '法說' in e.get('title', '')]
        
        if not found: con_msg += "  (今日暫無公開法說)\n"
        else: con_msg += "\n".join(found)
    except: con_msg += "  (法說會暫時無法連線)\n"
    
    return dis_msg + con_msg

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    report = get_data()
    now = datetime.datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股精準偵測】{now}\n\n{report}")
