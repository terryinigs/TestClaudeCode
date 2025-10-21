#!/usr/bin/env python3
"""
使用範例腳本

展示如何直接使用模組而不是 CLI
"""

from src.api.youtube_service import YouTubeService
from src.parser.comment_parser import CommentParser
from src.clipper.video_clipper import VideoClipper
from src.utils.config import settings

# 確保目錄存在
settings.ensure_dirs()

# 設定你的 API 金鑰
API_KEY = settings.youtube_api_key or "your_api_key_here"

# 設定影片 URL
VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def main():
    """主函數"""

    # 1. 初始化服務
    print("初始化服務...")
    youtube = YouTubeService(API_KEY)
    parser = CommentParser()
    clipper = VideoClipper(
        output_dir=settings.output_dir,
        temp_dir=settings.temp_dir,
        buffer_seconds=2
    )

    # 2. 獲取影片資訊
    print(f"\n獲取影片資訊: {VIDEO_URL}")
    video_id = youtube.extract_video_id(VIDEO_URL)
    video_info = youtube.get_video_info(video_id)

    if not video_info:
        print("無法獲取影片資訊")
        return

    print(f"標題: {video_info.title}")
    print(f"頻道: {video_info.channel_name}")
    print(f"長度: {video_info.duration} 秒")

    # 3. 獲取留言
    print("\n獲取留言...")
    comments = youtube.get_comments(video_id, max_results=100)
    print(f"獲取了 {len(comments)} 則留言")

    # 4. 解析時間戳
    print("\n解析時間戳...")
    timestamps = parser.extract_all_timestamps(comments)

    # 驗證時間戳
    valid_timestamps = [
        ts for ts in timestamps
        if parser.validate_timestamp(ts, video_info.duration)
    ]

    print(f"找到 {len(valid_timestamps)} 個有效時間戳:")
    for i, ts in enumerate(valid_timestamps, 1):
        print(f"  {i}. {ts}")

    # 5. 剪輯影片（可選）
    if valid_timestamps:
        proceed = input("\n是否開始剪輯? (y/n): ")
        if proceed.lower() == 'y':
            print("\n開始剪輯...")
            clipped_files = clipper.batch_clip(
                video_url=f"https://www.youtube.com/watch?v={video_id}",
                timestamps=valid_timestamps,
                video_info=video_info
            )
            print(f"\n完成！成功剪輯 {len(clipped_files)} 個片段")
            print(f"輸出目錄: {settings.output_dir}")


if __name__ == "__main__":
    main()
