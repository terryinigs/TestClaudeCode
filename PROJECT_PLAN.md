# YouTube 歌回自動剪輯系統 - 專案規劃書

## 專案概述

### 背景
VTuber 直播後常會上傳完整直播檔案，粉絲會在留言區標註歌曲演唱時間。本專案旨在開發自動化系統，根據留言區時間戳自動剪輯出歌曲片段。

### 目標使用者
- VTuber 粉絲群體
- 歌回剪輯愛好者
- 內容創作者

---

## 一、產品經理（PM）視角

### 1.1 核心功能需求

#### MVP (最小可行產品)
1. **影片監控**
   - 支援新增 YouTube 頻道或播放清單
   - 自動偵測新上傳的直播檔案
   - 手動輸入單個影片 URL

2. **留言解析**
   - 自動掃描影片留言區
   - 識別時間戳格式（如：`12:34 - 歌名` 或 `1:23:45 歌曲標題`）
   - 支援多種常見時間戳格式
   - 過濾和驗證有效留言

3. **影片剪輯**
   - 根據時間戳自動下載並剪輯
   - 支援設定片段前後緩衝時間（如前後各 2 秒）
   - 輸出標準格式（MP4, 720p/1080p）
   - 自動命名：`[頻道名]_[日期]_[歌名].mp4`

4. **結果管理**
   - 本機儲存剪輯片段
   - 顯示處理狀態和進度
   - 錯誤日誌和通知

#### 進階功能（Phase 2）
- 留言投票系統（優先處理高讚留言）
- 批次處理多個影片
- 自動上傳到雲端儲存
- Web 介面或 GUI
- 定時任務排程
- 去重機制（避免重複剪輯）

### 1.2 使用者場景

**場景 1：手動單影片處理**
```
1. 使用者輸入 YouTube 影片 URL
2. 系統掃描留言區獲取時間戳
3. 使用者確認要剪輯的片段
4. 系統自動下載和剪輯
5. 輸出到指定資料夾
```

**場景 2：頻道自動監控**
```
1. 使用者設定監控的頻道清單
2. 系統定期檢查新影片（每小時/每天）
3. 發現新直播檔案後自動處理
4. 完成後發送通知
```

### 1.3 成功指標
- 時間戳識別準確率 > 90%
- 單個影片處理時間 < 30 分鐘（取決於片段數量）
- 系統穩定性：連續運行 7 天無崩潰
- 使用者操作步驟 < 5 步完成設定

### 1.4 風險與限制
- YouTube API 配額限制（每天 10,000 units）
- 版權和使用政策合規性
- 網路頻寬需求（下載大影片）
- 儲存空間管理

---

## 二、後端工程師（Backend）視角

### 2.1 系統架構

```
┌─────────────────┐
│  使用者介面層    │
│  (CLI/Web)      │
└────────┬────────┘
         │
┌────────▼────────────────────────────────┐
│         應用服務層                       │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ 影片管理 │  │ 留言解析 │  │ 剪輯器 │ │
│  └──────────┘  └──────────┘  └────────┘ │
└────────┬────────────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│         基礎設施層                       │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │YouTube API│  │  FFmpeg  │  │ 儲存   │ │
│  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────┘
```

### 2.2 技術棧選型

#### 程式語言
**推薦：Python 3.10+**
- 理由：豐富的影片處理函式庫、YouTube API 客戶端成熟、快速原型開發

**備選：Node.js / Go**
- Node.js：適合 Web 服務整合
- Go：高效能、適合長時間運行服務

#### 核心相依函式庫

```python
# YouTube 互動
google-api-python-client  # YouTube Data API v3
google-auth-oauthlib      # 認證

# 影片下載
yt-dlp                    # YouTube 影片下載（ffmpeg wrapper）

# 影片處理
ffmpeg-python            # FFmpeg Python 綁定

# 資料處理
pydantic                 # 資料驗證
sqlalchemy               # 資料庫 ORM（可選）

# 任務排程
celery                   # 非同步任務佇列（進階）
apscheduler              # 定時任務

# 其他
requests                 # HTTP 請求
python-dotenv            # 環境變數管理
loguru                   # 日誌
```

### 2.3 核心模組設計

#### 2.3.1 YouTube 服務模組
```python
class YouTubeService:
    """
    負責與 YouTube API 互動
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = build('youtube', 'v3', developerKey=api_key)

    def get_video_info(self, video_id: str) -> VideoInfo:
        """獲取影片元資料"""
        pass

    def get_comments(self, video_id: str, max_results: int = 100) -> List[Comment]:
        """獲取影片留言"""
        pass

    def get_channel_videos(self, channel_id: str) -> List[VideoInfo]:
        """獲取頻道最新影片"""
        pass
```

**API 配額優化策略：**
- 快取影片資訊（24小時）
- 留言增量獲取（只獲取新留言）
- 批次請求減少 API 呼叫

#### 2.3.2 留言解析模組
```python
class CommentParser:
    """
    解析留言中的時間戳和歌曲資訊
    """
    # 支援的時間格式
    PATTERNS = [
        r'(\d{1,2}):(\d{2}):(\d{2})\s*[-–—]\s*(.+)',  # 1:23:45 - 歌名
        r'(\d{1,2}):(\d{2})\s*[-–—]\s*(.+)',          # 12:34 - 歌名
        r'(\d{1,2}):(\d{2}):(\d{2})\s+(.+)',          # 1:23:45 歌名
        r'(\d{1,2}):(\d{2})\s+(.+)',                  # 12:34 歌名
    ]

    def parse_comment(self, text: str) -> Optional[SongTimestamp]:
        """解析單條留言"""
        pass

    def extract_all_timestamps(self, comments: List[Comment]) -> List[SongTimestamp]:
        """批次提取時間戳"""
        pass

    def validate_timestamp(self, timestamp: SongTimestamp, video_duration: int) -> bool:
        """驗證時間戳有效性"""
        pass
```

**資料模型：**
```python
from pydantic import BaseModel

class SongTimestamp(BaseModel):
    start_time: int          # 秒數
    end_time: Optional[int]  # 如果留言包含結束時間
    song_name: str
    original_comment: str
    comment_likes: int       # 用於排序
    comment_author: str
```

#### 2.3.3 影片剪輯模組
```python
class VideoClipper:
    """
    處理影片下載和剪輯
    """
    def __init__(self, output_dir: str, buffer_seconds: int = 2):
        self.output_dir = output_dir
        self.buffer_seconds = buffer_seconds

    def download_video(self, video_url: str) -> str:
        """下載影片到臨時目錄"""
        # 使用 yt-dlp
        pass

    def clip_segment(self,
                     video_path: str,
                     start: int,
                     end: int,
                     output_name: str) -> str:
        """剪輯影片片段"""
        # 使用 FFmpeg
        # ffmpeg -i input.mp4 -ss START -to END -c copy output.mp4
        pass

    def batch_clip(self, video_url: str, timestamps: List[SongTimestamp]):
        """批次剪輯"""
        pass
```

**FFmpeg 命令優化：**
```bash
# 快速剪輯（stream copy，不重新編碼）
ffmpeg -ss START -i input.mp4 -to DURATION -c copy -avoid_negative_ts 1 output.mp4

# 精確剪輯（重新編碼，速度較慢但精確）
ffmpeg -i input.mp4 -ss START -to END -c:v libx264 -c:a aac output.mp4
```

### 2.4 資料庫設計（可選）

如果需要持久化和任務管理，建議使用 SQLite（簡單）或 PostgreSQL（正式環境）

```sql
-- 影片表
CREATE TABLE videos (
    id INTEGER PRIMARY KEY,
    video_id VARCHAR(20) UNIQUE,
    title TEXT,
    channel_name VARCHAR(255),
    duration INTEGER,
    published_at TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 歌曲片段表
CREATE TABLE song_clips (
    id INTEGER PRIMARY KEY,
    video_id VARCHAR(20),
    song_name TEXT,
    start_time INTEGER,
    end_time INTEGER,
    file_path TEXT,
    comment_text TEXT,
    status VARCHAR(20), -- pending, processing, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

-- 監控頻道表
CREATE TABLE monitored_channels (
    id INTEGER PRIMARY KEY,
    channel_id VARCHAR(50) UNIQUE,
    channel_name VARCHAR(255),
    last_check TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);
```

### 2.5 效能考量

#### 2.5.1 非同步處理
```python
# 使用非同步下載和剪輯
import asyncio

async def process_video_async(video_id: str):
    # 1. 獲取留言（I/O bound）
    comments = await fetch_comments_async(video_id)

    # 2. 解析時間戳（CPU bound）
    timestamps = parse_timestamps(comments)

    # 3. 下載影片（I/O bound）
    video_path = await download_video_async(video_id)

    # 4. 並行剪輯多個片段
    tasks = [clip_segment_async(video_path, ts) for ts in timestamps]
    await asyncio.gather(*tasks)
```

#### 2.5.2 儲存優化
- 下載最低品質滿足需求的影片（節省頻寬和儲存）
- 剪輯完成後刪除原影片
- 實作 LRU 快取策略

#### 2.5.3 錯誤處理
```python
class VideoProcessingError(Exception):
    pass

def retry_on_failure(max_retries=3):
    """裝飾器：失敗重試"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_retries - 1:
                        raise
                    time.sleep(2 ** i)  # 指數退避
        return wrapper
    return decorator
```

### 2.6 API 設計（如果提供 Web 服務）

```python
# RESTful API 端點

POST /api/videos
# 提交新影片處理任務
{
    "video_url": "https://youtube.com/watch?v=xxx",
    "auto_detect_timestamps": true,
    "manual_timestamps": [...]  # 可選
}

GET /api/videos/{video_id}
# 獲取處理狀態

GET /api/videos/{video_id}/clips
# 獲取剪輯清單

POST /api/channels
# 新增監控頻道

GET /api/jobs/{job_id}
# 查詢任務狀態
```

---

## 三、前端工程師（Frontend）視角

### 3.1 介面方案

#### 方案 A：命令列工具 (CLI) - MVP 推薦
```bash
# 單影片處理
youtube-clipper process https://youtube.com/watch?v=xxx

# 監控頻道
youtube-clipper monitor --channel UC123456 --interval 1h

# 設定
youtube-clipper config --api-key YOUR_KEY --output-dir ./clips
```

**優點：**
- 開發快速
- 適合技術使用者
- 易於自動化整合

**技術棧：**
- Python: `click` 或 `typer` 函式庫
- 進度顯示: `tqdm`
- 表格輸出: `rich`

#### 方案 B：Web 介面 - Phase 2
```
技術棧：
- 前端：React / Vue.js / Svelte
- 後端：FastAPI / Flask
- 即時通訊：WebSocket（進度更新）
```

**核心頁面：**
1. **儀表板**
   - 顯示處理中/完成的任務
   - 儲存空間使用情況

2. **新建任務**
   - 輸入影片 URL
   - 預覽偵測到的時間戳
   - 編輯/刪除時間戳
   - 開始處理

3. **頻道管理**
   - 新增/刪除監控頻道
   - 查看歷史處理記錄

4. **設定**
   - API 設定
   - 輸出格式設定
   - 通知設定

### 3.2 使用者體驗設計

#### 關鍵互動流程
```
1. 輸入影片 URL
   ↓
2. [載入動畫] 正在獲取留言...
   ↓
3. 顯示偵測到的時間戳清單
   - 可編輯/刪除
   - 顯示留言原文
   ↓
4. 點擊「開始剪輯」
   ↓
5. [進度條] 下載中... 45%
   [進度條] 剪輯中... 2/5 完成
   ↓
6. 完成提示 + 下載連結
```

#### 錯誤處理 UI
- 友善的錯誤提示（而非技術錯誤訊息）
- 提供解決建議
- 重試按鈕

---

## 四、技術實作路線圖

### Phase 1: MVP (2-3 週)
**Week 1:**
- [ ] YouTube API 整合和測試
- [ ] 留言解析邏輯開發
- [ ] 時間戳提取和驗證

**Week 2:**
- [ ] 影片下載功能（yt-dlp）
- [ ] FFmpeg 剪輯功能
- [ ] 基本 CLI 工具

**Week 3:**
- [ ] 錯誤處理和日誌
- [ ] 單元測試
- [ ] 文件和使用說明

### Phase 2: 增強功能 (3-4 週)
- [ ] 批次處理
- [ ] 資料庫持久化
- [ ] 頻道監控和排程
- [ ] Web 介面開發

### Phase 3: 優化和擴充
- [ ] 效能優化
- [ ] 雲端儲存整合
- [ ] 使用者認證系統
- [ ] 行動端適配

---

## 五、開發環境設定

### 5.1 必需軟體
```bash
# Python 3.10+
python --version

# FFmpeg
sudo apt install ffmpeg  # Linux
brew install ffmpeg      # macOS

# 專案相依
pip install -r requirements.txt
```

### 5.2 YouTube API 設定
```
1. 造訪 Google Cloud Console
2. 建立新專案
3. 啟用 YouTube Data API v3
4. 建立 API 金鑰
5. 設定到 .env 檔案
```

### 5.3 專案結構
```
youtube-song-clipper/
├── src/
│   ├── api/              # YouTube API 互動
│   ├── parser/           # 留言解析
│   ├── clipper/          # 影片剪輯
│   ├── storage/          # 儲存管理
│   └── utils/            # 工具函數
├── tests/                # 單元測試
├── cli/                  # 命令列工具
├── web/                  # Web 介面（可選）
├── config/               # 設定檔
├── docs/                 # 文件
├── requirements.txt
├── .env.example
└── README.md
```

---

## 六、成本估算

### 6.1 開發成本
- MVP 開發：約 80-120 小時
- 測試和優化：約 40 小時
- 文件撰寫：約 20 小時

### 6.2 營運成本
- YouTube API：免費（配額內）
- 雲端伺服器：$5-20/月（如需託管）
- 雲端儲存：按使用量計費
- 網域名稱：$10/年（如需 Web 服務）

### 6.3 配額限制
```
YouTube Data API v3 每日配額：10,000 units

操作成本：
- 獲取影片詳情：1 unit
- 獲取留言：1 unit（每頁）
- 搜尋：100 units

估算：
每天可處理約 100 個影片（假設每個影片 100 條留言）
```

---

## 七、風險評估與應對

### 7.1 技術風險

| 風險 | 影響 | 機率 | 應對措施 |
|------|------|------|----------|
| API 配額超限 | 高 | 中 | 實作快取、批次請求、使用者自帶 API Key |
| 時間戳格式多樣 | 中 | 高 | 使用多個正規表達式、機器學習輔助 |
| 影片下載失敗 | 中 | 中 | 重試機制、降級策略 |
| FFmpeg 剪輯錯誤 | 中 | 低 | 參數驗證、錯誤捕獲 |

### 7.2 法律風險
- **版權問題**：明確標註僅供個人學習使用
- **YouTube ToS**：遵守服務條款，避免大規模爬取
- **使用者協議**：新增免責聲明

### 7.3 營運風險
- 儲存空間快速增長 → 實作自動清理機制
- 網路頻寬限制 → 限制並行下載數

---

## 八、成功案例參考

### 類似專案
1. **yt-dlp**：YouTube 下載工具（可借鑑其下載邏輯）
2. **youtube-dl-server**：Web 介面封裝
3. **Clipper.gg**：遊戲剪輯工具（UI/UX 參考）

---

## 九、下一步行動

### 立即執行
1. ✅ 閱讀並確認此規劃書
2. [ ] PM 確認功能優先順序
3. [ ] Backend 選定技術棧
4. [ ] Frontend 確定介面方案（CLI vs Web）

### 本週任務
1. [ ] 申請 YouTube API 金鑰
2. [ ] 建置開發環境
3. [ ] 實作時間戳解析 POC（Proof of Concept）
4. [ ] 測試 yt-dlp + FFmpeg 剪輯流程

### 需要決策的問題
1. **目標使用者群體**：技術使用者 vs 一般使用者？
2. **部署方式**：本機工具 vs 雲端服務？
3. **商業模式**：開源免費 vs 付費服務？
4. **初始支援語言**：僅中文留言 vs 多語言？

---

## 十、附錄

### A. 技術詞彙表
- **VTuber**：Virtual YouTuber，虛擬主播
- **歌回**：唱歌直播的錄播
- **時間戳**：影片中特定時間點標記（如 12:34）
- **FFmpeg**：開源影片處理工具
- **yt-dlp**：YouTube 影片下載工具

### B. 參考資源
- YouTube Data API v3 文件：https://developers.google.com/youtube/v3
- FFmpeg 文件：https://ffmpeg.org/documentation.html
- yt-dlp GitHub：https://github.com/yt-dlp/yt-dlp

---

**文件版本**：v1.1
**建立日期**：2025-10-21
**最後更新**：2025-10-21
**負責人**：待定
**狀態**：待審核
