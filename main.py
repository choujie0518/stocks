import os
import requests
import pandas as pd
from datetime import datetime

# --- 1. 從 GitHub Secrets 讀取金鑰 ---
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    """發送推播至 LINE 官方帳號"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        return res.status_code
    except Exception as e:
        print(f"LINE 發送異常: {e}")
        return 500

def get_notice_and_disposition():
    """抓取證交所注意及處置股 (強化偽裝版)"""
    # 模擬真實瀏覽器的 Headers，減少被證交所封鎖的機率
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.twse.com.tw/zh/page/announcement/notice.html'
    }
    
    # 增加時間戳記防止快取
    ts = str(int(datetime.now().timestamp()))
    notice_url = f"https://www.twse.com.tw/zh/api/noticeData?response=json&_={ts}"
    punish_url = f"https://www.twse.com.tw/zh/api/punishData?response=json&_={ts}"
    
    msg = "⚠️ 【注意/處置股清單】\n"
    
    try:
        # 抓取注意股
        res_n_raw = requests.get(notice_url, headers=headers, timeout=20)
        if res_n_raw.status_code == 200:
            try:
                res_n = res_n_raw.json()
                if res_n.get('stat') == 'OK' and res_n.get('data'):
                    msg += "📍注意股:\n"
                    for i in res_n['data'][:12]:
                        msg +=
