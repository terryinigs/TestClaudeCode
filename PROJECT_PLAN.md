# YouTube 歌回自动剪辑系统 - 项目规划书

## 项目概述

### 背景
VTuber 直播后常会上传完整直播档案，粉丝会在评论区标注歌曲演唱时间。本项目旨在开发自动化系统，根据评论区时间戳自动剪辑出歌曲片段。

### 目标用户
- VTuber 粉丝群体
- 歌回剪辑爱好者
- 内容创作者

---

## 一、产品经理（PM）视角

### 1.1 核心功能需求

#### MVP (最小可行产品)
1. **视频监控**
   - 支持添加 YouTube 频道或播放列表
   - 自动检测新上传的直播档案
   - 手动输入单个视频 URL

2. **评论解析**
   - 自动扫描视频评论区
   - 识别时间戳格式（如：`12:34 - 歌名` 或 `1:23:45 歌曲标题`）
   - 支持多种常见时间戳格式
   - 过滤和验证有效评论

3. **视频剪辑**
   - 根据时间戳自动下载并剪辑
   - 支持设置片段前后缓冲时间（如前后各 2 秒）
   - 输出标准格式（MP4, 720p/1080p）
   - 自动命名：`[频道名]_[日期]_[歌名].mp4`

4. **结果管理**
   - 本地存储剪辑片段
   - 显示处理状态和进度
   - 错误日志和通知

#### 进阶功能（Phase 2）
- 评论投票系统（优先处理高赞评论）
- 批量处理多个视频
- 自动上传到云端存储
- Web 界面或 GUI
- 定时任务调度
- 去重机制（避免重复剪辑）

### 1.2 用户场景

**场景 1：手动单视频处理**
```
1. 用户输入 YouTube 视频 URL
2. 系统扫描评论区获取时间戳
3. 用户确认要剪辑的片段
4. 系统自动下载和剪辑
5. 输出到指定文件夹
```

**场景 2：频道自动监控**
```
1. 用户配置监控的频道列表
2. 系统定期检查新视频（每小时/每天）
3. 发现新直播档案后自动处理
4. 完成后发送通知
```

### 1.3 成功指标
- 时间戳识别准确率 > 90%
- 单个视频处理时间 < 30 分钟（取决于片段数量）
- 系统稳定性：连续运行 7 天无崩溃
- 用户操作步骤 < 5 步完成配置

### 1.4 风险与限制
- YouTube API 配额限制（每天 10,000 units）
- 版权和使用政策合规性
- 网络带宽需求（下载大视频）
- 存储空间管理

---

## 二、后端工程师（Backend）视角

### 2.1 系统架构

```
┌─────────────────┐
│  用户界面层      │
│  (CLI/Web)      │
└────────┬────────┘
         │
┌────────▼────────────────────────────────┐
│         应用服务层                       │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ 视频管理 │  │ 评论解析 │  │ 剪辑器 │ │
│  └──────────┘  └──────────┘  └────────┘ │
└────────┬────────────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│         基础设施层                       │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │YouTube API│  │  FFmpeg  │  │ 存储   │ │
│  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────┘
```

### 2.2 技术栈选型

#### 编程语言
**推荐：Python 3.10+**
- 理由：丰富的视频处理库、YouTube API 客户端成熟、快速原型开发

**备选：Node.js / Go**
- Node.js：适合 Web 服务集成
- Go：高性能、适合长时间运行服务

#### 核心依赖库

```python
# YouTube 交互
google-api-python-client  # YouTube Data API v3
google-auth-oauthlib      # 认证

# 视频下载
yt-dlp                    # YouTube 视频下载（ffmpeg wrapper）

# 视频处理
ffmpeg-python            # FFmpeg Python 绑定

# 数据处理
pydantic                 # 数据验证
sqlalchemy               # 数据库 ORM（可选）

# 任务调度
celery                   # 异步任务队列（进阶）
apscheduler              # 定时任务

# 其他
requests                 # HTTP 请求
python-dotenv            # 环境变量管理
loguru                   # 日志
```

### 2.3 核心模块设计

#### 2.3.1 YouTube 服务模块
```python
class YouTubeService:
    """
    负责与 YouTube API 交互
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = build('youtube', 'v3', developerKey=api_key)

    def get_video_info(self, video_id: str) -> VideoInfo:
        """获取视频元数据"""
        pass

    def get_comments(self, video_id: str, max_results: int = 100) -> List[Comment]:
        """获取视频评论"""
        pass

    def get_channel_videos(self, channel_id: str) -> List[VideoInfo]:
        """获取频道最新视频"""
        pass
```

**API 配额优化策略：**
- 缓存视频信息（24小时）
- 评论增量获取（只获取新评论）
- 批量请求减少 API 调用

#### 2.3.2 评论解析模块
```python
class CommentParser:
    """
    解析评论中的时间戳和歌曲信息
    """
    # 支持的时间格式
    PATTERNS = [
        r'(\d{1,2}):(\d{2}):(\d{2})\s*[-–—]\s*(.+)',  # 1:23:45 - 歌名
        r'(\d{1,2}):(\d{2})\s*[-–—]\s*(.+)',          # 12:34 - 歌名
        r'(\d{1,2}):(\d{2}):(\d{2})\s+(.+)',          # 1:23:45 歌名
        r'(\d{1,2}):(\d{2})\s+(.+)',                  # 12:34 歌名
    ]

    def parse_comment(self, text: str) -> Optional[SongTimestamp]:
        """解析单条评论"""
        pass

    def extract_all_timestamps(self, comments: List[Comment]) -> List[SongTimestamp]:
        """批量提取时间戳"""
        pass

    def validate_timestamp(self, timestamp: SongTimestamp, video_duration: int) -> bool:
        """验证时间戳有效性"""
        pass
```

**数据模型：**
```python
from pydantic import BaseModel

class SongTimestamp(BaseModel):
    start_time: int          # 秒数
    end_time: Optional[int]  # 如果评论包含结束时间
    song_name: str
    original_comment: str
    comment_likes: int       # 用于排序
    comment_author: str
```

#### 2.3.3 视频剪辑模块
```python
class VideoClipper:
    """
    处理视频下载和剪辑
    """
    def __init__(self, output_dir: str, buffer_seconds: int = 2):
        self.output_dir = output_dir
        self.buffer_seconds = buffer_seconds

    def download_video(self, video_url: str) -> str:
        """下载视频到临时目录"""
        # 使用 yt-dlp
        pass

    def clip_segment(self,
                     video_path: str,
                     start: int,
                     end: int,
                     output_name: str) -> str:
        """剪辑视频片段"""
        # 使用 FFmpeg
        # ffmpeg -i input.mp4 -ss START -to END -c copy output.mp4
        pass

    def batch_clip(self, video_url: str, timestamps: List[SongTimestamp]):
        """批量剪辑"""
        pass
```

**FFmpeg 命令优化：**
```bash
# 快速剪辑（stream copy，不重新编码）
ffmpeg -ss START -i input.mp4 -to DURATION -c copy -avoid_negative_ts 1 output.mp4

# 精确剪辑（重新编码，速度较慢但精确）
ffmpeg -i input.mp4 -ss START -to END -c:v libx264 -c:a aac output.mp4
```

### 2.4 数据库设计（可选）

如果需要持久化和任务管理，建议使用 SQLite（简单）或 PostgreSQL（生产）

```sql
-- 视频表
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

-- 监控频道表
CREATE TABLE monitored_channels (
    id INTEGER PRIMARY KEY,
    channel_id VARCHAR(50) UNIQUE,
    channel_name VARCHAR(255),
    last_check TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);
```

### 2.5 性能考虑

#### 2.5.1 异步处理
```python
# 使用异步下载和剪辑
import asyncio

async def process_video_async(video_id: str):
    # 1. 获取评论（I/O bound）
    comments = await fetch_comments_async(video_id)

    # 2. 解析时间戳（CPU bound）
    timestamps = parse_timestamps(comments)

    # 3. 下载视频（I/O bound）
    video_path = await download_video_async(video_id)

    # 4. 并行剪辑多个片段
    tasks = [clip_segment_async(video_path, ts) for ts in timestamps]
    await asyncio.gather(*tasks)
```

#### 2.5.2 存储优化
- 下载最低质量满足需求的视频（节省带宽和存储）
- 剪辑完成后删除原视频
- 实现 LRU 缓存策略

#### 2.5.3 错误处理
```python
class VideoProcessingError(Exception):
    pass

def retry_on_failure(max_retries=3):
    """装饰器：失败重试"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_retries - 1:
                        raise
                    time.sleep(2 ** i)  # 指数退避
        return wrapper
    return decorator
```

### 2.6 API 设计（如果提供 Web 服务）

```python
# RESTful API 端点

POST /api/videos
# 提交新视频处理任务
{
    "video_url": "https://youtube.com/watch?v=xxx",
    "auto_detect_timestamps": true,
    "manual_timestamps": [...]  # 可选
}

GET /api/videos/{video_id}
# 获取处理状态

GET /api/videos/{video_id}/clips
# 获取剪辑列表

POST /api/channels
# 添加监控频道

GET /api/jobs/{job_id}
# 查询任务状态
```

---

## 三、前端工程师（Frontend）视角

### 3.1 界面方案

#### 方案 A：命令行工具 (CLI) - MVP 推荐
```bash
# 单视频处理
youtube-clipper process https://youtube.com/watch?v=xxx

# 监控频道
youtube-clipper monitor --channel UC123456 --interval 1h

# 配置
youtube-clipper config --api-key YOUR_KEY --output-dir ./clips
```

**优点：**
- 开发快速
- 适合技术用户
- 易于自动化集成

**技术栈：**
- Python: `click` 或 `typer` 库
- 进度显示: `tqdm`
- 表格输出: `rich`

#### 方案 B：Web 界面 - Phase 2
```
技术栈：
- 前端：React / Vue.js / Svelte
- 后端：FastAPI / Flask
- 实时通信：WebSocket（进度更新）
```

**核心页面：**
1. **仪表盘**
   - 显示处理中/完成的任务
   - 存储空间使用情况

2. **新建任务**
   - 输入视频 URL
   - 预览检测到的时间戳
   - 编辑/删除时间戳
   - 开始处理

3. **频道管理**
   - 添加/删除监控频道
   - 查看历史处理记录

4. **设置**
   - API 配置
   - 输出格式设置
   - 通知设置

### 3.2 用户体验设计

#### 关键交互流程
```
1. 输入视频 URL
   ↓
2. [加载动画] 正在获取评论...
   ↓
3. 显示检测到的时间戳列表
   - 可编辑/删除
   - 显示评论原文
   ↓
4. 点击"开始剪辑"
   ↓
5. [进度条] 下载中... 45%
   [进度条] 剪辑中... 2/5 完成
   ↓
6. 完成提示 + 下载链接
```

#### 错误处理 UI
- 友好的错误提示（而非技术错误信息）
- 提供解决建议
- 重试按钮

---

## 四、技术实现路线图

### Phase 1: MVP (2-3 周)
**Week 1:**
- [ ] YouTube API 集成和测试
- [ ] 评论解析逻辑开发
- [ ] 时间戳提取和验证

**Week 2:**
- [ ] 视频下载功能（yt-dlp）
- [ ] FFmpeg 剪辑功能
- [ ] 基本 CLI 工具

**Week 3:**
- [ ] 错误处理和日志
- [ ] 单元测试
- [ ] 文档和使用说明

### Phase 2: 增强功能 (3-4 周)
- [ ] 批量处理
- [ ] 数据库持久化
- [ ] 频道监控和调度
- [ ] Web 界面开发

### Phase 3: 优化和扩展
- [ ] 性能优化
- [ ] 云存储集成
- [ ] 用户认证系统
- [ ] 移动端适配

---

## 五、开发环境配置

### 5.1 必需软件
```bash
# Python 3.10+
python --version

# FFmpeg
sudo apt install ffmpeg  # Linux
brew install ffmpeg      # macOS

# 项目依赖
pip install -r requirements.txt
```

### 5.2 YouTube API 设置
```
1. 访问 Google Cloud Console
2. 创建新项目
3. 启用 YouTube Data API v3
4. 创建 API 密钥
5. 配置到 .env 文件
```

### 5.3 项目结构
```
youtube-song-clipper/
├── src/
│   ├── api/              # YouTube API 交互
│   ├── parser/           # 评论解析
│   ├── clipper/          # 视频剪辑
│   ├── storage/          # 存储管理
│   └── utils/            # 工具函数
├── tests/                # 单元测试
├── cli/                  # 命令行工具
├── web/                  # Web 界面（可选）
├── config/               # 配置文件
├── docs/                 # 文档
├── requirements.txt
├── .env.example
└── README.md
```

---

## 六、成本估算

### 6.1 开发成本
- MVP 开发：约 80-120 小时
- 测试和优化：约 40 小时
- 文档编写：约 20 小时

### 6.2 运营成本
- YouTube API：免费（配额内）
- 云服务器：$5-20/月（如需托管）
- 云存储：按使用量计费
- 域名：$10/年（如需 Web 服务）

### 6.3 配额限制
```
YouTube Data API v3 每日配额：10,000 units

操作成本：
- 获取视频详情：1 unit
- 获取评论：1 unit（每页）
- 搜索：100 units

估算：
每天可处理约 100 个视频（假设每个视频 100 条评论）
```

---

## 七、风险评估与应对

### 7.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| API 配额超限 | 高 | 中 | 实现缓存、批量请求、用户自带 API Key |
| 时间戳格式多样 | 中 | 高 | 使用多个正则表达式、机器学习辅助 |
| 视频下载失败 | 中 | 中 | 重试机制、降级策略 |
| FFmpeg 剪辑错误 | 中 | 低 | 参数验证、错误捕获 |

### 7.2 法律风险
- **版权问题**：明确标注仅供个人学习使用
- **YouTube ToS**：遵守服务条款，避免大规模爬取
- **用户协议**：添加免责声明

### 7.3 运营风险
- 存储空间快速增长 → 实现自动清理机制
- 网络带宽限制 → 限制并发下载数

---

## 八、成功案例参考

### 类似项目
1. **yt-dlp**：YouTube 下载工具（可借鉴其下载逻辑）
2. **youtube-dl-server**：Web 界面封装
3. **Clipper.gg**：游戏剪辑工具（UI/UX 参考）

---

## 九、下一步行动

### 立即执行
1. ✅ 阅读并确认此规划书
2. [ ] PM 确认功能优先级
3. [ ] Backend 选定技术栈
4. [ ] Frontend 确定界面方案（CLI vs Web）

### 本周任务
1. [ ] 申请 YouTube API 密钥
2. [ ] 搭建开发环境
3. [ ] 实现时间戳解析 POC（Proof of Concept）
4. [ ] 测试 yt-dlp + FFmpeg 剪辑流程

### 需要决策的问题
1. **目标用户群体**：技术用户 vs 普通用户？
2. **部署方式**：本地工具 vs 云服务？
3. **商业模式**：开源免费 vs 付费服务？
4. **初始支持语言**：仅中文评论 vs 多语言？

---

## 十、附录

### A. 技术词汇表
- **VTuber**：Virtual YouTuber，虚拟主播
- **歌回**：唱歌直播的录播
- **时间戳**：视频中特定时间点标记（如 12:34）
- **FFmpeg**：开源视频处理工具
- **yt-dlp**：YouTube 视频下载工具

### B. 参考资源
- YouTube Data API v3 文档：https://developers.google.com/youtube/v3
- FFmpeg 文档：https://ffmpeg.org/documentation.html
- yt-dlp GitHub：https://github.com/yt-dlp/yt-dlp

---

**文档版本**：v1.0
**创建日期**：2025-10-21
**最后更新**：2025-10-21
**负责人**：待定
**状态**：待审核
