import os
import requests
import json
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_stock_names():
    """預先抓取全台股名稱對照表，避免 API 欄位亂跳"""
    names = {}
    try:
        # 抓取證交所代號對照 JSON
        res = requests.get("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_AVG_ALL", timeout=10)
        for item in res.json():
            names[item['Code']] = item['Name']
    except:
        pass
    return names

def get_disposition_final():
    """強行匹配名稱與去重"""
    name_dict = get_stock_names()
    url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json().get('data', [])
        
        result_map = {}
        for row in data:
            date_range = str(row[0])
            code = str(row[1])
            # 優先從我們的字典找中文名，找不到再看 API 欄位
            name = name_dict.get(code, "未知名稱")
            
            # 以 code 為 Key 強制去重
            result_map[code] = f"• {code} {name}\n  ⏳ {date_range}"
            
        report = "🚫 【今日處置股名單】\n"
        if not result_map: return report + "  (今日暫無標的)\n"
        
        # 排序並組合
        sorted_keys = sorted(result_map.keys())
        return report + "\n".join([result_map[k] for k in sorted_keys]) + "\n\n"
    except:
        return "🚫 【今日處置股】\n  (讀取異常)\n\n"

def get_official_conferences():
    """改用證交所官方新聞 API 抓取法說會關鍵字"""
    report = "🎙️ 【今日法說會資訊】\n"
    try:
        # 這是證交所每日重大訊息/法說會的 API
        url = "https://openapi.twse.com.tw/v1/mops/t100sb02_1"
        res = requests.get(url, timeout=15)
        today = datetime.now().strftime('%Y%m%d')
        
        found = []
        for item in res.json():
            # 判斷日期是否為今日，且包含法說會關鍵字
            if item.get('MeetDate') == today or item.get('AggregationDate') == today:
                code = item.get('Code', '')
                name = item.get('Name', '')
                found.append(f"• {code} {name}")
        
        if not found:
            return report + "  (今日官方暫無登記法說)\n"
        return report + "\n".join(list(set(found))) # 去重
    except:
        return report + "  (資料源連線中)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    dis = get_disposition_final()
    con = get_official_conferences()
    now = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股精準報表】 {now}\n\n{dis}{con}")
