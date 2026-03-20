import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_data():
    driver = get_driver()
    report = ""

    # 1. 處置股：解析完整資訊
    try:
        driver.get("https://www.twse.com.tw/zh/announcement/punish.html")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#reports table")))
        time.sleep(3)
        
        report += "🚫 【今日處置股名單】\n"
        rows = driver.find_elements(By.CSS_SELECTOR, "#reports table tbody tr")
        
        count = 0
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 4:
                # 把民國轉西元：115/03/19 -> 2026/03/19
                raw_date = cols[0].text.strip()
                date_parts = raw_date.split('/')
                ad_date = f"{int(date_parts[0])+1911}/{date_parts[1]}/{date_parts[2]}"
                
                code = cols[1].text.strip()
                name = cols[2].text.strip()
                period = cols[3].text.strip() # 這是「處置起訖期間」
                
                report += f"• {code} {name}\n  📅 公告日: {ad_date}\n  ⏳ 區間: {period}\n"
                count += 1
        
        if count == 0: report += "  (目前查無標的)\n"
    except:
        report += "❌ 處置股讀取失敗\n"

    # 2. 法說會：改抓「公開資訊觀測站」的當日彙整，這最準
    try:
        # 這是最硬核的法說會資料源，不需要 UI 渲染
        today_roc = f"{datetime.now().year - 1911}/{datetime.now().strftime('%m/%d')}"
        # 建立一個查詢今天法說會的 Session
        report += "\n🎙️ 【今日法說會資訊】\n"
        
        # 這裡我們換回穩定度最高的 OpenAPI
        res = requests.get("https://openapi.twse.com.tw/v1/mops/t100sb02_1", timeout=15)
        conf_data = res.json()
        
        found = []
        target_date = datetime.now().strftime("%Y%m%d")
        for item in conf_data:
            # 只要日期對得上（移除斜線比對）
            m_date = str(item.get('MeetDate', '')).replace('/', '')
            if m_date == target_date:
                found.append(f"• {item.get('Code')} {item.get('Name')}")
        
        if found:
            report += "\n".join(list(set(found)))
        else:
            report += "  (今日官方暫無登記法說)\n"
    except:
        report += "  (法說會資料連線中)\n"

    driver.quit()
    return report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    final_msg = scrape_data()
    send_line(f"🚀 台股終極完整報表\n\n{final_msg}")
