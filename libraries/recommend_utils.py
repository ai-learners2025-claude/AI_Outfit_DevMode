import os
import numpy as np
import pandas as pd
from PIL import Image

def cosine_similarity(a, b):
    a = a / np.linalg.norm(a, axis=-1, keepdims=True)
    b = b / np.linalg.norm(b, axis=-1, keepdims=True)
    return np.dot(a, b.T)


def recommend_top3(target_folder, closet_folder, base_name):
    """
    根據指定的 base_name（如 try4），從 target_folder 中找出 try4_removed_bg.csv，
    與 closet_folder 下各類別衣物進行相似度比對，回傳 top3 推薦圖檔。
    """
    categories = ['top', 'bottom', 'shoes', 'dress', 'skirt', 'outwear']
    recommendations = {}

    for cat in categories:
        # 改為使用 base_name 組成 target_csv 路徑
        target_csv = os.path.join(target_folder, cat, f"{base_name}_removed_bg.csv")
        if not os.path.exists(target_csv):
            continue

        try:
            df_target = pd.read_csv(target_csv)
        except Exception as e:
            print(f"[Warning] Failed to load target csv {target_csv}: {e}")
            continue

        target_feat = df_target.drop(columns=['file']).values

        closet_cat_folder = os.path.join(closet_folder, cat)
        if not os.path.exists(closet_cat_folder):
            continue

        closet_feats = []
        closet_files = []
        for file in os.listdir(closet_cat_folder):
            if file.endswith('.csv'):
                csv_path = os.path.join(closet_cat_folder, file)
                try:
                    df_closet = pd.read_csv(csv_path)
                    closet_feats.append(df_closet.drop(columns=['file']).values[0])
                    closet_files.append(file.replace('.csv', '.png'))
                except Exception as e:
                    print(f"[Warning] Failed to read {csv_path}: {e}")

        if len(closet_feats) == 0:
            continue

        closet_feats = np.array(closet_feats)
        sims = cosine_similarity(target_feat, closet_feats)[0]

        top_idx = sims.argsort()[::-1][:3]
        top3_files = [closet_files[i] for i in top_idx]
        top3_paths = [os.path.join(cat, file) for file in top3_files]
        recommendations[cat] = top3_paths

    return recommendations
