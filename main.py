import os
import requests
import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_twse_data():
    report = "🚀 【台股官網同步偵測報表】\n"
    now = datetime.datetime.now()
    today_str = now.strftime("%Y%m%d")
    
    # 1. 處置股：直接抓證交所 Punish 頁面的後台數據
    report += "\n🚫 【生效中處置股名單】\n"
    try:
        # 這是證交所官網表格的真實數據來源
        punish_url = f"https://www.twse.com.tw/zh/announcement/punish.html?response=json&_={int(now.timestamp())}"
        res = requests.get(punish_url, timeout=15)
        data = res.json().get('data', [])
        
        unique_stocks = {}
        for row in data:
            # row[1]:代號, row[2]:名稱, row[3]:處置日期區間
            code, name, period = row[1], row[2], row[3]
            # 格式化顯示 (去掉 HTML 標籤)
            clean_name = name.replace(' ', '')
            if code not in unique_stocks:
                unique_stocks[code] = f"• {code} {clean_name}\n  ⏳ {period}"
        
        if unique_stocks:
            for k in sorted(unique_stocks.keys()):
                report += unique_stocks[k] + "\n"
        else:
            report += "  (目前官網查無標的)\n"
    except:
        report += "  (處置股數據接口連線逾時)\n"

    # 2. 法說會：改抓「公開資訊觀測站」的當日彙整 API
    report += "\n🎙️ 【今日法說會資訊】\n"
    try:
        # 直接抓 Open Data 彙整好的法說會清單
        conf_url = "https://openapi.twse.com.tw/v1/mops/t100sb02_1"
        res_conf = requests.get(conf_url, timeout=15)
        conf_list = res_conf.json()
        
        found = []
        # 證交所 API 的日期格式通常是 2026/03/20
        target_date = now.strftime("%Y/%m/%d")
        for item in conf_list:
            if item.get('MeetDate') == target_date:
                found.append(f"• {item.get('Code')} {item.get('Name')}")
        
        if found:
            report += "\n".join(list(set(found)))
        else:
            report += "  (今日官方公告暫無法說)"
    except:
        report += "  (法說會 API 更新中)"

    return report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    content = get_twse_data()
    send_line(content)
