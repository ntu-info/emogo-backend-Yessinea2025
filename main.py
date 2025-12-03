from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
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

app = FastAPI(title="EmoGo Backend API with GridFS")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    tw_time = dt.astimezone(TW_TZ)
    return tw_time.strftime("%Y-%m-%d %H:%M:%S")

# MongoDB 連接會在 startup 事件中初始化
@app.on_event("startup")
async def startup_db_client():
    """啟動時連接 MongoDB 和 GridFS"""
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    app.mongodb = app.mongodb_client[DB_NAME]
    # 🆕 初始化 GridFS
    app.fs = AsyncIOMotorGridFSBucket(app.mongodb)
    print(f"✅ Connected to MongoDB: {DB_NAME}")
    print(f"✅ GridFS initialized for video storage")

@app.on_event("shutdown")
async def shutdown_db_client():
    """關閉時斷開 MongoDB 連接"""
    app.mongodb_client.close()
    print("❌ Disconnected from MongoDB")

# Pydantic models
class Sentiment(BaseModel):
    emotion: str
    score: int
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
        "message": "Welcome to EmoGo Backend API with GridFS",
        "storage": "Videos stored permanently in MongoDB GridFS",
        "endpoints": {
            "POST /sentiments": "上傳情緒資料",
            "POST /gps": "上傳 GPS 座標",
            "POST /vlogs": "上傳影片（GridFS 永久儲存）",
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
    """
    🆕 接收影片檔案並上傳到 MongoDB GridFS（永久儲存）
    """
    try:
        # 產生唯一檔名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        
        # 讀取檔案內容
        content = await file.read()
        file_size = len(content)
        
        # 🆕 上傳到 GridFS
        grid_in = app.fs.open_upload_stream(
            filename,
            metadata={
                "original_filename": file.filename,
                "content_type": file.content_type or "video/mp4",
                "description": description,
                "upload_time": datetime.now(),
                "size": file_size
            }
        )
        
        await grid_in.write(content)
        await grid_in.close()
        
        file_id = grid_in._id
        
        # 將影片資訊存入 vlogs collection（保持原有結構，方便查詢）
        vlog_info = {
            "file_id": str(file_id),  # 🆕 GridFS 文件 ID
            "filename": filename,
            "original_filename": file.filename,
            "description": description,
            "upload_time": datetime.now(),
            "size": file_size,
            "storage": "gridfs"  # 🆕 標記儲存方式
        }
        
        result = await app.mongodb["vlogs"].insert_one(vlog_info)
        
        return {
            "message": "Vlog uploaded to GridFS (permanent storage)",
            "id": str(result.inserted_id),
            "file_id": str(file_id),
            "filename": filename,
            "storage": "MongoDB GridFS"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/vlogs/{filename}")
async def download_vlog(filename: str):
    """
    🆕 從 MongoDB GridFS 下載影片（永久可用）
    """
    try:
        # 從資料庫取得影片資訊
        vlog = await app.mongodb["vlogs"].find_one({"filename": filename})
        
        if not vlog:
            raise HTTPException(status_code=404, detail="Video not found in database")
        
        # 🆕 從 GridFS 取得影片
        try:
            file_id = ObjectId(vlog["file_id"])
            
            # 開啟 GridFS 檔案流
            grid_out = await app.fs.open_download_stream(file_id)
            
            # 讀取檔案內容
            contents = await grid_out.read()
            
            # 返回影片檔案
            return Response(
                content=contents,
                media_type="video/mp4",
                headers={
                    "Content-Disposition": f"attachment; filename={vlog.get('original_filename', filename)}"
                }
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=404, 
                detail=f"Video file not found in GridFS: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading video: {str(e)}")

@app.get("/export", response_class=HTMLResponse)
async def export_page():
    """資料匯出頁面"""
    
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
            .info-box {{
                background-color: #e3f2fd;
                border-left: 4px solid #2196F3;
                padding: 12px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            .info-text {{
                color: #1565c0;
                font-size: 14px;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <h1>📊 EmoGo 資料中心</h1>
        
        <div class="info-box">
            <p class="info-text">
                ✨ <strong>永久儲存：</strong> 所有影片使用 MongoDB GridFS 永久保存，不受伺服器重啟影響！
            </p>
        </div>
        
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
            <h2>🎥 影片日記 (Vlogs - GridFS 永久儲存)</h2>
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
            if (!confirm("⚠️ 確定要清空所有資料嗎？\\n\\n此操作將刪除：\\n• 所有情緒記錄\\n• 所有 GPS 座標\\n• 所有影片日記（包括 GridFS）\\n\\n此操作無法復原！")) {{
                return;
            }}
            
            if (!confirm("🚨 最後確認：真的要刪除所有資料嗎？")) {{
                return;
            }}

            try {{
                const response = await fetch("/clear_all_data", {{
                    method: "POST"
                }});

                if (response.ok) {{
                    const result = await response.json();
                    alert(`✅ 所有資料已清空！\\n\\n刪除統計：\\n• 情緒資料：${{result.deleted_counts.sentiments}} 筆\\n• GPS 座標：${{result.deleted_counts.gps_coordinates}} 筆\\n• 影片日記：${{result.deleted_counts.vlogs}} 筆\\n• GridFS 檔案：${{result.deleted_counts.gridfs_files}} 個`);
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

@app.get("/export/sentiments/csv")
async def export_sentiments_csv():
    """下載情緒資料為 CSV 檔案"""
    sentiments = await app.mongodb["sentiments"].find().to_list(1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['emotion', 'score', 'note', 'timestamp'])
    
    for s in sentiments:
        timestamp = to_tw_time(s.get("timestamp"))
        writer.writerow([
            s.get('emotion', ''),
            s.get('score', ''),
            s.get('note', ''),
            timestamp
        ])
    
    filename = f"sentiments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_content = '\ufeff' + output.getvalue()
    
    return Response(
        content=csv_content.encode('utf-8'),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/export/sentiments/preview", response_class=HTMLResponse)
async def preview_sentiments():
    """預覽情緒資料"""
    sentiments = await app.mongodb["sentiments"].find().to_list(100)
    
    rows = ""
    for s in sentiments:
        timestamp = to_tw_time(s.get("timestamp"))
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

@app.get("/export/gps/csv")
async def export_gps_csv():
    """下載 GPS 資料為 CSV 檔案"""
    gps_data = await app.mongodb["gps_coordinates"].find().to_list(1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['latitude', 'longitude', 'timestamp'])
    
    for g in gps_data:
        timestamp = to_tw_time(g.get("timestamp"))
        writer.writerow([
            g.get('latitude', ''),
            g.get('longitude', ''),
            timestamp
        ])
    
    filename = f"gps_coordinates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_content = '\ufeff' + output.getvalue()
    
    return Response(
        content=csv_content.encode('utf-8'),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/export/gps/preview", response_class=HTMLResponse)
async def preview_gps():
    """預覽 GPS 資料"""
    gps_data = await app.mongodb["gps_coordinates"].find().to_list(100)
    
    rows = ""
    for g in gps_data:
        timestamp = to_tw_time(g.get("timestamp"))
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
    """列出所有影片（從 GridFS 永久儲存）"""
    vlogs = await app.mongodb["vlogs"].find().to_list(1000)
    
    rows = ""
    for v in vlogs:
        upload_time = to_tw_time(v.get("upload_time"))
        size_mb = v.get("size", 0) / (1024 * 1024)
        filename = v.get('filename', '')
        storage = v.get('storage', 'gridfs')
        
        rows += f"""
        <tr>
            <td><input type="checkbox" class="video-checkbox" value="{filename}"></td>
            <td>{v.get('original_filename', 'N/A')}</td>
            <td>{v.get('description', 'N/A')}</td>
            <td>{size_mb:.2f} MB</td>
            <td>{upload_time}</td>
            <td><span style="color: green;">✅ GridFS</span></td>
            <td><a href="/vlogs/{filename}">下載</a></td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vlogs List (GridFS)</title>
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
            .info-box {{
                background-color: #e3f2fd;
                border-left: 4px solid #2196F3;
                padding: 12px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .info-text {{
                color: #1565c0;
                font-size: 14px;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <h1>影片列表 (GridFS 永久儲存)</h1>
        <p><a href="/export">← 返回</a></p>
        
        <div class="info-box">
            <p class="info-text">
                ✨ <strong>永久儲存：</strong> 所有影片使用 MongoDB GridFS 永久保存<br>
                ✅ 不受伺服器重啟影響<br>
                ✅ 影片下載功能永久可用
            </p>
        </div>
        
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
                <th>儲存方式</th>
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
                
                const filenames = selected.join(',');
                window.location.href = `/export/vlogs/download-multiple?filenames=${{filenames}}`;
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/export/vlogs/download-all")
async def download_all_vlogs():
    """🆕 一鍵下載所有影片為 ZIP 檔案（從 GridFS）"""
    vlogs = await app.mongodb["vlogs"].find().to_list(1000)
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for v in vlogs:
            try:
                file_id = ObjectId(v["file_id"])
                grid_out = await app.fs.open_download_stream(file_id)
                contents = await grid_out.read()
                
                original_filename = v.get('original_filename', v.get('filename'))
                zip_file.writestr(original_filename, contents)
            except Exception as e:
                print(f"Error adding {v.get('filename')} to ZIP: {e}")
                continue
    
    zip_filename = f"emogo_vlogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    zip_buffer.seek(0)
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )

@app.get("/export/vlogs/download-multiple")
async def download_multiple_vlogs(filenames: str):
    """🆕 下載選中的多個影片為 ZIP 檔案（從 GridFS）"""
    filename_list = filenames.split(',')
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in filename_list:
            try:
                vlog = await app.mongodb["vlogs"].find_one({"filename": filename})
                if not vlog:
                    continue
                    
                file_id = ObjectId(vlog["file_id"])
                grid_out = await app.fs.open_download_stream(file_id)
                contents = await grid_out.read()
                
                original_filename = vlog.get('original_filename', filename)
                zip_file.writestr(original_filename, contents)
            except Exception as e:
                print(f"Error adding {filename} to ZIP: {e}")
                continue
    
    zip_filename = f"emogo_vlogs_selected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    zip_buffer.seek(0)
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )

@app.get("/export/all")
async def export_all():
    """在網頁上查看所有資料（JSON 格式）"""
    sentiments = await app.mongodb["sentiments"].find().to_list(1000)
    gps_data = await app.mongodb["gps_coordinates"].find().to_list(1000)
    vlogs = await app.mongodb["vlogs"].find().to_list(1000)
    
    for s in sentiments:
        s["_id"] = str(s["_id"])
        if "timestamp" in s and s["timestamp"]:
            dt = s["timestamp"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            s["timestamp"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    for g in gps_data:
        g["_id"] = str(g["_id"])
        if "timestamp" in g and g["timestamp"]:
            dt = g["timestamp"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            g["timestamp"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
        g.pop("accuracy", None)
    
    for v in vlogs:
        v["_id"] = str(v["_id"])
        v["file_id"] = str(v.get("file_id", ""))
        if "upload_time" in v and v["upload_time"]:
            dt = v["upload_time"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            v["upload_time"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    return JSONResponse(content={
        "sentiments": sentiments,
        "gps_coordinates": gps_data,
        "vlogs": vlogs,
        "export_time": datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Taipei (UTC+8)",
        "storage": "Videos stored in MongoDB GridFS (permanent)",
        "note": "所有時間已轉換為台灣時區 (UTC+8)",
        "total_records": {
            "sentiments": len(sentiments),
            "gps": len(gps_data),
            "vlogs": len(vlogs)
        }
    })

@app.post("/clear_all_data")
async def clear_all_data():
    """🆕 刪除所有資料（包括 GridFS 檔案）"""
    deleted_counts = {}
    
    # 刪除 collections
    for collection in ["sentiments", "gps_coordinates", "vlogs"]:
        result = await app.mongodb[collection].delete_many({})
        deleted_counts[collection] = result.deleted_count
    
    # 🆕 刪除所有 GridFS 檔案
    try:
        cursor = app.fs.find()
        gridfs_count = 0
        async for grid_file in cursor:
            await app.fs.delete(grid_file._id)
            gridfs_count += 1
        deleted_counts["gridfs_files"] = gridfs_count
    except Exception as e:
        print(f"Error clearing GridFS: {e}")
        deleted_counts["gridfs_files"] = 0
    
    return {"success": True, "deleted_counts": deleted_counts}

@app.get("/export/all/download")
async def download_all():
    """下載所有資料為 JSON 檔案"""
    sentiments = await app.mongodb["sentiments"].find().to_list(1000)
    gps_data = await app.mongodb["gps_coordinates"].find().to_list(1000)
    vlogs = await app.mongodb["vlogs"].find().to_list(1000)
    
    for s in sentiments:
        s["_id"] = str(s["_id"])
        if "timestamp" in s and s["timestamp"]:
            dt = s["timestamp"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            s["timestamp"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    for g in gps_data:
        g["_id"] = str(g["_id"])
        if "timestamp" in g and g["timestamp"]:
            dt = g["timestamp"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            g["timestamp"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
        g.pop("accuracy", None)
    
    for v in vlogs:
        v["_id"] = str(v["_id"])
        v["file_id"] = str(v.get("file_id", ""))
        if "upload_time" in v and v["upload_time"]:
            dt = v["upload_time"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            tw_dt = dt.astimezone(TW_TZ)
            v["upload_time"] = tw_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    data = {
        "sentiments": sentiments,
        "gps_coordinates": gps_data,
        "vlogs": vlogs,
        "export_time": datetime.now(TW_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Taipei (UTC+8)",
        "storage": "Videos stored in MongoDB GridFS (permanent)",
        "note": "所有時間已轉換為台灣時區 (UTC+8)",
        "total_records": {
            "sentiments": len(sentiments),
            "gps": len(gps_data),
            "vlogs": len(vlogs)
        }
    }
    
    filename = f"emogo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)