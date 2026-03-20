import os
import time
import requests
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

FINMIND_TOKEN = os.getenv("FINMIND_API_TOKEN")
LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 偽裝成真人瀏覽器，避免被封
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def get_report():
    driver = get_driver()
    report = "🚀 【台股精準混合報表】\n"
    
    # --- 1. Selenium 爬取 Yahoo 處置股 (第一優先) ---
    report += "\n🚫 【生效中處置股】\n"
    try:
        # Yahoo 股市處置股頁面通常較穩定
        driver.get("https://tw.stock.yahoo.com/rank/punishment")
        time.sleep(5)
        items = driver.find_elements(By.CSS_SELECTOR, 'li[class*="List(n)"]')
        
        count = 0
        for item in items[:15]: # 抓前 15 筆
            txt = item.text.replace('\n', ' ')
            if txt:
                report += f"• {txt}\n"
                count += 1
        if count == 0: raise Exception("Yahoo 無資料")
    except:
        # 如果 Selenium 失敗，觸發 FinMind 保底
        report += "⚠️ Yahoo 爬取失敗，啟動 FinMind 備援...\n"
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&start_date={(datetime.datetime.now()-datetime.timedelta(days=3)).strftime('%Y-%m-%d')}&token={FINMIND_TOKEN}"
        data = requests.get(url).json().get("data", [])
        dis_list = set([i['stock_id'] for i in data if "處置" in i.get("remark", "")])
        for sid in dis_list:
            report += f"• {sid} (行情備註處置)\n"

    # --- 2. Selenium 爬取 Yahoo 法說會 ---
    report += "\n🎙️ 【近期法說會資訊】\n"
    try:
        driver.get("https://tw.stock.yahoo.com/calendar/conference")
        time.sleep(5)
        # 抓取包含括號代碼的文字塊
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), '(') and contains(text(), ')')]")
        found_con = set()
        for e in elements:
            t = e.text.strip()
            if 4 <= len(t) <= 15: # 過濾出像 "台積電(2330)" 的字樣
                found_con.add(t)
        
        if found_con:
            for c in sorted(list(found_con)): report += f"• {c}\n"
        else:
            report += "  (今日暫無公開法說)\n"
    except:
        report += "  (法說會資料讀取失敗)\n"

    driver.quit()
    return report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    content = get_report()
    send_line(content)
