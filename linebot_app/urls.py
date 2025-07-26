# linebot_app/urls.py
from django.urls import path
from .views import upload_closet, view_closet
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('upload_closet/', upload_closet, name='upload_closet'),
    path('delete_closet_images/', views.delete_closet_images, name='delete_closet_images'),
    path('edit_closet_image_category/', views.edit_closet_image_category, name='edit_closet_image_category'),
    path('view_closet/<str:user_id>/', view_closet, name='view_closet'),
    # path('linebot/view_closet/<str:user_id>/', view_closet, name='view_closet'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # 可以讓media的圖片產生網址