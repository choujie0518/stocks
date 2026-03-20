import os
import requests
import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_report():
    report = ""
    # 取得今天日期 (西元與民國格式)
    now = datetime.datetime.now()
    today_std = now.strftime("%Y%m%d")
    today_roc = f"{now.year - 1911}/{now.strftime('%m/%d')}"
    
    # 1. 處置股 (直接從 Open Data 抓取)
    report += "🚫 【今日處置股名單】\n"
    try:
        # 證交所開放資料: 公布處置有價證券彙總表
        url = "https://openapi.twse.com.tw/v1/announcement/punish"
        res = requests.get(url, timeout=20)
        data = res.json()
        
        seen = set()
        count = 0
        for item in data:
            code = item.get('SecuritiesCode', '').strip()
            name = item.get('SecuritiesName', '').strip()
            start_date = item.get('StartDate', '').strip() # 格式: 20260319
            end_date = item.get('EndDate', '').strip()     # 格式: 20260401
            
            # 只抓「目前還在處置中」的股票 (今天日期在區間內)
            if start_date <= today_std <= end_date:
                identity = f"{code}_{start_date}"
                if identity not in seen:
                    # 格式化日期顯示
                    s = f"{start_date[:4]}/{start_date[4:6]}/{start_date[6:]}"
                    e = f"{end_date[:4]}/{end_date[4:6]}/{end_date[6:]}"
                    report += f"• {code} {name}\n  ⏳ 區間: {s} - {e}\n"
                    seen.add(identity)
                    count += 1
        if count == 0: report += "  (今日暫無生效中標的)\n"
    except:
        report += "  (處置股伺服器連線異常)\n"

    # 2. 法說會 (Open Data 彙整)
    report += "\n🎙️ 【今日法說會資訊】\n"
    try:
        # 證交所法說會公告
        url_conf = "https://openapi.twse.com.tw/v1/mops/t100sb02_1"
        res_conf = requests.get(url_conf, timeout=20)
        conf_data = res_conf.json()
        
        found_conf = []
        for item in conf_data:
            # 比對西元日期或帶斜線的日期
            m_date = str(item.get('MeetDate', '')).replace('/', '')
            if m_date == today_std:
                found_conf.append(f"• {item.get('Code')} {item.get('Name')}")
        
        if found_conf:
            report += "\n".join(list(set(found_conf)))
        else:
            report += "  (今日官方暫無登記法說)"
    except:
        report += "  (法說會資料連線異常)"
        
    return report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    content = get_report()
    date_head = datetime.datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 台股數據中心 ({date_head})\n\n{content}")
