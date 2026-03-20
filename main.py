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
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_data():
    driver = get_driver()
    report = ""

    # 1. 處置股：使用 Dictionary 確保「代號」唯一
    try:
        driver.get("https://www.twse.com.tw/zh/announcement/punish.html")
        time.sleep(5)
        
        dis_dict = {} # 用 dict 來去重
        rows = driver.find_elements(By.CSS_SELECTOR, "#reports table tr")
        
        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 4:
                code = cols[1].text.strip()
                name = cols[2].text.strip()
                # 只保留該代號最新的一筆資訊
                if code not in dis_dict:
                    dis_dict[code] = f"• {code} {name}"
        
        report += "🚫 【今日處置股名單】\n"
        if dis_dict:
            # 按代號排序輸出
            for code in sorted(dis_dict.keys()):
                report += f"{dis_dict[code]}\n"
        else:
            report += "  (目前網頁查無處置標的)\n"
    except Exception as e:
        report += "❌ 處置股抓取失敗\n"

    # 2. 法說會：改用更精準的 CSS 選擇器並抓取所有文字
    try:
        driver.get("https://tw.stock.yahoo.com/calendar/conference")
        time.sleep(5)
        
        report += "\n🎙️ 【今日法說會資訊】\n"
        # Yahoo 股市的法說會通常在特定表格或清單中
        con_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '(') and contains(text(), ')')]")
        
        unique_con = set()
        for elem in con_elements:
            txt = elem.text.strip()
            # 過濾掉太長的句子，只抓公司名(代號)格式
            if 4 <= len(txt) <= 20 and "(" in txt:
                unique_con.add(txt)
        
        if unique_con:
            for item in sorted(list(unique_con)):
                report += f"• {item}\n"
        else:
            report += "  (今日暫無或尚未更新)\n"
    except Exception as e:
        report += "❌ 法說會連線異常\n"

    driver.quit()
    return report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    final_msg = scrape_data()
    now = datetime.now().strftime('%Y/%m/%d')
    send_line(f"🚀 台股精準報表 ({now})\n\n{final_msg}")
