# linebot_app/urls.py
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('upload_closet/', views.upload_closet, name='upload_closet'),
    path('delete_closet_images/', views.delete_closet_images, name='delete_closet_images'),
    path('edit_closet_image_category/', views.edit_closet_image_category, name='edit_closet_image_category'),
    path('delete_mimic_images/', views.delete_mimic_images, name='delete_mimic_images'),
    path('upload_mimic/', views.upload_mimic, name='upload_mimic'),
    path('view_images/<str:user_id>/<str:source>/', views.view_images, name='view_images'),
    path('get_search_results/', views.get_search_results, name='get_search_results'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # 可以讓media的圖片產生網址