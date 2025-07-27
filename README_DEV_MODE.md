# AI Outfit - 開發模式說明

## 概述
已將 LINE LIFF 衣櫃上傳頁面修改為支援開發模式，讓開發者可以在不使用 LINE LIFF 驗證的情況下測試功能。

## 開發模式啟用方式

### 方法 1: 自動檢測（推薦）
當 Django 的 `DEBUG = True` 時，自動啟用開發模式。

### 方法 2: URL 參數
在網址後面加上 `?dev=1` 參數，例如：
```
http://127.0.0.1:8000/liff/closet/?dev=1
```
### 步驟：
(1) 建立虛擬環境：python -m venv vm  
(2) 進入虛擬環境：vm\Scripts\activate  
(3) 下載所需套件：pip install -r requirements.txt  
(4) 建立資料庫：python manage.py makemigrations  
               python manage.py migrate  
(5) 將實體照片同步至資料庫：python SyncMediaToDb.py  
(6) 開始進入測試環境：python manage.py runserver  

## 開發模式功能

### 1. 跳過 LINE LIFF 驗證
- 不會呼叫 `liff.init()`
- 不需要登入 LINE 帳號
- 直接使用固定的測試 UserId: `dev_test_user_12345`

### 2. 視覺提示
- 頁面頂部會顯示黃色背景的 "🚀 開發模式：使用測試 UserId" 提示
- 狀態欄會顯示當前使用的測試 UserId

### 3. 圖片選擇限制
- 在開發模式下，"LINE 拍照/相簿" 功能會被禁用
- 點選會自動轉為使用本機檔案選擇器
- 會彈出警告提示使用者改用本機選擇

## 修改的檔案

1. **`templates/liff/closet_upload.html`**
   - 新增開發模式檢測邏輯
   - 修改 LIFF 初始化流程
   - 新增開發模式視覺提示
   - 修改圖片選擇邏輯

2. **`outfit/views.py`**
   - 在 `closet_upload_view` 函式中新增 `debug` 參數傳遞

## 使用建議

### 開發階段
```bash
# 確保 Django 設定為開發模式
DEBUG = True

# 啟動伺服器
python manage.py runserver

# 訪問衣櫃上傳頁面
http://127.0.0.1:8000/liff/closet/
```

### 正式部署
```bash
# 設定為正式模式
DEBUG = False

# 會自動使用 LINE LIFF 驗證流程
```

## 測試功能

在開發模式下，你可以測試：
- ✅ 本機圖片上傳
- ✅ 圖片分類設定
- ✅ 圖片篩選功能
- ✅ 圖片刪除功能
- ✅ 後端 API 呼叫

無法測試：
- ❌ LINE LIFF 拍照功能
- ❌ LINE LIFF 相簿功能
- ❌ 真實的 LINE 使用者 ID

## 注意事項

1. 開發模式使用固定 UserId `dev_test_user_12345`，所有測試資料都會關聯到這個 ID
2. 正式部署時務必確保 `DEBUG = False`
3. 可以使用 URL 參數 `?dev=1` 在正式環境中暫時啟用開發模式（僅限測試）
