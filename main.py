import os
import requests
from bs4 import BeautifulSoup
import datetime

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_report():
    # 擬人化 Header，防止被 Yahoo 或證交所封鎖
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # --- 1. 處置股 (不再單純去重，確保列出所有日期) ---
    dis_report = "🚫 【今日處置股名單】\n"
    try:
        res = requests.get("https://www.twse.com.tw/rwd/zh/announcement/punish?response=json", headers=headers, timeout=15)
        raw_data = res.json().get('data', [])
        
        unique_items = []
        seen = set()
        
        for row in raw_data:
            date_info = str(row[0]).strip()
            code = str(row[1]).strip()
            # 找名稱：遍歷欄位，找 2-5 個字且不含「處置」的純中文
            name = "查詢中"
            for cell in row:
                c_str = str(cell).strip()
                if 2 <= len(c_str) <= 5 and not any(char.isdigit() for char in c_str) and "處置" not in c_str:
                    name = c_str
                    break
            
            # 使用「日期+代號」作為唯一標識，避免漏掉同一股票不同時段的處置
            identity = f"{date_info}_{code}"
            if identity not in seen:
                unique_items.append(f"• {code} {name}\n  ⏳ {date_info}")
                seen.add(identity)
        
        dis_report += "\n".join(unique_items) if unique_items else "  (今日暫無處置標的)\n"
    except:
        dis_report += "  (處置股讀取失敗)\n"

    # --- 2. 法說會 (直接從 Yahoo 股市撈取) ---
    con_report = "\n\n🎙️ 【今日法說會資訊】\n"
    try:
        # Yahoo 股市法說會行事曆
        yahoo_url = "https://tw.stock.yahoo.com/calendar/conference"
        res = requests.get(yahoo_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Yahoo 的結構：尋找包含股票代號括號的文字 (例如：台積電(2330))
        found_list = []
        # 抓取頁面中所有看起來像公司名+代號的標籤
        for item in soup.select('div[class*="StyledTableCell"]'):
            text = item.get_text(strip=True)
            if "(" in text and ")" in text and any(char.isdigit() for char in text):
                found_list.append(f"• {text}")
        
        # 去重並保留前 15 筆
        con_report += "\n".join(list(dict.fromkeys(found_list))[:15]) if found_list else "  (今日 Yahoo 暫無公開資訊)\n"
    except:
        con_report += "  (Yahoo 連線受阻)\n"
        
    return dis_report + con_report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    report_content = get_report()
    today_str = datetime.datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 【台股偵測】{today_str}\n\n{report_content}")
