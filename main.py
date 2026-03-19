import os
import requests
import re
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_disposition_final_fix():
    """強制過濾與去重邏輯"""
    url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        data = res.json().get('data', [])
        
        # 建立一個以『代號』為 key 的字典，強制去重
        result_map = {}
        
        for row in data:
            # 遍歷這一行的所有欄位，找出長度為 4 的數字(代號)和包含 115/ 的日期
            code = ""
            name = ""
            date_range = ""
            
            for cell in row:
                cell_str = str(cell).strip()
                # 判斷是否為 4 位數字代號 (例如 6715)
                if re.fullmatch(r'\d{4}', cell_str):
                    code = cell_str
                # 判斷是否為中文名稱 (通常長度 2-6 且非數字)
                elif 2 <= len(cell_str) <= 8 and not any(c.isdigit() for c in cell_str):
                    name = cell_str
                # 判斷是否包含起訖日期 (例如 115/03/17)
                elif '115/' in cell_str:
                    date_range = cell_str
            
            if code:
                # 存入字典。如果 6715 再次出現，會直接覆蓋，保證唯一性
                result_map[code] = {
                    "name": name if name else "名稱讀取中",
                    "date": date_range if date_range else "日期未標註"
                }
        
        if not result_map:
            return "🚫 【今日處置股名單】\n  (目前無資料)\n"
            
        report = "🚫 【今日處置股名單】\n"
        # 按照代號排序輸出
        for c in sorted(result_map.keys()):
            info = result_map[c]
            report += f"• {c} {info['name']}\n  ⏳ {info['date']}\n"
        return report + "\n"
    except:
        return "🚫 【處置股】資料讀取失敗\n\n"

def get_investor_conf_final():
    """法說會：改用最暴力的 Yahoo 財經名單抓取"""
    report = "🎙️ 【今日法說會資訊】\n"
    try:
        # 直接抓取彙整頁面
        url = "https://tw.stock.yahoo.com/calendar/conference"
        res = requests.get(url, timeout=15)
        # 用正則表達式直接從 HTML 原始碼中撈出 (股票代號)
        # 這是為了避開網頁標籤被封鎖的問題
        matches = re.findall(r'[\u4e00-\u9fa5]+\(\d{4}\)', res.text)
        
        found = sorted(list(set(matches))) # 去重並排序
        if not found:
            return report + "  (今日暫無公開法說)\n"
        return report + "\n".join([f"• {m}" for m in found[:15]])
    except:
        return report + "  (連線異常)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    content = get_disposition_final_fix() + get_investor_conf_final()
    now_str = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股報表】 {now_str}\n\n{content}")
