# rembg_utils.py
# from rembg import new_session, remove

# _MODEL_PATH = "/var/www/.cache/rembg/u2net.onnx"
# _session = None

# def get_session():
#     global _session
#     if _session is None:
#         _session = new_session(model_path=_MODEL_PATH)
#     return _session


# def remove_background(image_bytes: bytes) -> bytes:
#     return remove(image_bytes, session=get_session())
# import os
# import requests

# # REMBG_API_KEY=f5c1020d-0348-494b-9c7f-a9749de9adb4

# def remove_background(image_bytes):
#     api_key = "cb936e7d-50ee-4b7c-9c30-7fdf4c11e60f"

#     if not api_key:
#         raise ValueError("Rembg API Key 未設定。請在 .env 檔中設定 REMBG_API_KEY")

#     response = requests.post(
#         "https://api.rembg.com/remove",
#         files={"image": ("image.png", image_bytes, "image/png")},
#         headers={"Authorization": f"Bearer {api_key}"}
#     )

#     if response.status_code != 200:
#         raise Exception(f"Rembg API 呼叫失敗: {response.status_code} - {response.text}")

#     return response.content


# rembg_utils.py
import os
import requests
from dotenv import load_dotenv

# 載入 .env 設定
load_dotenv()

# 從環境變數讀取 API Key，避免把金鑰寫死在程式碼
# API_KEY = os.getenv("REMBG_API_KEY")
API_KEY = "79d03fc2-c156-4ead-bdba-d592debe9895"
# API_KEY = "8387301b-4c91-44d1-a836-dbe1f5f64209"

def remove_background(image_bytes: bytes) -> bytes:
    """
    呼叫 Rembg API，將輸入圖片去背，回傳 PNG bytes。

    :param image_bytes: 原始圖片的二進位資料 (bytes)
    :return: 去背後的 PNG 圖片 bytes
    :raises Exception: API 呼叫失敗時會丟出錯誤
    """
    if not API_KEY:
        raise ValueError("Rembg API Key 未設定，請在 .env 設定 REMBG_API_KEY")

    url = "https://api.rembg.com/rmbg"
    headers = {"x-api-key": API_KEY}

    response = requests.post(
        url,
        headers=headers,
        files={"image": ("image.png", image_bytes, "image/png")}
    )

    if response.status_code != 200:
        raise Exception(f"Rembg API 呼叫失敗: {response.status_code} - {response.text}")

    return response.content
