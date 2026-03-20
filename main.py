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

    # 1. 處置股：抓取證交所公告表格
    try:
        driver.get("https://www.twse.com.tw/zh/announcement/punish.html")
        # 等待表格出現
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#reports table")))
        time.sleep(3)
        
        report += "🚫 【今日處置股名單】\n"
        rows = driver.find_elements(By.CSS_SELECTOR, "#reports table tbody tr")
        
        seen_items = set()
        count = 0
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 4:
                date = cols[0].text.strip()
                code = cols[1].text.strip()
                name = cols[2].text.strip()
                period = cols[3].text.strip()
                
                # 唯一標籤：代號+起訖日期，防止重複
                identity = f"{code}_{period}"
                if identity not in seen_items:
                    report += f"• {code} {name}\n  ⏳ {period}\n"
                    seen_items.add(identity)
                    count += 1
        
        if count == 0: report += "  (目前查無生效中處置標的)\n"
    except Exception as e:
        report += "❌ 處置股連線異常 (TWSE)\n"

    # 2. 法說會：直接抓證交所法人說明會公告
    try:
        # 這是證交所官網的法說會公告頁
        driver.get("https://www.twse.com.tw/zh/education/corporate-day/list.html")
        time.sleep(5)
        
        report += "\n🎙️ 【今日法說會資訊】\n"
        # 抓取表格內的公司名稱
        con_rows = driver.find_elements(By.CSS_SELECTOR, ".list-table tbody tr")
        
        found_con = []
        today_str = datetime.now().strftime("%Y/%m/%d") # 格式如 2026/03/20
        
        for r in con_rows:
            c = r.find_elements(By.TAG_NAME, "td")
            if len(c) >= 3:
                meeting_date = c[0].text.strip()
                company_info = c[1].text.strip() # 格式通常是 "公司名(代號)"
                if meeting_date == today_str:
                    found_con.append(company_info)
        
        if found_con:
            for item in sorted(list(set(found_con))):
                report += f"• {item}\n"
        else:
            report += "  (今日暫無官方登記法說)\n"
    except:
        report += "  (法說會資料暫時無法讀取)\n"

    driver.quit()
    return report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    final_content = scrape_data()
    now_date = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 台股官網同步報表 ({now_date})\n\n{final_content}")
