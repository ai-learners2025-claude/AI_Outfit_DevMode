from django.shortcuts import render

# Create your views here.

import os
os.environ["PYMATTING_NO_CACHE"] = "1"
import io
from PIL import Image

from rembg import remove
from django.core.files.base import ContentFile

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from django.core.files.uploadedfile import InMemoryUploadedFile


from django.conf import settings
from django.shortcuts import render
from .models import ClosetItem, MimicItem,MimicBackendItem
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename


from pathlib import Path
import json

from io import BytesIO 

import logging

# 20250729 
from libraries.rembg_utils import remove_background
from urllib.parse import urlparse
from libraries.E1_text_image_en_avoid_crash_utils import generate_top3_Json



from libraries.description_utils import generate_description_from_image_path, save_description_to_csv, load_prompt
from libraries.description_utils_new import generate_description, load_prompt, save_description_to_csv
from libraries.runninghub_utils import RunningHubImageProcessor
import csv


# 將以下設定寫入 settings.py 中
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "cMmRHEkKdOaJWv9LdQk1RIedv5DX3qKpg8O7SIXqiIi3yp0jcdXy6xJtlM7eBqV0HigKhWoWkKb85hArSFwalPguOoig6KwqCI7dYasf/hUxOEMVugV/snhSltG1msJ6bcE1kl61lSOqE1/wiV8XOQdB04t89/1O/w1cDnyilFU=")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "93ec1dfd2a32b6c2819eda90cc28d485")

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

@csrf_exempt
def callback(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request")

    signature = request.headers.get('X-Line-Signature')
    body = request.body.decode('utf-8')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return HttpResponseBadRequest("Invalid signature")

    return HttpResponse("OK")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text

    if user_msg == "衣櫃":
        reply = "點擊進入衣櫃： https://你的LIFF網址/liff/closet/"
    elif user_msg == "穿搭":
        reply = "模仿穿搭： https://你的LIFF網址/liff/mimic/"
    elif user_msg == "推薦":
        reply = "推薦結果： https://你的LIFF網址/liff/recommend/"
    else:
        reply = "請點選選單或輸入：衣櫃 / 穿搭 / 推薦"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


@csrf_exempt
def view_images(request, user_id, source):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

    def is_image(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        return ext in image_extensions

    if source == 'closet':
        items = ClosetItem.objects.filter(user_id=user_id)
        images = [{
            'id': item.id,
            'url': item.image.url,
            'category': item.category
        } for item in items if is_image(item.image.name)]
    elif source == 'mimic':
        items = MimicItem.objects.filter(user_id=user_id).order_by('-id')
        images = [{
            'id': item.id,
            'url': item.image.url,
        } for item in items if is_image(item.image.name)]
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid source'}, status=400)

    return JsonResponse({'status': 'success', 'images': images})


#  upload+去背API
@csrf_exempt
def upload_closet(request):
    if request.method == 'POST':
        user_id = request.POST.get('userId')
        category = request.POST.get('category')
        files = request.FILES.getlist('images')

        saved = []

        if not user_id or not category or not files:
            return JsonResponse({'status': 'error', 'message': '缺少參數'}, status=400)

        for f in files:
            try:
                image = Image.open(f)
                image = image.convert("RGBA")

                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()

                # 20250729 用 lib 處理圖片去背
                # output_bytes = remove(img_bytes)
                output_bytes = remove_background(img_bytes)
                output_image = Image.open(io.BytesIO(output_bytes))

                output_stream = io.BytesIO()
                output_image.save(output_stream, format='PNG')
                output_stream.seek(0)

                filename_wo_ext = os.path.splitext(f.name)[0]
                bgremoved_filename = f'{filename_wo_ext}_bgremoved.png'

                image_content = ContentFile(output_stream.read(), name=bgremoved_filename)

                item = ClosetItem(user_id=user_id, category=category, image=image_content)
                item.save()

                saved.append({
                    'id': item.id,                # 新增 id
                    'url': item.image.url,
                    'category': item.category
                })

                # # 20250729 圖檔文字描述
                # prompt_path = os.path.join(settings.BASE_DIR, 'libraries', 'prompt7_en.txt')#'prompt_closet.txt')
                # prompt_text = load_prompt(prompt_path)
                # bgremoved_filename = os.path.join(settings.MEDIA_ROOT, item.image.name)
                # bgremoved_filename = bgremoved_filename.replace('\\', '/')  # 確保路徑格式正確
                # print(f"Processing image: {bgremoved_filename}")
                # description = generate_description_from_image_path(bgremoved_filename, prompt_text)
                # print(f"Generated description: {description}")

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'處理圖片失敗: {str(e)}'}, status=500)

        return JsonResponse({'status': 'success', 'new_images': saved})  # key 改成 new_images
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def delete_closet_images(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '只接受 POST 請求'})
    try:
        data = json.loads(request.body)
        user_id = data.get('userId')
        image_ids = data.get('imageIds', [])

        if not user_id or not image_ids:
            return JsonResponse({'status': 'error', 'message': '缺少必要參數'})

        items = ClosetItem.objects.filter(user_id=user_id, id__in=image_ids)
        deleted_count = 0
        for item in items:
            if item.image and os.path.exists(item.image.path):
                os.remove(item.image.path)
            item.delete()
            deleted_count += 1

        return JsonResponse({"status": "success", "deleted_count": deleted_count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@csrf_exempt
def edit_closet_image_category(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '只接受 POST 請求'})

    try:
        # 解析請求中的 JSON 數據
        data = json.loads(request.body)
        user_id = data.get('userId')
        image_id = data.get('imageId')
        new_category = data.get('newCategory')
        new_imageURL = data.get('newURL')

        print(f"收到請求: user_id={user_id}, image_id={image_id}, new_category={new_category}")  # 日誌輸出

        if not user_id or not image_id or not new_category:
            return JsonResponse({'status': 'error', 'message': '缺少必要參數'})

        # 查詢圖片
        item = ClosetItem.objects.filter(user_id=user_id, id=image_id).first()
        if not item:
            return JsonResponse({'status': 'error', 'message': '找不到指定圖片'})

        # 更新圖片分類
        old_category = item.category
        item.category = new_category

        # 下載新的圖片並更新
        if new_imageURL:
            response = requests.get(new_imageURL)
            if response.status_code == 200:
                # 生成唯一的圖片名稱，避免覆蓋舊圖片
                timestamp = str(int(time.time()))  # 使用時間戳來保證唯一性
                random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))  # 隨機字符串
                new_image_name = f"{item.user_id}_{item.category}_{timestamp}_{random_str}.jpg"  # 生成唯一名稱

                # 儲存新的圖片檔案
                item.image.save(new_image_name, ContentFile(response.content), save=True)

                # 更新圖片名稱，這樣它將會有新的 URL
                item.image.name = f'closet/{item.user_id}/{new_category}/{new_image_name}'

            else:
                return JsonResponse({'status': 'error', 'message': '無法下載新的圖片'})

        item.save()

        # 獲取更新後的圖片 URL
        new_image_url = item.image.url if item.image else None

        return JsonResponse({'status': 'success', 'newImageUrl': new_image_url})  # 返回新的圖片 URL

    except Exception as e:
        print(f"錯誤: {str(e)}")  # 日誌輸出
        return JsonResponse({'status': 'error', 'message': str(e)})

# {
#   "userId": "使用者ID",
#   "imageId": 123,
#   "newCategory": "新分類",
#   "newURL": "新的圖片網址"  // 這是可選參數，可以不帶
# }

# mimic：
    

@csrf_exempt
def delete_mimic_images(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '只接受 POST 請求'})
    try:
        data = json.loads(request.body)
        user_id = data.get('userId')
        image_ids = data.get('imageIds', [])

        if not user_id or not image_ids:
            return JsonResponse({'status': 'error', 'message': '缺少必要參數'})

        items = MimicItem.objects.filter(user_id=user_id, id__in=image_ids)
        deleted_count = 0
        for item in items:
            if item.image and os.path.exists(item.image.path):
                os.remove(item.image.path)
            item.delete()
            deleted_count += 1

        return JsonResponse({"status": "success", "deleted_count": deleted_count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# @csrf_exempt
# def upload_mimic(request):
#     if request.method == 'POST':
#         user_id = request.POST.get('userId')  # key 要和前端 formData 裡的一致，這邊是 'userId'

#         files = request.FILES.getlist('images')  # 多張圖片用 getlist
#         if not files:
#             return JsonResponse({'status': 'error', 'message': '沒有上傳圖片'}, status=400)

#         saved_images = []
#         try:
#             for f in files:
#                 image_content = ContentFile(f.read(), name=f.name)
#                 item = MimicItem(user_id=user_id, image=image_content)
#                 item.save()
#                 saved_images.append({
#                     'id': item.id,
#                     'url': item.image.url,
#                 })

#                 # 20250729
#                 # 🔸 取得原始檔名（如 try3.jpg）並轉換為合法檔名
#                 raw_filename = get_valid_filename(f.name)  # try3.jpg
#                 base_filename, _ = os.path.splitext(raw_filename)  # try3

#                 # 🔥 呼叫處理器處理圖片，並傳入 base_filename
#                 processor = RunningHubImageProcessor()
#                 print(f"raw_filename: {f.name}")  # 日誌輸出
#                 print(f"base_filename: {base_filename}")  # 日誌輸出
#                 print(f"Processing image: {item.image.path}")  # 日誌輸出
#                 print(f"Image path: {item.image.path}")  # 日誌輸出
#                 success = processor.process_image(
#                     image_path= item.image.path,  # 🔸 這是原始圖片的路徑
#                     output_dir=os.path.dirname(item.image.path),
#                     base_name=base_filename  # 🔸 這是你要改進 process_image() 支援的參數
#                 )

#                 if not success:
#                     return JsonResponse({'status': 'error', 'message': '圖片處理失敗'})

#                 # 🔎 組出處理後檔案名稱
#                 removed_bg_filename = f"{base_filename}_removed_bg.png"
#                 removed_bg_path = os.path.join(os.path.dirname(item.image.path), removed_bg_filename)

#                 if not os.path.exists(removed_bg_path):
#                     return JsonResponse({'status': 'error', 'message': '找不到處理後圖片'})

                # # 產生描述
                # prompt_path = os.path.join(settings.BASE_DIR, 'libraries', 'prompt7_en.txt')
                # print(f"Prompt path: {prompt_path}")  # 日誌輸出
                # print(f"Removed background image path: {removed_bg_path}")  # 日誌輸
                # prompt_text = load_prompt(prompt_path)
                # description = generate_description(removed_bg_path, prompt_text)
                # print(f"Generated description: {description}")  # 日誌輸出


#             return JsonResponse({'status': 'success', 'new_images': saved_images})

#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': f'處理圖片失敗: {str(e)}'}, status=500)

#     return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def upload_mimic(request):
    if request.method == 'POST':
        user_id = request.POST.get('userId')
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'userId缺失'}, status=400)

        files = request.FILES.getlist('images')
        if not files:
            return JsonResponse({'status': 'error', 'message': '沒有上傳圖片'}, status=400)

        saved_items = []

        def get_next_serial_folder(base_dir):
            i = 0
            while True:
                folder_name = f"{i:02d}"
                folder_path = os.path.join(base_dir, folder_name)
                if not os.path.exists(folder_path):
                    return folder_path, folder_name
                i += 1

        try:
            # 先儲存 mimic items
            mimic_items = []
            for f in files:
                raw_filename = get_valid_filename(f.name)
                image_content = ContentFile(f.read(), name=raw_filename)

                mimic_item = MimicItem(user_id=user_id)
                mimic_item.image.save(raw_filename, image_content, save=True)
                mimic_item.save()

                mimic_items.append({
                    'instance': mimic_item,
                    'base_filename': os.path.splitext(raw_filename)[0],
                    'raw_filename': raw_filename
                })

            # 然後逐一處理
            for item in mimic_items:
                mimic_item = item['instance']
                base_filename = item['base_filename']

                backend_item = MimicBackendItem(user_id=user_id)
                backend_item.save()

                user_base_dir = os.path.join(settings.MEDIA_ROOT, 'Mimic_backend', user_id)
                output_dir, serial_str = get_next_serial_folder(user_base_dir)
                os.makedirs(output_dir, exist_ok=True)

                # 執行圖片處理（如去背）
                processor = RunningHubImageProcessor()
                success = processor.process_image(
                    image_path=mimic_item.image.path,
                    output_dir=output_dir,
                    base_name=base_filename
                )
                if not success:
                    return JsonResponse({'status': 'error', 'message': '圖片處理失敗'})

                # 處理後圖片路徑
                processed_image_filename = f"{base_filename}_removed_bg.png"
                processed_image_path = os.path.join(output_dir, processed_image_filename)

                if not os.path.exists(processed_image_path):
                    return JsonResponse({'status': 'error', 'message': '找不到去背圖片'})

                # 儲存到 backend_item
                with open(processed_image_path, 'rb') as imgf:
                    backend_item.image.save(processed_image_filename, ContentFile(imgf.read()), save=True)

                # ---------- 產生描述 ----------
                try:
                    # 取得 prompt 路徑與圖片路徑
                    prompt_path = os.path.join(settings.BASE_DIR, 'libraries', 'prompt7_en.txt')
                    removed_bg_path = processed_image_path

                    print(f"Prompt path: {prompt_path}")
                    print(f"Removed background image path: {removed_bg_path}")

                    # 取得 CSV 儲存路徑（與原始圖片同資料夾）
                    original_img_dir = os.path.dirname(mimic_item.image.path)
                    csv_path = os.path.join(original_img_dir, 'descriptions.csv')

                    # 檢查是否已有該圖片記錄（使用圖片檔名來比對）
                    image_filename = os.path.basename(mimic_item.image.path)
                    already_exists = False

                    if os.path.exists(csv_path):
                        with open(csv_path, newline='', encoding='utf-8') as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                if row.get('filename') == image_filename:
                                    already_exists = True
                                    break

                    if already_exists:
                        print(f"描述已存在，略過: {image_filename}")
                    else:
                        # 載入 prompt 並產生描述
                        prompt_text = load_prompt(prompt_path)
                        description = generate_description(removed_bg_path, prompt_text)
                        print("已寫入CSV檔案")

                        # 存到 backend_item（如有欄位）
                        backend_item.description = description
                        backend_item.save()

                        # 寫入 CSV，若不存在則建立含標頭
                        file_exists = os.path.exists(csv_path)
                        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                            fieldnames = ['filename', 'description']
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                            if not file_exists:
                                writer.writeheader()

                            writer.writerow({
                                'filename': image_filename,
                                'description': description
                            })

                except Exception as desc_err:
                    print(f"描述產生錯誤: {str(desc_err)}")
                    # 不中斷流程

                saved_items.append({
                    'id': backend_item.id,
                    'url': mimic_item.image.url,
                    'description': backend_item.description if hasattr(backend_item, 'description') else None
                })

            return JsonResponse({'status': 'success', 'new_images': saved_items})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': f'處理圖片失敗: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def get_search_results(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            userId = data.get('userId')
            imageUrl = data.get('imageUrl')

            print(f"Received request: userId={userId}, imageUrl={imageUrl}")  # 日誌輸出
            parsed = urlparse(imageUrl)
            # parsed.scheme == 'http'， parsed.netloc == '127.0.0.1:8000'
            base = f"{parsed.scheme}://{parsed.netloc}"         # → 主機與 port 部分
            path = "."+os.path.dirname(parsed.path)                # → /media/mimic/dev_test_user_12345
            filename = os.path.basename(parsed.path)           # → P-02.png
            print(base, path, filename, sep="\n")  # 日誌輸出

            response = generate_top3_Json(userId, path, filename)

            # 回傳固定假資料
            # response = {
            #     "status": "success",
            #     "categories": [
            #         {
            #             "name": "上衣",
            #             "id": "top",
            #             "images": [
            #                 "/media/closet/dev_test_user_12345/top/PXL_20250727_111210375.MP2_bgremoved.png",
            #                 "/media/closet/dev_test_user_12345/top/PXL_20250727_111236442_bgremoved.png",
            #                 "/media/closet/dev_test_user_12345/top/PXL_20250727_111323404.MP2_bgremoved.png"
            #             ],
            #             "scores": [0.95, 0.90, 0.85]
            #         },
            #         {
            #             "name": "褲子",
            #             "id": "bottoms",
            #             "images": [
            #                 "/media/closet/dev_test_user_12345/bottom/PXL_20250727_110601137.MP2_bgremoved.png",
            #                 "/media/closet/dev_test_user_12345/bottom/PXL_20250727_110635816.MP2_bgremoved.png",
            #                 "/media/closet/dev_test_user_12345/bottom/PXL_20250727_110716262.MP2_bgremoved.png"
            #             ],
            #             "scores": [0.95, 0.90, 0.85]
            #         },
            #         {
            #             "name": "外套",
            #             "id": "outwear",
            #             "images": [
            #                 "/media/closet/dev_test_user_12345/outwear/PXL_20250727_112110655_bgremoved.png",
            #                 "/media/closet/dev_test_user_12345/outwear/PXL_20250727_112135360.MP2_bgremoved.png",
            #                 "/media/closet/dev_test_user_12345/outwear/PXL_20250727_112205412.MP2_bgremoved.png",
            #             ],
            #             "scores": [0.95, 0.90, 0.85]
            #         },
            #         {
            #             "name": "鞋子",
            #             "id": "shoes",
            #             "images": [
            #                 "/media/closet/dev_test_user_12345/shoes/PXL_20250727_113330061_bgremoved.png",
            #                 "/media/closet/dev_test_user_12345/shoes/PXL_20250727_113335027_bgremoved.png",
            #                 "/media/closet/dev_test_user_12345/shoes/PXL_20250727_113506483.MP2_bgremoved.png",
            #             ],
            #             "scores": [0.95, 0.90, 0.85]
            #         }
            #     ]
            # }
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    else:
        return JsonResponse({"status": "error", "message": "只接受 POST 請求"})
