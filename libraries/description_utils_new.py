import os
import requests
import base64
import time
import csv

# === 可調參數 ===
OPENROUTER_API_KEY = "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"  # 建議改用 .env 管理
MODEL_NAME = "qwen/qwen2.5-vl-32b-instruct:free"
RETRY_LIMIT = 3
DELAY_SECONDS = 20


def load_prompt(prompt_path: str) -> str:
    """
    從指定路徑讀取 prompt 文字
    """
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_description(image_path: str, prompt_text: str) -> str:
    """
    上傳圖片並取得文字描述
    """
    attempts = 0
    result_text = ""

    while attempts < RETRY_LIMIT:
        attempts += 1
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            }

            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

            if response.status_code == 200:
                result_text = response.json()['choices'][0]['message']['content']
                return result_text.strip()
            else:
                print(f"[⚠️] 嘗試第 {attempts} 次失敗，HTTP {response.status_code}")
                time.sleep(DELAY_SECONDS)

        except Exception as e:
            print(f"[❌] 發生錯誤：{e}")
            time.sleep(DELAY_SECONDS)

    return ""


def save_description_to_csv(csv_path: str, filename: str, description: str):
    """
    將單筆資料儲存至 CSV（自動新增欄位）
    """
    first_write = not os.path.exists(csv_path) or os.stat(csv_path).st_size == 0
    with open(csv_path, "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if first_write:
            writer.writerow(["filename", "description"])
        writer.writerow([filename, description])
