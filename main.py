import os
import requests
import pandas as pd
from datetime import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_disposition_data():
    """使用 Pandas 處理資料，強行去重並匹配欄位"""
    api_url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        raw_json = res.json()
        if 'data' not in raw_json: return "🚫 【今日處置股】\n  (今日暫無處置標的)\n"
        
        # 將資料轉成 DataFrame 處理
        df = pd.DataFrame(raw_json['data'])
        
        # 證交所 API 欄位通常是：0:日期, 1:代號, 2:名稱
        # 我們只取這三個欄位，並針對『代號』做去重
        df = df[[0, 1, 2]].drop_duplicates(subset=[1])
        
        report = "🚫 【今日處置股名單】\n"
        for _, row in df.iterrows():
            report += f"• {row[1]} {row[2]}\n  ⏳ {row[0]}\n"
        return report + "\n"
    except:
        return "🚫 【今日處置股】\n  (連線數據異常)\n\n"

def get_investor_conference():
    """改用 XQ 系統的開放接口，這對 GitHub 較友善"""
    report = "🎙️ 【今日法說會資訊】\n"
    try:
        # 這裡是另一個更底層的資訊源
        url = "https://mops.twse.com.tw/mops/web/ajax_t100sb02_1"
        payload = {
            'encodeURIComponent': '1',
            'step': '1',
            'firstin': '1',
            'off': '1',
            'TYPEK': 'all',
            'year': str(datetime.now().year - 1911),
            'month': str(datetime.now().month).zfill(2)
        }
        res = requests.post(url, data=payload, timeout=15)
        
        # 簡單的關鍵字匹配，抓取包含今日日期的行
        today_m = datetime.now().strftime('%m/%d')
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        
        found = []
        for tr in soup.select('tr'):
            text = tr.get_text()
            if today_m in text:
                # 抓取該行中的股票名稱(通常是第2或3個 td)
                tds = tr.find_all('td')
                if len(tds) > 2:
                    found.append(f"• {tds[1].text.strip()} {tds[2].text.strip()}")
        
        if not found:
            return report + "  (今日暫無公開法說)\n"
        return report + "\n".join(set(found)) # 這裡也做去重
    except:
        return report + "  (資料庫讀取中)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    msg = get_disposition_data() + get_investor_conference()
    date_str = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 台股偵測報表 ({date_str})\n\n{msg}")
