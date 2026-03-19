import os
import requests
import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_report():
    # --- 1. 處置股 (重新調整欄位抓取邏輯) ---
    dis_report = "🚫 【今日處置股名單】\n"
    try:
        res = requests.get("https://www.twse.com.tw/rwd/zh/announcement/punish?response=json", timeout=15)
        raw_data = res.json().get('data', [])
        stocks = {}
        for row in raw_data:
            code = str(row[1]).strip()
            date_info = str(row[0]).strip()
            
            # 遍歷這一行的所有欄位，找「不含數字」且「不是廢話」的欄位當名稱
            name = "未知名稱"
            for cell in row:
                c_str = str(cell).strip()
                # 排除掉日期、代號、以及包含處置說名的長句子
                if len(c_str) >= 2 and len(c_str) <= 6 and not any(char.isdigit() for char in c_str):
                    if "處置" not in c_str and "撮合" not in c_str:
                        name = c_str
                        break
            
            # 以 code 為 Key 強制去重，3054 絕對只會出現一次
            stocks[code] = f"• {code} {name}\n  ⏳ {date_info}"
        
        if not stocks: dis_report += "  (今日暫無標的)\n"
        else: dis_report += "\n".join([stocks[k] for k in sorted(stocks.keys())])
    except: dis_report += "  (處置股讀取失敗)\n"

    # --- 2. 法說會 (同步修正) ---
    con_report = "\n\n🎙️ 【今日法說會資訊】\n"
    try:
        # 改用更直覺的 MOPS 彙整源
        url = "https://openapi.twse.com.tw/v1/mops/t100sb02_1"
        res = requests.get(url, timeout=15)
        today_ymd = datetime.datetime.now().strftime("%Y%m%d")
        today_roc = str(datetime.datetime.now().year - 1911) + datetime.datetime.now().strftime("%m%d")
        
        found = []
        for item in res.json():
            m_date = str(item.get('MeetDate', '')).replace('/', '')
            # 同時比對西元與民國日期
            if m_date == today_ymd or m_date == today_roc:
                found.append(f"• {item.get('Code')} {item.get('Name')}")
        
        if not found: con_report += "  (今日官方暫無登記法說)\n"
        else: con_report += "\n".join(sorted(list(set(found))))
    except: con_report += "  (連線失敗)\n"
        
    return dis_report + con_report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    content = get_report()
    now = datetime.datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股偵測】{now}\n\n{content}")
