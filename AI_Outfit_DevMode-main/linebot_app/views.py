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
import time


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



#from libraries.description_utils import generate_description_from_image_path, save_description_to_csv, load_prompt
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
        deleted_filenames = []

        for item in items:
            if item.image and os.path.exists(item.image.path):
                deleted_filenames.append(os.path.basename(item.image.path))
                os.remove(item.image.path)
            item.delete()
            deleted_count += 1

        # descriptions.csv 處理（透過 csv 模組安全過濾）
        csv_path = os.path.join(settings.MEDIA_ROOT, f'mimic/{user_id}/descriptions.csv')
        if os.path.exists(csv_path):
            rows_to_keep = []
            with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['filename'] not in deleted_filenames:
                        rows_to_keep.append(row)

            # 寫回檔案
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['filename', 'description'])
                writer.writeheader()
                writer.writerows(rows_to_keep)

        return JsonResponse({"status": "success", "deleted_count": deleted_count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def upload_mimic(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    user_id = request.POST.get('userId')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'userId缺失'}, status=400)

    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'status': 'error', 'message': '沒有上傳圖片'}, status=400)

    saved_items = []

    def get_next_serial_folder(base_dir):
        i = 0
        while os.path.exists(os.path.join(base_dir, f"{i:02d}")):
            i += 1
        return os.path.join(base_dir, f"{i:02d}"), f"{i:02d}"

    try:
        mimic_items = []
        for f in files:
            raw_filename = get_valid_filename(f.name)
            image_content = ContentFile(f.read(), name=raw_filename)
            mimic_items.append({
                'instance': MimicItem(user_id=user_id),
                'base_filename': os.path.splitext(raw_filename)[0],
                'raw_filename': raw_filename,
                'image_content': image_content
            })

        for item in mimic_items:
            mimic_item = item['instance']
            base_filename, raw_filename, image_content = item['base_filename'], item['raw_filename'], item['image_content']

            backend_item = MimicBackendItem(user_id=user_id)
            backend_item.save()

            user_base_dir = os.path.join(settings.MEDIA_ROOT, 'Mimic_backend', user_id)
            output_dir, serial_str = get_next_serial_folder(user_base_dir)
            os.makedirs(output_dir, exist_ok=True)

            # 临时保存图片到模型，但不保存到 MEDIA
            mimic_item.image.save(raw_filename, image_content, save=False)

            # 图片处理：重试机制
            processor = RunningHubImageProcessor()
            for attempt in range(3):
                if processor.process_image(image_path=mimic_item.image.path, output_dir=output_dir, base_name=base_filename):
                    break
                elif attempt < 2:
                    print(f"图片处理失败，重试 {attempt + 1}/3...")
                    time.sleep(5)
            else:
                # 图片处理失败，删除临时文件
                if os.path.exists(mimic_item.image.path):
                    os.remove(mimic_item.image.path)
                return JsonResponse({'status': 'error', 'message': '图片处理失败，已达最大重试次数'}, status=500)

            processed_image_path = os.path.join(output_dir, f"{base_filename}_removed_bg.png")
            if not os.path.exists(processed_image_path):
                # 找不到去背图片，删除临时文件
                if os.path.exists(mimic_item.image.path):
                    os.remove(mimic_item.image.path)
                return JsonResponse({'status': 'error', 'message': '找不到去背图片'}, status=500)

            # 生成描述
            try:
                prompt_path = os.path.join(settings.BASE_DIR, 'libraries', 'prompt7_en.txt')
                removed_bg_path = processed_image_path
                original_img_dir = os.path.dirname(mimic_item.image.path)
                csv_path = os.path.join(original_img_dir, 'descriptions.csv')

                # 描述生成与保存
                prompt_text = load_prompt(prompt_path)
                description = generate_description(removed_bg_path, prompt_text)
                backend_item.description = description
                backend_item.save()

                with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['filename', 'description'])
                    if not os.path.exists(csv_path):
                        writer.writeheader()
                    writer.writerow({'filename': os.path.basename(mimic_item.image.path), 'description': description})

            except Exception as desc_err:
                print(f"描述生成错误: {str(desc_err)}")

            saved_items.append({
                'id': backend_item.id,
                'url': mimic_item.image.url,
                'description': backend_item.description if hasattr(backend_item, 'description') else None
            })

        # 图片处理成功后，保存图片到 MEDIA
        for item in mimic_items:
            try:
                mimic_item = item['instance']
                mimic_item.image.save(item['raw_filename'], item['image_content'], save=True)
            except Exception as e:
                print(f"图片保存失败: {str(e)}")
                # 删除临时文件
                if os.path.exists(mimic_item.image.path):
                    os.remove(mimic_item.image.path)
                return JsonResponse({'status': 'error', 'message': '图片保存失败'}, status=500)

        return JsonResponse({'status': 'success', 'new_images': saved_items})

    except Exception as e:
        print(f"处理图片失败: {str(e)}")
        # 删除上传的文件及临时文件
        for item in mimic_items:
            if os.path.exists(item['instance'].image.path):
                os.remove(item['instance'].image.path)
        return JsonResponse({'status': 'error', 'message': f'处理图片失败: {str(e)}'}, status=500)

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
