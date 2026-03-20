import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_driver():
    """設定 Headless Chrome 參數"""
    chrome_options = Options()
    chrome_options.add_argument('--headless') # 不開啟視窗
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def scrape_data():
    driver = get_driver()
    report = ""

    # 1. 抓取證交所處置股 (直接看表格)
    try:
        driver.get("https://www.twse.com.tw/zh/announcement/punish.html")
        time.sleep(5) # 等待 JavaScript 載入
        
        report += "🚫 【今日處置股名單】\n"
        rows = driver.find_elements(By.CSS_SELECTOR, "#reports table tr")
        
        found_dis = False
        # 跳過標題列
        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 4:
                code = cols[1].text.strip()
                name = cols[2].text.strip()
                date_range = cols[3].text.strip()
                report += f"• {code} {name}\n  ⏳ {date_range}\n"
                found_dis = True
        
        if not found_dis: report += "  (目前網頁查無處置標的)\n"
    except Exception as e:
        report += f"❌ 處置股抓取失敗: {str(e)}\n"

    # 2. 抓取 Yahoo 股市法說會 (模擬真人瀏覽)
    try:
        driver.get("https://tw.stock.yahoo.com/calendar/conference")
        time.sleep(5)
        
        report += "\n🎙️ 【今日法說會資訊】\n"
        # 抓取 Yahoo 的 StyledTitle 區塊
        items = driver.find_elements(By.CSS_SELECTOR, 'div[class*="StyledTitle"]')
        
        found_con = False
        unique_con = set()
        for item in items:
            t = item.text.strip()
            if t and "(" in t:
                unique_con.add(t)
                found_con = True
        
        if found_con:
            for c in sorted(list(unique_con)):
                report += f"• {c}\n"
        else:
            report += "  (今日暫無公開資訊)\n"
    except Exception as e:
        report += f"❌ 法說會抓取失敗: {str(e)}\n"

    driver.quit()
    return report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    final_report = scrape_data()
    now_str = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 Selenium 自動偵測報表 ({now_str})\n\n{final_report}")
