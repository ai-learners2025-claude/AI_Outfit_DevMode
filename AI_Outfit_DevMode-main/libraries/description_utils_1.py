import os
import requests
import base64
import time
import csv

# === 可調參數 ===
FOLDER_PATH = "C:/Users/brian/Desktop/AI_Outfit/"                    # 圖片資料夾
PROMPT_PATH = "C:/Users/brian/Desktop/AI_Outfit/libraries/prompt_closet.txt"               # prompt 檔案位置
CSV_OUTPUT_PATH = "C:/Users/brian/Desktop/AI_Outfit/description_test_folder/descriptions.csv"  # 輸出 CSV 檔
OPENROUTER_API_KEY = "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"  # 替換為你的金鑰
MODEL_NAME = "qwen/qwen2.5-vl-32b-instruct:free"   #Llava-2-13b-vl-instruct
# === 重試次數與延遲時間 ===
RETRY_LIMIT = 3
DELAY_SECONDS = 20

# === 載入 prompt 文字 ===
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    prompt_text = f.read()

# === 準備儲存結果 ===
records = []

# === 讀取圖片並送出 API 請求 ===
for filename in sorted(os.listdir(FOLDER_PATH)):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    file_path = os.path.join(FOLDER_PATH, filename)
    success = False
    attempts = 0
    result_text = ""

    while not success and attempts < RETRY_LIMIT:
        attempts += 1
        try:
            with open(file_path, "rb") as image_file:
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
                print(f"[✅] {filename} 完成")
                success = True
            else:
                print(f"[⚠️] {filename} 嘗試第 {attempts} 次失敗，HTTP {response.status_code}")
                time.sleep(DELAY_SECONDS)

        except Exception as e:
            print(f"[❌] {filename} 發生錯誤：{e}")
            time.sleep(DELAY_SECONDS)

    records.append({
        "filename": filename,
        "description": result_text
    })

    # === 避免觸發 rate limit ===
    time.sleep(DELAY_SECONDS)

# === 儲存為 CSV ===
with open(CSV_OUTPUT_PATH, "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["filename", "description"])
    writer.writeheader()
    writer.writerows(records)

print(f"\n✅ 所有結果已儲存至 {CSV_OUTPUT_PATH}")
