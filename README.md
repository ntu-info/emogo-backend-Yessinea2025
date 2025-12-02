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

---

## 🚀 部署資訊

**部署網址：** https://emogo-backend-yessinea.onrender.com （部署後更新）

**資料匯出頁面：** https://emogo-backend-yessinea.onrender.com/export

---

## 📊 API 端點

### 資料上傳
- `POST /sentiments` - 上傳情緒資料
- `POST /gps` - 上傳 GPS 座標
- `POST /vlogs` - 上傳影片檔案

### 資料匯出
- `GET /export` - 資料中心（網頁）
- `GET /export/sentiments/csv` - 下載情緒資料 CSV
- `GET /export/gps/csv` - 下載 GPS 資料 CSV
- `GET /export/vlogs` - 查看影片列表
- `GET /export/all/download` - 下載完整資料 JSON

---

## 🗄️ 資料庫

使用 MongoDB Atlas 雲端資料庫

**Collections:**
- `sentiments` - 情緒記錄（emotion, score, note, timestamp）
- `gps_coordinates` - GPS 座標（latitude, longitude, timestamp）
- `vlogs` - 影片資訊（filename, size, upload_time）

---

## 🛠️ 技術架構

- **後端框架：** FastAPI
- **資料庫：** MongoDB Atlas
- **部署平台：** Render
- **程式語言：** Python 3.12

---

## 💻 本地開發

### 環境需求
```bash
Python 3.12+
pip
```

### 安裝套件
```bash
pip install -r requirements.txt
```

### 設定環境變數
建立 `.env` 檔案：
```bash
MONGODB_URI=mongodb+srv://your_username:your_password@cluster0.xxxxx.mongodb.net/
DB_NAME=emogo_database
```

### 啟動伺服器
```bash
python main.py
```

伺服器會在 http://localhost:8000 啟動

---

## 📦 專案結構

```
emogo-backend-Yessinea2025/
├── main.py              # 主程式
├── requirements.txt     # Python 套件清單
├── .env                 # 環境變數（不上傳）
├── .gitignore           # Git 忽略清單
├── README.md            # 專案說明
└── uploads/             # 上傳檔案（不上傳）
    └── vlogs/           # 影片檔案
```

---

## ⚠️ 注意事項

### 影片儲存
Render Free Plan 的檔案系統是**暫時性的**：
- 影片檔案存在 `uploads/` 資料夾
- 重新部署時會清空
- 影片的元資料（檔名、大小）儲存在 MongoDB，不會遺失