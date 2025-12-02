from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import os
import json
import csv
import io
import zipfile
from bson import ObjectId
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

app = FastAPI(title="EmoGo Backend API")

# CORS 設定 - 讓你的 React Native App 可以連接
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該設定具體的網址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB 連接設定
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "emogo_database")

# 台灣時區 (UTC+8)
TW_TZ = timezone(timedelta(hours=8))

def to_tw_time(dt):
    """將 datetime 轉換為台灣時間字串"""
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        return dt
    # 如果是 naive datetime，假設是 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # 轉換為台灣時間
    tw_time = dt.astimezone(TW_TZ)
    return tw_time.strftime("%Y-%m-%d %H:%M:%S")

# MongoDB 連接會在 startup 事件中初始化
@app.on_event("startup")
async def startup_db_client():
    """啟動時連接 MongoDB"""
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    app.mongodb = app.mongodb_client[DB_NAME]
    print(f"✅ Connected to MongoDB: {DB_NAME}")

@app.on_event("shutdown")
async def shutdown_db_client():
    """關閉時斷開 MongoDB 連接"""
    app.mongodb_client.close()
    print("❌ Disconnected from MongoDB")

# 建立資料夾存放上傳的影片
UPLOAD_DIR = "uploads/vlogs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pydantic models
class Sentiment(BaseModel):
    emotion: str
    score: int  # 1-5 心情評分
    note: Optional[str] = None
    timestamp: Optional[datetime] = None

class GPSCoordinate(BaseModel):
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None

# API Endpoints

@app.get("/")
async def root():
    """首頁 - API 說明"""
    return {
        "message": "Welcome to EmoGo Backend API",
        "endpoints": {
            "POST /sentiments": "上傳情緒資料",
            "POST /gps": "上傳 GPS 座標",
            "POST /vlogs": "上傳影片",
            "GET /export": "資料匯出頁面",
            "GET /export/sentiments/csv": "下載情緒資料 (CSV)",
            "GET /export/gps/csv": "下載 GPS 資料 (CSV)",
            "GET /export/vlogs": "取得影片列表",
            "GET /export/all": "在網頁查看所有資料 (JSON)",
            "GET /export/all/download": "下載所有資料 (JSON 檔案)"
        }
    }

@app.post("/sentiments")
async def create_sentiment(sentiment: Sentiment):
    """接收情緒資料"""
    sentiment_dict = sentiment.dict()
    if sentiment_dict["timestamp"] is None:
        sentiment_dict["timestamp"] = datetime.now()
    
    result = await app.mongodb["sentiments"].insert_one(sentiment_dict)
    return {"message": "Sentiment saved", "id": str(result.inserted_id)}

@app.post("/gps")
async def create_gps(gps: GPSCoordinate):
    """接收 GPS 座標"""
    gps_dict = gps.dict()
    if gps_dict["timestamp"] is None:
        gps_dict["timestamp"] = datetime.now()
    
    result = await app.mongodb["gps_coordinates"].insert_one(gps_dict)
    return {"message": "GPS coordinate saved", "id": str(result.inserted_id)}

@app.post("/vlogs")
async def upload_vlog(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """接收影片檔案"""
    # 產生唯一檔名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # 儲存影片檔案
    with open(filepath, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 將影片資訊存入資料庫
    vlog_info = {
        "filename": filename,
        "original_filename": file.filename,
        "filepath": filepath,
        "description": description,
        "upload_time": datetime.now(),
        "size": len(content)
    }
    
    result = await app.mongodb["vlogs"].insert_one(vlog_info)
    return {"message": "Vlog uploaded", "id": str(result.inserted_id), "filename": filename}

@app.get("/export", response_class=HTMLResponse)
async def export_page():
    """資料匯出頁面 - TA 可以在這裡看到和下載所有資料"""
    
    # 統計資料數量
    sentiment_count = await app.mongodb["sentiments"].count_documents({})
    gps_count = await app.mongodb["gps_coordinates"].count_documents({})
    vlog_count = await app.mongodb["vlogs"].count_documents({})
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>EmoGo 資料匯出</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #333;
            }}
            .data-section {{
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .download-btn {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin: 5px;
                border: none;
                cursor: pointer;
                font-size: 14px;
            }}
            .download-btn:hover {{
                background-color: #45a049;
            }}
            .danger-btn {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #f44336;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin: 5px;
                border: none;
                cursor: pointer;
                font-size: 14px;
            }}
            .danger-btn:hover {{
                background-color: #d32f2f;
            }}
            .stats {{
                color: #666;
                margin: 10px 0;
            }}
            .warning-box {{
                background-color: #fff3cd;
                border-left: 4px solid #ff9800;
                padding: 12px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            .warning-text {{
                color: #856404;
                font-size: 14px;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <h1>📊 EmoGo 資料中心</h1>
        
        <div class="data-section">
            <h2>😊 情緒資料 (Sentiments)</h2>
            <p class="stats">總筆數: {sentiment_count}</p>
            <a href="/export/sentiments/csv" class="download-btn">📥 下載 CSV</a>
            <a href="/export/sentiments/preview" class="download-btn">👁️ 預覽資料</a>
        </div>
        
        <div class="data-section">
            <h2>📍 GPS 座標 (GPS Coordinates)</h2>
            <p class="stats">總筆數: {gps_count}</p>
            <a href="/export/gps/csv" class="download-btn">📥 下載 CSV</a>
            <a href="/export/gps/preview" class="download-btn">👁️ 預覽資料</a>
        </div>
        
        <div class="data-section">
            <h2>🎥 影片日記 (Vlogs)</h2>
            <p class="stats">總筆數: {vlog_count}</p>
            <a href="/export/vlogs" class="download-btn">📋 查看影片列表</a>
        </div>
        
        <div class="data-section">
            <h2>📦 完整資料匯出</h2>
            <a href="/export/all" class="download-btn">👁️ 在網頁查看 JSON</a>
            <a href="/export/all/download" class="download-btn">📥 下載 JSON 檔案</a>
        </div>
        
        <div class="data-section">
            <h2>⚠️ 危險操作區</h2>
            <div class="warning-box">
                <p class="warning-text">⚠️ 警告：清空資料後無法復原，請謹慎操作！</p>
            </div>
            <button class="danger-btn" onclick="clearAllData()">🗑️ 清空所有資料</button>
        </div>

        <script>
        async function clearAllData() {{
            if (!confirm("⚠️ 確定要清空所有資料嗎？\\n\\n此操作將刪除：\\n• 所有情緒記錄\\n• 所有 GPS 座標\\n• 所有影片日記\\n\\n此操作無法復原！")) {{
                return;
            }}
            
            // 二次確認
            if (!confirm("🚨 最後確認：真的要刪除所有資料嗎？")) {{
                return;
            }}

            try {{
                const response = await fetch("/clear_all_data", {{
                    method: "POST"
                }});

                if (response.ok) {{
                    const result = await response.json();
                    alert(`✅ 所有資料已清空！\\n\\n刪除統計：\\n• 情緒資料：${{result.deleted_counts.sentiments}} 筆\\n• GPS 座標：${{result.deleted_counts.gps_coordinates}} 筆\\n• 影片日記：${{result.deleted_counts.vlogs}} 筆`);
                    location.reload();
                }} else {{
                    alert("❌ 清空資料失敗！");
                }}
            }} catch (err) {{
                alert("❌ 發生錯誤: " + err.message);
            }}
        }}
        </script>
    </body>
    </html>
    '''
    
    return HTMLResponse(content=html_content)

@app.get("/export/sentiments")
async def export_sentiments():
    """下載所有情緒資料（JSON）"""
    sentiments = await app.mongodb["sentiments"].find().to_list(1000)
    
    # 將 ObjectId 轉換為字串
    for s in sentiments:
        s["_id"] = str(s["_id"])
        if "timestamp" in s and s["timestamp"]:
            s["timestamp"] = s["timestamp"].isoformat()
    
    return JSONResponse(content=sentiments)

@app.get("/export/sentiments/csv")
async def export_sentiments_csv():
    """下載情緒資料為 CSV 檔案"""
    sentiments = await app.mongodb["sentiments"].find().to_list(1000)
    
    # 建立 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 寫入標題
    writer.writerow(['emotion', 'score', 'note', 'timestamp'])
    
    # 寫入資料
    for s in sentiments:
        timestamp = to_tw_time(s.get("timestamp"))  # 台灣時間
        
        writer.writerow([
            s.get('emotion', ''),
            s.get('score', ''),
            s.get('note', ''),
            timestamp
        ])
    
    # 產生檔名
    filename = f"sentiments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # 加入 UTF-8 BOM 讓 Excel 正確識別中文
    csv_content = '\ufeff' + output.getvalue()
    
    # 返回 CSV 檔案
    return Response(
        content=csv_content.encode('utf-8'),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.get("/export/sentiments/preview", response_class=HTMLResponse)
async def preview_sentiments():
    """預覽情緒資料"""
    sentiments = await app.mongodb["sentiments"].find().to_list(100)
    
    rows = ""
    for s in sentiments:
        timestamp = to_tw_time(s.get("timestamp"))  # 台灣時間
        rows += f"""
        <tr>
            <td>{s.get('emotion', 'N/A')}</td>
            <td>{s.get('score', 'N/A')}</td>
            <td>{s.get('note', 'N/A')}</td>
            <td>{timestamp}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sentiments Preview</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h1>情緒資料預覽</h1>
        <p><a href="/export">← 返回</a></p>
        <table>
            <tr>
                <th>情緒</th>
                <th>心情評分</th>
                <th>備註</th>
                <th>時間 (台灣時區)</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/export/gps")
async def export_gps():
    """下載所有 GPS 資料（JSON）"""
    gps_data = await app.mongodb["gps_coordinates"].find().to_list(1000)
    
    for g in gps_data:
        g["_id"] = str(g["_id"])
        if "timestamp" in g and g["timestamp"]:
            g["timestamp"] = g["timestamp"].isoformat()
        # 移除 accuracy 欄位
        g.pop("accuracy", None)
    
    return JSONResponse(content=gps_data)

@app.get("/export/gps/csv")
async def export_gps_csv():
    """下載 GPS 資料為 CSV 檔案"""
    gps_data = await app.mongodb["gps_coordinates"].find().to_list(1000)
    
    # 建立 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 寫入標題
    writer.writerow(['latitude', 'longitude', 'timestamp'])
    
    # 寫入資料
    for g in gps_data:
        timestamp = to_tw_time(g.get("timestamp"))  # 台灣時間
        
        writer.writerow([
            g.get('latitude', ''),
            g.get('longitude', ''),
            timestamp
        ])
    
    # 產生檔名
    filename = f"gps_coordinates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # 加入 UTF-8 BOM 讓 Excel 正確識別中文
    csv_content = '\ufeff' + output.getvalue()
    
    # 返回 CSV 檔案
    return Response(
        content=csv_content.encode('utf-8'),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.get("/export/gps/preview", response_class=HTMLResponse)
async def preview_gps():
    """預覽 GPS 資料"""
    gps_data = await app.mongodb["gps_coordinates"].find().to_list(100)
    
    rows = ""
    for g in gps_data:
        timestamp = to_tw_time(g.get("timestamp"))  # 台灣時間
        rows += f"""
        <tr>
            <td>{g.get('latitude', 'N/A')}</td>
            <td>{g.get('longitude', 'N/A')}</td>
            <td>{timestamp}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GPS Preview</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #2196F3; color: white; }}
        </style>
    </head>
    <body>
        <h1>GPS 座標預覽</h1>
        <p><a href="/export">← 返回</a></p>
        <table>
            <tr>
                <th>緯度</th>
                <th>經度</th>
                <th>時間 (台灣時區)</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/export/vlogs", response_class=HTMLResponse)
async def export_vlogs():
    """列出所有影片（支援批次下載）"""
    vlogs = await app.mongodb["vlogs"].find().to_list(1000)
    
    rows = ""
    for v in vlogs:
        upload_time = to_tw_time(v.get("upload_time"))  # 台灣時間
        
        size_mb = v.get("size", 0) / (1024 * 1024)
        filename = v.get('filename', '')
        
        rows += f"""
        <tr>
            <td><input type="checkbox" class="video-checkbox" value="{filename}"></td>
            <td>{v.get('original_filename', 'N/A')}</td>
            <td>{v.get('description', 'N/A')}</td>
            <td>{size_mb:.2f} MB</td>
            <td>{upload_time}</td>
            <td><a href="/vlogs/{filename}">下載</a></td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vlogs List</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #FF5722; color: white; }}
            a {{ color: #2196F3; text-decoration: none; }}
            .action-buttons {{
                margin: 20px 0;
                padding: 15px;
                background: #f5f5f5;
                border-radius: 8px;
            }}
            .btn {{
                display: inline-block;
                padding: 10px 20px;
                margin: 5px;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                border: none;
                cursor: pointer;
                font-size: 14px;
            }}
            .btn-primary {{ background-color: #4CAF50; }}
            .btn-primary:hover {{ background-color: #45a049; }}
            .btn-secondary {{ background-color: #2196F3; }}
            .btn-secondary:hover {{ background-color: #0b7dda; }}
            .btn-danger {{ background-color: #f44336; }}
            .btn-danger:hover {{ background-color: #da190b; }}
        </style>
    </head>
    <body>
        <h1>影片列表</h1>
        <p><a href="/export">← 返回</a></p>
        
        <div class="action-buttons">
            <a href="/export/vlogs/download-all" class="btn btn-danger">📦 一鍵下載全部影片 (ZIP)</a>
            <button class="btn btn-primary" onclick="selectAll()">✅ 全選</button>
            <button class="btn btn-secondary" onclick="deselectAll()">❌ 取消全選</button>
            <button class="btn btn-primary" onclick="downloadSelected()">📥 下載選取的影片</button>
        </div>
        
        <table>
            <tr>
                <th style="width: 50px;">選擇</th>
                <th>檔名</th>
                <th>描述</th>
                <th>大小</th>
                <th>上傳時間 (台灣時區)</th>
                <th>操作</th>
            </tr>
            {rows}
        </table>
        
        <script>
            function selectAll() {{
                document.querySelectorAll('.video-checkbox').forEach(cb => cb.checked = true);
            }}
            
            function deselectAll() {{
                document.querySelectorAll('.video-checkbox').forEach(cb => cb.checked = false);
            }}
            
            function downloadSelected() {{
                const selected = Array.from(document.querySelectorAll('.video-checkbox:checked'))
                    .map(cb => cb.value);
                
                if (selected.length === 0) {{
                    alert('請先選擇要下載的影片！');
                    return;
                }}
                
                // 建立下載連結
                const filenames = selected.join(',');
                window.location.href = `/export/vlogs/download-multiple?filenames=${{filenames}}`;
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/vlogs/{filename}")
async def download_vlog(filename: str):
    """下載特定影片"""
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(filepath)

@app.get("/export/vlogs/download-all")
async def download_all_vlogs():
    """一鍵下載所有影片為 ZIP 檔案"""
    vlogs = await app.mongodb["vlogs"].find().to_list(1000)
    
    # 建立記憶體中的 ZIP 檔案
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for v in vlogs:
            filename = v.get('filename')
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            if os.path.exists(filepath):
                # 使用原始檔名
                original_filename = v.get('original_filename', filename)
                zip_file.write(filepath, original_filename)
    
    # 產生 ZIP 檔名
    zip_filename = f"emogo_vlogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    # 返回 ZIP 檔案
    zip_buffer.seek(0)
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={zip_filename}"
        }
    )

@app.get("/export/vlogs/download-multiple")
async def download_multiple_vlogs(filenames: str):
    """下載選中的多個影片為 ZIP 檔案"""
    # 解析檔名列表
    filename_list = filenames.split(',')
    
    # 建立記憶體中的 ZIP 檔案
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in filename_list:
            filepath = os.path.join(UPLOAD_DIR, filename)
            
            if os.path.exists(filepath):
                # 從資料庫取得原始檔名
                vlog = await app.mongodb["vlogs"].find_one({"filename": filename})
                original_filename = vlog.get('original_filename', filename) if vlog else filename
                zip_file.write(filepath, original_filename)
    
    # 產生 ZIP 檔名
    zip_filename = f"emogo_vlogs_selected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    # 返回 ZIP 檔案
    zip_buffer.seek(0)
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={zip_filename}"
        }
    )

@app.get("/export/all")
async def export_all():
    """在網頁上查看所有資料（JSON 格式）- 時間已轉換為台灣時區"""
    sentiments = await app.mongodb["sentiments"].find().to_list(1000)
    gps_data = await app.mongodb["gps_coordinates"].find().to_list(1000)
    vlogs = await app.mongodb["vlogs"].find().to_list(1000)
    
    # 轉換資料格式 - 所有時間轉換為台灣時區
    for s in sentiments:
        s["_id"] = str(s["_id"])
        if "timestamp" in s and s["timestamp"]:
            # 轉換為台灣時間
            dt = s["timestamp"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            s["timestamp"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    for g in gps_data:
        g["_id"] = str(g["_id"])
        if "timestamp" in g and g["timestamp"]:
            # 轉換為台灣時間
            dt = g["timestamp"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            g["timestamp"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
        # 移除 accuracy 欄位
        g.pop("accuracy", None)
    
    for v in vlogs:
        v["_id"] = str(v["_id"])
        if "upload_time" in v and v["upload_time"]:
            # 轉換為台灣時間
            dt = v["upload_time"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            v["upload_time"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # 返回 JSON（在網頁上顯示）
    return JSONResponse(content={
        "sentiments": sentiments,
        "gps_coordinates": gps_data,
        "vlogs": vlogs,
        "export_time": datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Taipei (UTC+8)",
        "note": "所有時間已轉換為台灣時區 (UTC+8)",
        "total_records": {
            "sentiments": len(sentiments),
            "gps": len(gps_data),
            "vlogs": len(vlogs)
        }
    })

@app.post("/clear_all_data")
async def clear_all_data():
    """刪除 sentiments、gps_coordinates、vlogs 三個 collection 的所有資料"""
    deleted_counts = {}
    for collection in ["sentiments", "gps_coordinates", "vlogs"]:
        result = await app.mongodb[collection].delete_many({})
        deleted_counts[collection] = result.deleted_count
    return {"success": True, "deleted_counts": deleted_counts}

@app.get("/export/all/download")
async def download_all():
    """下載所有資料為 JSON 檔案 - 時間已轉換為台灣時區"""
    sentiments = await app.mongodb["sentiments"].find().to_list(1000)
    gps_data = await app.mongodb["gps_coordinates"].find().to_list(1000)
    vlogs = await app.mongodb["vlogs"].find().to_list(1000)
    
    # 轉換資料格式 - 所有時間轉換為台灣時區
    for s in sentiments:
        s["_id"] = str(s["_id"])
        if "timestamp" in s and s["timestamp"]:
            # 轉換為台灣時間
            dt = s["timestamp"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            s["timestamp"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    for g in gps_data:
        g["_id"] = str(g["_id"])
        if "timestamp" in g and g["timestamp"]:
            # 轉換為台灣時間
            dt = g["timestamp"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            g["timestamp"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
        # 移除 accuracy 欄位
        g.pop("accuracy", None)
    
    for v in vlogs:
        v["_id"] = str(v["_id"])
        if "upload_time" in v and v["upload_time"]:
            # 轉換為台灣時間
            dt = v["upload_time"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            v["upload_time"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # 建立 JSON 內容
    data = {
        "sentiments": sentiments,
        "gps_coordinates": gps_data,
        "vlogs": vlogs,
        "export_time": datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Taipei (UTC+8)",
        "note": "所有時間已轉換為台灣時區 (UTC+8)",
        "total_records": {
            "sentiments": len(sentiments),
            "gps": len(gps_data),
            "vlogs": len(vlogs)
        }
    }
    
    # 產生檔名（包含日期時間）
    filename = f"emogo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 返回為下載檔案
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)