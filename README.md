# YouTube 歌回自動剪輯器

自動從 YouTube 影片留言區解析歌曲時間戳，並剪輯出個別歌曲片段的 CLI 工具。

## 功能特色

- ✅ 自動掃描 YouTube 影片留言區
- ✅ 智慧識別多種時間戳格式
- ✅ 批次下載並剪輯歌曲片段
- ✅ 支援自訂緩衝時間和影片品質
- ✅ 精美的命令列介面（使用 Rich）
- ✅ 完整的錯誤處理和日誌記錄

## 支援的時間戳格式

程式能自動識別以下常見的時間戳格式：

```
12:34 - 歌名
12:34 歌名
1:23:45 - 歌名
[12:34] 歌名
12:34~15:20 歌名（包含結束時間）
```

## 安裝步驟

### 1. 系統需求

- Python 3.10 或更高版本
- FFmpeg（用於影片剪輯）

### 2. 安裝 FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
下載並安裝 [FFmpeg](https://ffmpeg.org/download.html)

### 3. 安裝 Python 套件

```bash
# 克隆專案（或直接下載）
git clone <repository-url>
cd youtube-song-clipper

# 安裝相依套件
pip install -r requirements.txt
```

## 設定

### 1. 申請 YouTube API 金鑰

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇現有專案
3. 啟用 **YouTube Data API v3**
4. 建立憑證 → API 金鑰
5. 複製 API 金鑰

### 2. 設定環境變數

複製 `.env.example` 為 `.env`：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，填入您的 API 金鑰：

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
OUTPUT_DIR=./output
TEMP_DIR=./temp
CLIP_BUFFER_SECONDS=2
VIDEO_QUALITY=720p
LOG_LEVEL=INFO
```

## 使用方法

### 基本用法

```bash
python cli/main.py process "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 進階選項

```bash
# 指定輸出目錄
python cli/main.py process "VIDEO_URL" --output ./my_clips

# 限制獲取的留言數量
python cli/main.py process "VIDEO_URL" --max-comments 50

# 使用不同的 API 金鑰
python cli/main.py process "VIDEO_URL" --api-key YOUR_API_KEY

# 手動確認後再剪輯
python cli/main.py process "VIDEO_URL" --no-auto-clip
```

### 查看設定

```bash
python cli/main.py config --show
```

### 查看版本

```bash
python cli/main.py version
```

## 完整流程範例

```bash
# 1. 設定 API 金鑰（編輯 .env 檔案）
vim .env

# 2. 處理影片
python cli/main.py process "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# 程式會自動：
# ✓ 獲取影片資訊
# ✓ 掃描留言區
# ✓ 解析時間戳
# ✓ 顯示歌曲清單
# ✓ 下載並剪輯每首歌
# ✓ 輸出到 ./output 目錄
```

## 輸出範例

```
步驟 1/4: 獲取影片資訊...
✓ 影片: 【歌回】唱歌直播精華
✓ 頻道: VTuber 頻道
✓ 長度: 7200 秒

步驟 2/4: 獲取影片留言...
✓ 成功獲取 100 則留言

步驟 3/4: 解析歌曲時間戳...
✓ 找到 15 個有效時間戳

                    解析到的歌曲清單
┌──────┬────────────┬─────────────────┬────────┐
│ 序號 │ 時間       │ 歌名            │ 讚數   │
├──────┼────────────┼─────────────────┼────────┤
│ 1    │ 5:23       │ 歌曲名稱 A      │ 156    │
│ 2    │ 12:45      │ 歌曲名稱 B      │ 89     │
│ 3    │ 18:30      │ 歌曲名稱 C      │ 234    │
└──────┴────────────┴─────────────────┴────────┘

步驟 4/4: 剪輯影片片段...

✓ 完成！
成功剪輯 15/15 個片段
輸出目錄: /path/to/output

剪輯完成的檔案：
  • VTuber頻道_歌曲名稱A.mp4 (12.34 MB)
  • VTuber頻道_歌曲名稱B.mp4 (15.67 MB)
  • VTuber頻道_歌曲名稱C.mp4 (18.90 MB)
```

## 專案結構

```
youtube-song-clipper/
├── cli/
│   └── main.py              # CLI 主程式
├── src/
│   ├── api/
│   │   └── youtube_service.py    # YouTube API 服務
│   ├── parser/
│   │   └── comment_parser.py     # 留言解析器
│   ├── clipper/
│   │   └── video_clipper.py      # 影片剪輯器
│   └── utils/
│       ├── models.py             # 資料模型
│       └── config.py             # 設定管理
├── tests/                   # 單元測試（待實作）
├── output/                  # 輸出目錄（自動建立）
├── temp/                    # 臨時檔案（自動建立）
├── requirements.txt         # Python 相依套件
├── .env.example            # 環境變數範例
├── PROJECT_PLAN.md         # 專案規劃文件
└── README.md               # 本檔案
```

## 常見問題

### Q: 程式無法找到時間戳？

**A:** 請確認：
1. 影片留言區是否包含時間戳格式的歌曲清單
2. 時間戳格式是否符合支援的格式（見上方「支援的時間戳格式」）
3. 留言是否為公開可見

### Q: YouTube API 配額不足？

**A:** YouTube Data API v3 每天有 10,000 units 的免費配額。如果超過：
- 等待隔天重置
- 申請額外配額
- 減少 `--max-comments` 參數的數量

### Q: FFmpeg 剪輯失敗？

**A:** 請確認：
1. FFmpeg 已正確安裝（執行 `ffmpeg -version` 測試）
2. 有足夠的磁碟空間
3. 檢查錯誤日誌（預設顯示在終端機）

### Q: 影片下載很慢？

**A:** 可以：
1. 降低影片品質設定（在 `.env` 中設定 `VIDEO_QUALITY=480p`）
2. 檢查網路連線
3. 使用有線網路替代 Wi-Fi

## 注意事項

### 法律與版權

⚠️ **重要提醒：**

- 本工具僅供個人學習和研究使用
- 請遵守 YouTube 服務條款
- 請尊重影片創作者的版權
- 不得用於商業用途或大規模爬取
- 剪輯的影片片段僅供私人收藏，請勿公開分享或二次上傳

### YouTube API 使用限制

- 每日配額：10,000 units
- 每次獲取留言：1 unit
- 建議合理使用，避免浪費配額

## 技術細節

### 主要套件

- `google-api-python-client`: YouTube Data API 客戶端
- `yt-dlp`: YouTube 影片下載
- `ffmpeg-python`: FFmpeg Python 綁定
- `typer`: 命令列介面框架
- `rich`: 終端機美化
- `pydantic`: 資料驗證
- `loguru`: 日誌管理

### 剪輯策略

程式使用 FFmpeg 的 stream copy 模式進行快速剪輯：
- 優點：速度快，不重新編碼，保持原始品質
- 缺點：剪輯點可能不精確（受關鍵幀影響）

如需精確剪輯，可修改 `video_clipper.py` 中的 FFmpeg 命令。

## 開發計劃

### 已完成 ✅
- [x] YouTube API 整合
- [x] 留言解析
- [x] 影片下載和剪輯
- [x] CLI 工具
- [x] 基本錯誤處理

### 規劃中 🚧
- [ ] Web 介面
- [ ] 頻道監控功能
- [ ] 批次處理多個影片
- [ ] 單元測試
- [ ] 資料庫持久化
- [ ] 自動上傳到雲端儲存

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 授權

本專案僅供學習和研究使用。

## 鳴謝

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 強大的 YouTube 下載工具
- [FFmpeg](https://ffmpeg.org/) - 影片處理瑞士刀
- [Typer](https://typer.tiangolo.com/) - 優雅的 CLI 框架
- [Rich](https://rich.readthedocs.io/) - 美化終端機輸出

---

**版本：** 1.0.0
**最後更新：** 2025-10-21
**作者：** Claude Code
