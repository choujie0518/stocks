import os
import requests
import datetime

FINMIND_TOKEN = os.getenv("FINMIND_API_TOKEN")
LINE_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def get_finmind_report():
    # 1. 抓取行情資料 (收盤行情最準，因為處置股會被標記在備註)
    # 考慮到 API 更新，我們抓「前一個交易日」到「今天」的資料
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
    
    url = "https://api.finmindtrade.com/api/v4/data"
    
    # --- 處置股偵測邏輯 ---
    dis_report = "🚫 【台股生效中處置股】\n"
    price_params = {
        "dataset": "TaiwanStockPrice",
        "start_date": start_date,
        "end_date": end_date,
        "token": FINMIND_TOKEN
    }
    
    try:
        res = requests.get(url, params=price_params, timeout=20)
        price_data = res.json().get("data", [])
        
        # 用 dict 去重，只抓最新日期的標記
        dis_map = {}
        for item in price_data:
            remark = item.get("remark", "")
            # 只要備註提到處置，就是我們要找的標的
            if "處置" in remark:
                sid = item.get("stock_id")
                # 這裡 FinMind 沒給中文名，我們手動標註或直接顯示代號
                dis_map[sid] = remark
        
        if dis_map:
            for sid, rem in dis_map.items():
                dis_report += f"• {sid}\n  ℹ️ {rem}\n"
        else:
            dis_report += "  (API 行情備註尚未標記處置)\n"
    except:
        dis_report += "  (處置資料連線異常)\n"

    # --- 法說會偵測邏輯 ---
    conf_report = "\n🎙️ 【近期法說會清單】\n"
    conf_params = {
        "dataset": "TaiwanStockConference",
        "start_date": start_date, # 抓最近三天的
        "token": FINMIND_TOKEN
    }
    
    try:
        res_conf = requests.get(url, params=conf_params, timeout=20)
        conf_data = res_conf.json().get("data", [])
        
        if conf_data:
            for c in conf_data:
                conf_report += f"• {c.get('stock_id')} {c.get('stock_name')}\n  📅 日期: {c.get('date')}\n"
        else:
            conf_report += "  (近期無登記法說資訊)\n"
    except:
        conf_report += "  (法說資料連線異常)\n"
        
    return dis_report + conf_report

def send_line(msg):
    if not LINE_TOKEN or not USER_ID: return
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)

if __name__ == "__main__":
    if not FINMIND_TOKEN:
        send_line("❌ 錯誤：未設定 FINMIND_API_TOKEN")
    else:
        content = get_finmind_report()
        date_str = datetime.datetime.now().strftime('%Y/%m/%d')
        send_line(f"🛡️ FinMind 實戰報表 ({date_str})\n\n{content}")
