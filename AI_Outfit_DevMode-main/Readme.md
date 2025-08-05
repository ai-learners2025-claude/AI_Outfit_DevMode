## 認識MyStylist
MyStylist 是一款結合個人化衣櫃管理與 AI 模仿穿搭顧問的智慧推薦系統，致力於協助現代女性簡化日常穿搭決策，打造專屬風格。  

---
## 平台核心技術
結合 LINE LIFF 前端框架、LINE BOT 互動介面、Rembg 圖片去背、FLUX-Kontext 姿勢修正、OpenRouter Qwen文字描述生成，  
以及 FashionCLIP 圖文語意比對，打造個人化的衣櫥管理與模仿穿搭推薦流程。  
系統部署於 GCP 虛擬機並搭配 Django Web 框架與 Apache 伺服器，提供穩定、高效的使用體驗。  

---
## 網址
https://brianoxox.learnai2025.com/

---
## Source Code使用步驟：
(1) 需替換成自己的Runninghub API KEY及Workflow id、OPENROUTER_API_KEY、RAPI Key  
(2) 指定python版本：python 3.10
(3) 建立虛擬環境：python -m venv vm  
(4) 進入虛擬環境：vm\Scripts\activate  
(5) 下載所需套件：pip install -r requirements_python310.txt  
(6) 建立空的資料庫：python manage.py migrate  
(7) 將實體照片同步至資料庫：python SyncMediaToDb.py  
(8) 開始進入測試環境：python manage.py runserver  

---
## 未來展望

可結合鏡頭掃描自動分類、一鍵補齊穿搭組合、AR 虛擬試穿、天氣與行程穿搭整合，甚至推動永續時尚與理性消費。  
系統未來也可導入 AI 個人顧問，提供根據膚色、身形與場合的專屬每日推薦。  

MyStylist 不只是一套穿搭工具，而是貼近使用者生活、理解個人風格的虛擬設計師，陪伴你從衣櫃出發，梳理衣櫃的可能性，探索時尚自信，「每一天都穿出自己的樣子」。
