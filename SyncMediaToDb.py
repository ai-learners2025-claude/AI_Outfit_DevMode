import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "APP.settings")
django.setup()

from django.conf import settings
from linebot_app.models import ClosetItem

def sync_media_db():
    media_root = settings.MEDIA_ROOT
    base_folder = os.path.join(media_root, 'closet')

    # 資料庫中所有圖片路徑
    db_paths = set(ClosetItem.objects.values_list('image', flat=True))

    # 實體檔案掃描
    media_files = set()
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, media_root).replace('\\', '/')
            media_files.add(rel_path)

    # 找出實體檔案有但資料庫沒有的
    new_files = media_files - db_paths
    # 找出資料庫有但實體檔案沒有的
    missing_files = db_paths - media_files

    # 1. 補新增的圖片到資料庫
    for path in new_files:
        # 從路徑取出 user_id 與 category
        parts = path.split('/')
        if len(parts) >= 3:
            _, user_id, category, filename = parts[0], parts[1], parts[2], parts[-1]
            try:
                ClosetItem.objects.create(
                    user_id=user_id,
                    category=category,
                    image=path
                )
                print(f"✅ 已新增至資料庫: {path}")
            except Exception as e:
                print(f"❌ 新增失敗 {path}: {e}")
        else:
            print(f"⚠ 無法解析路徑: {path}")

    # 2. 刪除資料庫中多餘的紀錄
    deleted_count, _ = ClosetItem.objects.filter(image__in=missing_files).delete()
    for path in missing_files:
        print(f"🗑 已刪除資料庫紀錄: {path}")

    # 結果輸出
    if new_files or missing_files:
        print(f"\n同步完成：新增 {len(new_files)} 筆，刪除 {deleted_count} 筆。")
    else:
        print("✅ 資料庫與實體檔案完全同步，無需處理。")

if __name__ == '__main__':
    sync_media_db()
