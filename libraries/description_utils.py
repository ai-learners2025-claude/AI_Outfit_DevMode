# libraries/description_utils.py

import os
import base64
import requests
import time
import csv

from dotenv import load_dotenv
load_dotenv()

OPENROUTER_API_KEY = "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"
DEFAULT_MODEL = "qwen/qwen2.5-vl-32b-instruct:free"
RETRY_LIMIT = 3
DELAY_SECONDS = 20

def load_prompt(prompt_path: str) -> str:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_description_from_image_path(image_path: str, prompt_text: str, model=DEFAULT_MODEL) -> str:
    """
    給定圖片路徑與 prompt，回傳描述文字。
    """
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    }

    for attempt in range(RETRY_LIMIT):
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                print(f"[WARNING] 嘗試第 {attempt+1} 次失敗：HTTP {response.status_code}")
                time.sleep(DELAY_SECONDS)
        except Exception as e:
            print(f"[ERROR] 發生錯誤：{e}")
            time.sleep(DELAY_SECONDS)

    return ""

def save_description_to_csv(csv_path, filename, description):
    """
    將單筆資料寫入 CSV。如果檔案不存在，會自動建立表頭。
    """
    first_write = not os.path.exists(csv_path) or os.stat(csv_path).st_size == 0
    with open(csv_path, "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if first_write:
            writer.writerow(["filename", "description"])
        writer.writerow([filename, description])
