# ✅ 本地端 Streamlit 應用程式
# ✅ 功能：
# 1. 使用 FashionCLIP 模型，根據敘述推薦 closet 中每個類別最相似的 top3 服飾圖片(以文搜圖)
# 2. 顯示在 Streamlit 介面，支援 retry/延遲

import os
import time
import requests
import base64
import pandas as pd
import re
import numpy as np
from PIL import Image
from fashion_clip.fashion_clip import FashionCLIP
from sklearn.metrics.pairwise import cosine_similarity

# # ✅ 設定常數與資料夾位置
# TARGET_FOLDER = "./target"  # 放全身穿搭圖
# CLOSET_FOLDER = "./closet"  # 各部位圖片資料夾：outerwear, tops, pants, skirts, dresses, shoes
# OUTPUT_CSV = "./target/descriptions_prompt7_test.csv"



# ✅ 定義函式：用 FashionCLIP 計算敘述與圖片的相似度，取 top3
# ✅ 自訂 cosine similarity 函數
def cosine_similarity(a, b):
    a = a / np.linalg.norm(a, axis=-1, keepdims=True)
    b = b / np.linalg.norm(b, axis=-1, keepdims=True)
    return np.dot(a, b.T)

def recommend_top3(desc_text, category_folder):
    # ✅ 載入 FashionCLIP 模型
    fclip = FashionCLIP("fashion-clip")
    text_emb = fclip.encode_text([desc_text], batch_size=1)
    image_paths = [os.path.join(category_folder, f)
                   for f in os.listdir(category_folder)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    img_embs = fclip.encode_images(image_paths, batch_size=4)  # 可一次 encode 多張
    sims = cosine_similarity(img_embs, text_emb)[..., 0]
    scores = list(zip(image_paths, sims))
    top3 = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
    return top3

def generate_top3_Json(userId,image_path,image_name):
    
    target_path = image_path
    df = pd.read_csv(os.path.join(image_path, "descriptions.csv"))
    desc_row = df[df['filename'] == image_name]
    desc = desc_row['description'].values[0] if not desc_row.empty else "[無對應描述]"

    # 安全地嘗試擷取 <Output 2> 後方的敘述
    try:
        output_2_desc = desc.split("### <Output 2>")[-1].strip()
        if not output_2_desc or output_2_desc.startswith("###"):
            raise ValueError
    except Exception:
        output_2_desc = ""

    # 類別對應表（英文id: 中文名, id）
    sections = {
        "outerwear": {"name": "外套", "id": "outwear", "marker": "【Outerwear】: "},
        "tops": {"name": "上衣", "id": "top", "marker": "【Top】: "},
        "pants": {"name": "褲子", "id": "bottoms", "marker": "【Pants】: "},
        "skirts": {"name": "裙子", "id": "skirt", "marker": "【Skirt】: "},
        "dresses": {"name": "洋裝", "id": "dress", "marker": "【Dress】: "},
        "shoes": {"name": "鞋子", "id": "shoes", "marker": "【Shoes】: "}
    }

    categories = []

    if output_2_desc:
        format_error_flag = False
        for cat, info in sections.items():
            if info["marker"] not in output_2_desc:
                format_error_flag = True
                break
        if format_error_flag:
            return {"status": "fail", "msg": "格式錯誤，請選擇其他圖片或重新上傳。"}
        for cat, info in sections.items():
            marker = info["marker"]
            if marker in output_2_desc:
                try:
                    part = output_2_desc.split(marker)[1].split("【")[0].strip()
                    if part in ["None", "", "None, None, None, None, None"]:
                        continue
                    closet_path = os.path.join(f"./media/closet/{userId}", cat)
                    if not os.path.exists(closet_path):
                        continue
                    top3 = recommend_top3(part, closet_path)
                    images = [os.path.join(f"/media/closet/{userId}", cat, os.path.basename(p[0])) for p in top3]
                    scores = [round(float(p[1]), 2) for p in top3]
                    categories.append({
                        "name": info["name"],
                        "id": info["id"],
                        "images": images,
                        "scores": scores
                    })
                except Exception as e:
                    continue
        return {"status": "success", "categories": categories}
    else:
        return {"status": "fail", "msg": "此圖片無法解析，請選擇其他圖片或重新上傳。"}

if __name__ == "__main__":
    # ✅ 測試用的圖片路徑與名稱
    userId = "dev_test_user_12345"
    image_path = "./media/mimic/dev_test_user_12345"
    image_name = "7.jpg"

    # ✅ 生成推薦結果
    print(generate_top3_Json(userId, image_path, image_name))

