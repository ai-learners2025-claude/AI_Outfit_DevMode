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
from .models import ClosetItem, MimicItem
from django.http import JsonResponse
from django.core.files.storage import default_storage

from pathlib import Path
import json

from io import BytesIO 

import logging


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
    if source == 'closet':
        items = ClosetItem.objects.filter(user_id=user_id)
        images = [{
            'id': item.id,
            'url': item.image.url,
            'category': item.category
        } for item in items]
    elif source == 'mimic':
        items = MimicItem.objects.filter(user_id=user_id).order_by('-id')
        images = [{
            'id': item.id,
            'url': item.image.url,
        } for item in items]
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

                output_bytes = remove(img_bytes)
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
        for item in items:
            if item.image and os.path.exists(item.image.path):
                os.remove(item.image.path)
            item.delete()
            deleted_count += 1

        return JsonResponse({"status": "success", "deleted_count": deleted_count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def upload_mimic(request):
    if request.method == 'POST':
        user_id = request.POST.get('userId')  # key 要和前端 formData 裡的一致，這邊是 'userId'

        files = request.FILES.getlist('images')  # 多張圖片用 getlist
        if not files:
            return JsonResponse({'status': 'error', 'message': '沒有上傳圖片'}, status=400)

        saved_images = []
        try:
            for f in files:
                image_content = ContentFile(f.read(), name=f.name)
                item = MimicItem(user_id=user_id, image=image_content)
                item.save()
                saved_images.append({
                    'id': item.id,
                    'url': item.image.url,
                })

            return JsonResponse({'status': 'success', 'new_images': saved_images})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'處理圖片失敗: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)