import os
import requests
import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_stock_name(code):
    """直接呼叫證交所基本資料 API，保證代號轉名稱正確"""
    try:
        # 使用證交所 Open Data，這對自動化程式最友善
        url = f"https://openapi.twse.com.tw/v1/openapi/basic/t187ap03_L?stock_id={code}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if data and len(data) > 0:
            return data[0].get('Abbreviation', '未知')
    except:
        pass
    return "查詢中"

def get_report():
    # 1. 抓取處置股
    dis_report = "🚫 【今日處置股名單】\n"
    try:
        res = requests.get("https://www.twse.com.tw/rwd/zh/announcement/punish?response=json", timeout=15)
        raw_data = res.json().get('data', [])
        
        unique_stocks = {}
        for row in raw_data:
            code = str(row[1]).strip()
            # 只要代號，名稱我們自己去另一個 API 查，確保不被「第一次處置」誤導
            if code not in unique_stocks:
                name = get_stock_name(code)
                unique_stocks[code] = f"• {code} {name}\n  ⏳ {row[0]}"
        
        if not unique_stocks:
            dis_report += "  (今日暫無處置標的)\n"
        else:
            dis_report += "\n".join([unique_stocks[k] for k in sorted(unique_stocks.keys())])
    except:
        dis_report += "  (處置股連線異常)\n"

    # 2. 抓取法說會 (改用證交所法說會公告 API)
    con_report = "\n\n🎙️ 【今日法說會資訊】\n"
    try:
        # 這是證交所官方法說會公告源
        url = "https://openapi.twse.com.tw/v1/mops/t100sb02_1"
        res = requests.get(url, timeout=15)
        today = datetime.datetime.now().strftime("%Y%m%d")
        
        found = []
        for item in res.json():
            # 匹配今天日期的公告
            if item.get('MeetDate') == today:
                found.append(f"• {item.get('Code')} {item.get('Name')}")
        
        if not found:
            con_report += "  (今日官方暫無登記法說)\n"
        else:
            con_report += "\n".join(list(set(found)))
    except:
        con_report += "  (法說會資料讀取失敗)\n"
        
    return dis_report + con_report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    content = get_report()
    date_str = datetime.datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股偵測終極報表】{date_str}\n\n{content}")
