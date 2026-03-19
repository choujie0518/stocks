import os
import requests
import pandas as pd
from datetime import datetime
import io

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_disposition_data():
    """直接從證交所網頁表格抓取，這份資料最完整，不會漏掉任何一支"""
    url = "https://www.twse.com.tw/zh/announcement/punish.html" # 網頁版，比 API 豐富
    api_url = "https://www.twse.com.tw/rwd/zh/announcement/punish?response=html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    try:
        res = requests.get(api_url, headers=headers, timeout=15)
        # 用 pandas 直接硬刷表格內容
        dfs = pd.read_html(io.StringIO(res.text))
        if not dfs: return "🚫 【今日處置股】\n  (今日暫無標的)\n"
        
        df = dfs[0]
        # 證交所表格通常為：0:公佈日期, 1:證券代號, 2:證券名稱, 3:處置起訖日期...
        # 我們只取 1, 2, 3 欄位
        report = "🚫 【完整處置股清單】\n"
        
        # 強制去重：有些股票會重複公佈，我們以「代號+起訖日期」來確保唯一
        df = df.drop_duplicates(subset=[df.columns[1], df.columns[3]])
        
        for _, row in df.iterrows():
            code = str(row.iloc[1])
            name = str(row.iloc[2])
            period = str(row.iloc[3])
            report += f"• {code} {name}\n  ⏳ {period}\n"
        return report + "\n"
    except Exception as e:
        return f"🚫 【處置股】抓取異常: {str(e)}\n\n"

def get_conference_data():
    """改用對 GitHub 環境最友善的數據源"""
    report = "🎙️ 【今日法說會資訊】\n"
    try:
        # 換成這組 API，這是專門提供給金融看盤軟體的，比較不會擋 IP
        url = "https://openapi.twse.com.tw/v1/mops/t100sb02_1"
        res = requests.get(url, timeout=15)
        data = res.json()
        
        # 取得今天日期 (民國格式，因為 API 裡面多用民國)
        today_roc = f"{datetime.now().year - 1911}{datetime.now().strftime('%m%d')}"
        today_std = datetime.now().strftime("%Y%m%d")
        
        found = []
        for item in data:
            m_date = str(item.get('MeetDate', '')).replace('/', '')
            if m_date == today_roc or m_date == today_std:
                found.append(f"• {item.get('Code')} {item.get('Name')}")
        
        if not found:
            return report + "  (今日暫無官方登記法說)\n"
        return report + "\n".join(list(set(found)))
    except:
        return report + "  (資料庫連線中)\n"

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    full_report = get_disposition_data() + get_conference_data()
    now_str = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 台股全效報表 ({now_str})\n\n{full_report}")
