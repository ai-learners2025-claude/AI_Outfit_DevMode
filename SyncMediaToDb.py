import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "APP.settings")
django.setup()

from django.conf import settings
from linebot_app.models import ClosetItem

def check_media_db_sync():
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

    # 輸出檢查結果
    if new_files or missing_files:
        print("⚠ 發現不同步情況：")
        if new_files:
            print(f"\n資料庫缺少 {len(new_files)} 筆圖片（存在於 media 但無資料庫紀錄）：")
            for path in new_files:
                print(f"  - {path}")
        if missing_files:
            print(f"\n資料庫多出 {len(missing_files)} 筆紀錄（資料庫有但檔案不存在）：")
            for path in missing_files:
                print(f"  - {path}")
        print("\n尚未進行任何修改，請確認後再決定是否要同步。")
    else:
        print("✅ 資料庫與實體檔案完全同步，無需處理。")

if __name__ == '__main__':
    check_media_db_sync()
