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

# EmoGo 後端 API

情緒日記應用的後端服務 - 使用 FastAPI + MongoDB Atlas + GridFS

---

## 🌐 部署資訊

**後端部署網址：** https://emogo-backend-yessinea2025.onrender.com

**📊 資料匯出頁面：** https://emogo-backend-yessinea2025.onrender.com/export  

---

## 📱 前端 App

### Android APK 下載

**下載連結：** https://expo.dev/accounts/yessinea/projects/expo-router-mwe/builds/2aedaf10-163f-483d-baa6-8b25115f69ed

### 使用說明

1. **選擇心情** - 點擊 1-5 顆心評分（1 = 很難過，5 = 很開心）
2. **輸入備註**（可選）- 記錄當下的想法
3. **點擊「下一步」**
4. **錄製影片** - 自動錄影 1 秒並上傳
5. **查看資料** - 訪問 https://emogo-backend-yessinea2025.onrender.com/export

### ⚠️ App 使用注意事項

**首次連接較慢：** Render Free Plan 可能需要 30-60 秒喚醒

**建議測試流程：**
1. 先在瀏覽器訪問 `/export` 頁面（喚醒伺服器）
2. 等待頁面完全載入（約 30-60 秒）
3. 立即使用 App 上傳資料
4. 上傳應該會成功 ✅

---

## 📦 資料類型與匯出

### 1. 😊 情緒資料 (Sentiments)

**包含內容：**
- 情緒類型（very_sad, sad, neutral, happy, very_happy）
- 心情評分 (1-5)
- 用戶備註
- 時間戳記（台灣時區 UTC+8）

**匯出方式：**
- CSV 下載：https://emogo-backend-yessinea2025.onrender.com/export/sentiments/csv
- 網頁預覽：https://emogo-backend-yessinea2025.onrender.com/export/sentiments/preview

---

### 2. 📍 GPS 座標 (GPS Coordinates)

**包含內容：**
- 緯度（latitude）
- 經度（longitude）
- 時間戳記（台灣時區 UTC+8）

**匯出方式：**
- CSV 下載：https://emogo-backend-yessinea2025.onrender.com/export/gps/csv
- 網頁預覽：https://emogo-backend-yessinea2025.onrender.com/export/gps/preview

---

### 3. 🎥 影片日記 (Vlogs)

**包含內容：**
- 影片檔案（MP4 格式）
- 檔案大小
- 上傳時間（台灣時區 UTC+8）
- 影片描述

**匯出方式：**
- 影片列表：https://emogo-backend-yessinea2025.onrender.com/export/vlogs
- 單一下載：點擊列表中的「下載」按鈕
- 批次下載：選取多個影片後下載 ZIP
- 全部下載：一鍵下載所有影片的 ZIP

---

## 🎥 影片儲存架構（GridFS）

### MongoDB GridFS 永久儲存

**採用技術：** MongoDB GridFS

**特點：**
- ✅ 影片檔案永久保存在 MongoDB 資料庫中
- ✅ 不受 Render 伺服器重啟影響
- ✅ 不受 Render 休眠影響
- ✅ 影片下載功能永久可用
- ✅ 與資料庫資料享有相同的持久性保證

**資料庫結構：**
```
emogo_database
├── sentiments           # 情緒資料 collection
├── gps_coordinates      # GPS 座標 collection
├── vlogs                # 影片元資料 collection
├── fs.files            # GridFS - 檔案資訊
└── fs.chunks           # GridFS - 檔案內容（分塊）
```
---

## 🎯 API 端點完整列表

### 基本資訊
- `GET /` - API 說明和端點列表

### 資料上傳
- `POST /sentiments` - 上傳情緒資料
- `POST /gps` - 上傳 GPS 座標
- `POST /vlogs` - 上傳影片（自動存入 GridFS）

### 資料匯出與下載
- `GET /export` - 📊 **資料中心**（主要入口，TA 從這裡開始）
- `GET /export/sentiments/csv` - 下載情緒資料 CSV
- `GET /export/sentiments/preview` - 網頁預覽情緒資料
- `GET /export/gps/csv` - 下載 GPS 資料 CSV
- `GET /export/gps/preview` - 網頁預覽 GPS 資料
- `GET /export/vlogs` - 影片列表（含下載按鈕）
- `GET /vlogs/{filename}` - 下載特定影片（從 GridFS）
- `GET /export/vlogs/download-all` - 下載所有影片（ZIP）
- `GET /export/vlogs/download-multiple` - 下載選取的影片（ZIP）
- `GET /export/all` - 查看完整資料（JSON 格式）
- `GET /export/all/download` - 下載完整資料（JSON 檔案）

### 資料管理
- `POST /clear_all_data` - 清空所有資料（含 GridFS，需二次確認）

---

## 🗄️ 資料庫架構

**資料庫平台：** MongoDB Atlas (雲端)  
**資料庫名稱：** emogo_database  
**連接方式：** MongoDB URI (使用 Motor 異步驅動)

### Collections 結構

#### sentiments
```json
{
  "_id": "ObjectId",
  "emotion": "very_happy",
  "score": 5,
  "note": "今天天氣很好",
  "timestamp": "2024-12-02T10:30:00.000Z"
}
```

#### gps_coordinates
```json
{
  "_id": "ObjectId",
  "latitude": 24.7936,
  "longitude": 120.9960,
  "timestamp": "2024-12-02T10:30:00.000Z"
}
```

#### vlogs
```json
{
  "_id": "ObjectId",
  "file_id": "GridFS_ObjectId",
  "filename": "20241202_183000_video.mp4",
  "original_filename": "video.mp4",
  "size": 1048576,
  "description": "今天的心情記錄",
  "upload_time": "2024-12-02T10:30:00.000Z",
  "storage": "gridfs"
}
```

#### fs.files (GridFS)
```json
{
  "_id": "ObjectId",
  "length": 1048576,
  "chunkSize": 261120,
  "uploadDate": "2024-12-02T10:30:00.000Z",
  "filename": "20241202_183000_video.mp4",
  "metadata": {
    "original_filename": "video.mp4",
    "content_type": "video/mp4",
    "description": "今天的心情記錄",
    "upload_time": "2024-12-02T10:30:00.000Z",
    "size": 1048576
  }
}
```

#### fs.chunks (GridFS)
```json
{
  "_id": "ObjectId",
  "files_id": "GridFS_ObjectId",
  "n": 0,
  "data": "Binary"
}
```

---

## 🛠️ 技術架構

### 後端技術
- **後端框架：** FastAPI 0.115.5
- **ASGI 伺服器：** Uvicorn 0.32.1
- **MongoDB 驅動：** Motor 3.6.0 (Async)
- **檔案處理：** python-multipart 0.0.18
- **環境變數：** python-dotenv 1.0.1

### 資料庫與儲存
- **資料庫：** MongoDB Atlas (Free Tier)
- **影片儲存：** MongoDB GridFS
- **時區處理：** UTC 儲存，顯示時轉換為 UTC+8

### 部署環境
- **平台：** Render (Free Plan)
- **程式語言：** Python 3.13
- **地區：** 自動選擇

---

## 📦 專案結構

```
emogo-backend-Yessinea2025/
├── main.py              # FastAPI 主程式（含 GridFS）
├── requirements.txt     # Python 套件清單
├── .env                 # 環境變數（本地開發，不上傳）
├── .gitignore           # Git 忽略清單
├── README.md            # 本文件
└── uploads/             # （已棄用，使用 GridFS 取代）
```
---

## ⚠️ Render Free Plan 特性

### 服務休眠機制

**休眠條件：**
- 15 分鐘無任何請求

**喚醒時間：**
- 首次請求需要 30-60 秒喚醒

**影響：**
- 首次訪問較慢
- App 上傳可能 timeout

**解決方案：**
- 前端實作了 90 秒 timeout
- 自動重試機制（最多 2 次）
- 建議先訪問網頁喚醒伺服器

### 檔案系統限制

**Render Free Plan：**
- ❌ 沒有持久化檔案系統
- ❌ 重啟後本地檔案會消失

**我們的解決方案：**
- ✅ 使用 MongoDB GridFS 儲存影片
- ✅ 所有檔案永久保存在資料庫
- ✅ 完全不依賴 Render 的檔案系統

---

## 📊 功能特色總結

### ✨ 資料匯出功能
- ✅ CSV 格式匯出（UTF-8 with BOM，支援中文）
- ✅ JSON 格式匯出
- ✅ 影片單一下載
- ✅ 影片批次下載（ZIP）
- ✅ 一鍵下載所有資料
- ✅ 網頁即時預覽
- ✅ 時區自動轉換（UTC+8）

### 🎨 使用者介面
- ✅ 美觀的資料匯出中心
- ✅ 統計資料即時顯示
- ✅ 清晰的操作按鈕
- ✅ 響應式設計
- ✅ GridFS 永久儲存說明

### 🔒 資料安全與管理
- ✅ MongoDB Atlas 雲端儲存
- ✅ GridFS 永久檔案儲存
- ✅ 資料備份與匯出
- ✅ 批次清空功能（二次確認保護）

### 🚀 效能與可靠性
- ✅ 異步 MongoDB 操作（Motor）
- ✅ GridFS 分塊儲存大檔案
- ✅ 自動重試機制（前端）
- ✅ 延長 timeout 適應休眠
- ✅ 影片永久可用（不受重啟影響）

---

**最後更新：** 2024/12/04  
**版本：** 1.0.0 (GridFS)