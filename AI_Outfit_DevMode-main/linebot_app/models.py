from django.db import models


# closet：
# 上傳的檔案會放到 MEDIA_ROOT/closet/使用者ID/分類名稱/檔名 的路徑下
def user_directory_closet_path(instance, filename):
    return f'closet/{instance.user_id}/{instance.category}/{filename}'


class ClosetItem(models.Model):
    user_id = models.CharField(max_length=64)
    category = models.CharField(max_length=32, blank=True, null=True)
    image = models.ImageField(upload_to=user_directory_closet_path)  # ImageField 自帶一個 url 屬性，它會根據 Django 設定的 MEDIA_URL 拼出完整 URL
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user_id} - {self.category} - {self.image.name}'


# mimic：
def user_directory_mimic_path(instance, filename):
    return f'mimic/{instance.user_id}/{filename}'


class MimicItem(models.Model):
    user_id = models.CharField(max_length=64)
    image = models.ImageField(upload_to=user_directory_mimic_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user_id} - {self.image.name}'
