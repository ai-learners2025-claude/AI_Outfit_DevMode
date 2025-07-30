import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "APP.settings")
django.setup()

from django.conf import settings
from linebot_app.models import ClosetItem, MimicItem, MimicBackendItem

def sync_media_db():
    media_root = settings.MEDIA_ROOT

    sync_targets = [
        {
            'model': ClosetItem,
            'folder': 'closet',
            'parse_path': lambda parts: {
                'user_id': parts[1] if len(parts) > 1 else None,
                'category': parts[2] if len(parts) > 2 else None
            }
        },
        {
            'model': MimicItem,
            'folder': 'mimic',
            'parse_path': lambda parts: {
                'user_id': parts[1] if len(parts) > 1 else None
            }
        },
        {
            'model': MimicBackendItem,
            'folder': 'Mimic_backend',
            'parse_path': lambda parts: {
                'user_id': parts[1] if len(parts) > 1 else None
            }
        }
    ]

    for target in sync_targets:
        model = target['model']
        base_folder = os.path.join(media_root, target['folder'])
        parse_path = target['parse_path']

        db_paths = set(model.objects.values_list('image', flat=True))

        media_files = set()
        for root, dirs, files in os.walk(base_folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, media_root).replace('\\', '/')
                media_files.add(rel_path)

        new_files = media_files - db_paths
        missing_files = db_paths - media_files

        for path in new_files:
            parts = path.split('/')
            info = parse_path(parts)
            user_id = info.get('user_id')
            category = info.get('category')

            if not user_id:
                print(f"⚠ 無法解析路徑 (user_id 缺失): {path}")
                continue

            try:
                if model == ClosetItem:
                    model.objects.create(user_id=user_id, category=category, image=path)
                elif model == MimicItem:
                    model.objects.create(user_id=user_id, image=path, backend_path=None)
                elif model == MimicBackendItem:
                    model.objects.create(user_id=user_id, image=path)
                print(f"✅ 已新增至資料庫 ({model.__name__}): {path}")
            except Exception as e:
                print(f"❌ {model.__name__} 新增失敗 {path}: {e}")

        deleted_count, _ = model.objects.filter(image__in=missing_files).delete()
        for path in missing_files:
            print(f"🗑 {model.__name__} 已刪除資料庫紀錄: {path}")

        if new_files or missing_files:
            print(f"\n📦 {model.__name__} 同步完成：新增 {len(new_files)} 筆，刪除 {deleted_count} 筆。\n")
        else:
            print(f"✅ {model.__name__} 資料庫與檔案一致，無需更新。\n")

if __name__ == '__main__':
    sync_media_db()
