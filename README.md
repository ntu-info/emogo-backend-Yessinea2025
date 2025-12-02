[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/e7FBMwSa)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=21873006&assignment_repo_type=AssignmentRepo)
# Deploy FastAPI on Render

Use this repo as a template to deploy a Python [FastAPI](https://fastapi.tiangolo.com) service on Render.

See https://render.com/docs/deploy-fastapi or follow the steps below:

## Manual Steps

1. You may use this repository directly or [create your own repository from this template](https://github.com/render-examples/fastapi/generate) if you'd like to customize the code.
2. Create a new Web Service on Render.
3. Specify the URL to your new repository or this repository.
4. Render will automatically detect that you are deploying a Python service and use `pip` to download the dependencies.
5. Specify the following as the Start Command.

    ```shell
    uvicorn main:app --host 0.0.0.0 --port $PORT
    ```

6. Click Create Web Service.

Or simply click:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/render-examples/fastapi)

## Thanks

Thanks to [Harish](https://harishgarg.com) for the [inspiration to create a FastAPI quickstart for Render](https://twitter.com/harishkgarg/status/1435084018677010434) and for some sample code!  


# 📱 前端 App 測試

## Android APK 下載

### APK 下載連結： https://expo.dev/accounts/yessinea/projects/expo-router-mwe/builds/330e4af7-1ab5-4f3a-9229-fbceed098600

## 使用說明

1. 選擇心情
   - 點擊 1-5 顆心來評分
   - 1 = 很難過，5 = 很開心

2. 輸入備註（可選）
   - 記錄當下的想法或發生的事

3. 點擊「下一步」

4. 錄製影片
   - 會自動開始錄影（1 秒）
   - 錄製完成後自動上傳

5. 查看資料
   - 訪問：https://emogo-backend-yessinea2025.onrender.com/export
   - 可以看到剛上傳的資料

## ⚠️ 注意事項
- ### 首次連接較慢：Render Free Plan 可能需要 30-60 秒喚醒


# EmoGo 後端 API

情緒日記應用的後端服務 - 使用 FastAPI + MongoDB Atlas

---

## 🌐 部署資訊

**後端部署網址：** https://emogo-backend-yessinea2025.onrender.com

**📊 資料中心頁面：** https://emogo-backend-yessinea2025.onrender.com/export

---

## 📦 資料類型

在資料匯出頁面可以查看和下載以下三種資料：

### 1. 😊 情緒資料 (Sentiments)
- 包含：情緒類型、心情評分 (1-5)、用戶備註、時間戳記
- 下載格式：CSV、JSON
- 預覽頁面：https://emogo-backend-yessinea2025.onrender.com/export/sentiments/preview

### 2. 📍 GPS 座標 (GPS Coordinates)
- 包含：緯度、經度、時間戳記
- 下載格式：CSV、JSON
- 預覽頁面：https://emogo-backend-yessinea2025.onrender.com/export/gps/preview

### 3. 🎥 影片日記 (Vlogs)
- 包含：影片檔案、檔案大小、上傳時間、描述
- 下載格式：單一影片、批次 ZIP
- 列表頁面：https://emogo-backend-yessinea2025.onrender.com/export/vlogs

---

## 🎯 API 端點

### 資料上傳
- `POST /sentiments` - 上傳情緒資料
- `POST /gps` - 上傳 GPS 座標
- `POST /vlogs` - 上傳影片檔案

### 資料匯出
- `GET /export` - 📊 **資料中心**（主要入口）
- `GET /export/sentiments/csv` - 下載情緒資料 CSV
- `GET /export/sentiments/preview` - 預覽情緒資料
- `GET /export/gps/csv` - 下載 GPS 資料 CSV
- `GET /export/gps/preview` - 預覽 GPS 資料
- `GET /export/vlogs` - 查看影片列表和下載
- `GET /export/all` - 查看完整資料（JSON）
- `GET /export/all/download` - 下載完整資料（JSON 檔案）

---

## 🗄️ 資料庫架構

**資料庫：** MongoDB Atlas  
**資料庫名稱：** emogo_database

### Collections

#### sentiments
```json
{
  "emotion": "very_happy",
  "score": 5,
  "note": "今天天氣很好",
  "timestamp": "2024-12-02 18:30:00"
}
```

#### gps_coordinates
```json
{
  "latitude": 24.7936,
  "longitude": 120.9960,
  "timestamp": "2024-12-02 18:30:00"
}
```

#### vlogs
```json
{
  "filename": "20241202_183000_video.mp4",
  "original_filename": "video.mp4",
  "size": 1048576,
  "description": "今天的心情記錄",
  "upload_time": "2024-12-02 18:30:00"
}
```

---

## 🛠️ 技術架構

- **後端框架：** FastAPI 0.115.5
- **Web 伺服器：** Uvicorn 0.32.1
- **資料庫驅動：** Motor 3.6.0 (Async MongoDB)
- **資料庫：** MongoDB Atlas (雲端)
- **部署平台：** Render (Free Plan)
- **程式語言：** Python 3.13

---

## 💻 本地開發

### 環境需求
```bash
Python 3.12+
pip
```

### 安裝步驟

1. Clone 專案
```bash
git clone https://github.com/ntu-info/emogo-backend-Yessinea2025.git
cd emogo-backend-Yessinea2025
```

2. 安裝套件
```bash
pip install -r requirements.txt
```

3. 設定環境變數

建立 `.env` 檔案：
```bash
MONGODB_URI=mongodb+srv://your_username:your_password@cluster0.xxxxx.mongodb.net/
DB_NAME=emogo_database
```

4. 啟動伺服器
```bash
python main.py
```

伺服器會在 http://localhost:8000 啟動

---

## 📦 專案結構

```
emogo-backend-Yessinea2025/
├── main.py              # 主程式（FastAPI 應用）
├── requirements.txt     # Python 套件清單
├── .env                 # 環境變數（不上傳到 Git）
├── .gitignore           # Git 忽略清單
├── README.md            # 專案說明文件
└── uploads/             # 上傳的影片（不上傳到 Git）
    └── vlogs/           # 影片檔案存放處
```

---

## ⚠️ 注意事項

### 時區設定
所有時間顯示為**台灣時區 (UTC+8)**：
- CSV 匯出
- 網頁預覽
- JSON 匯出

資料庫內部儲存為 UTC，顯示時自動轉換。

### Render Free Plan 限制

**檔案儲存：**
- 影片檔案為**暫時性儲存**
- 重新部署或休眠後會清空
- 影片的**元資料**（檔名、大小、上傳時間）永久保存在 MongoDB
- 情緒和 GPS 資料永久保存在 MongoDB

**服務狀態：**
- 15 分鐘無活動會進入休眠
- 首次訪問需要 30-60 秒喚醒時間

---

## 🧪 測試方式

### 1. 測試資料匯出頁面
```
訪問：https://emogo-backend-yessinea2025.onrender.com/export
應該看到：情緒、GPS、影片的筆數統計和下載按鈕
```

### 2. 測試 CSV 下載
```
點擊「下載 CSV」按鈕
應該下載包含中文的 CSV 檔案（UTF-8 with BOM）
```

### 3. 測試影片下載
```
訪問影片列表頁面
應該可以下載個別影片或批次打包下載
```

### 4. 使用 App 上傳測試
```
1. 在 EmoGo App 選擇心情
2. 輸入備註
3. 錄製影片
4. 上傳到雲端
5. 在 /export 頁面確認資料出現
```

---

## 📊 功能特色

### ✨ 資料匯出功能
- ✅ CSV 格式匯出（支援中文）
- ✅ JSON 格式匯出
- ✅ 影片批次下載（ZIP）
- ✅ 網頁預覽資料
- ✅ 時區自動轉換（UTC+8）

### 🎨 使用者介面
- ✅ 美觀的資料匯出中心
- ✅ 統計資料即時顯示
- ✅ 一鍵批次操作
- ✅ 響應式設計

### 🔒 資料管理
- ✅ MongoDB 雲端儲存
- ✅ 資料備份與匯出
- ✅ 批次清空功能（帶確認）