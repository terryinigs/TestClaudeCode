"""影片剪輯模組"""
import subprocess
from pathlib import Path
from typing import List, Optional
import yt_dlp
from loguru import logger

from src.utils.models import SongTimestamp, VideoInfo


class VideoClipper:
    """影片剪輯器類別"""

    def __init__(
        self,
        output_dir: Path,
        temp_dir: Path,
        buffer_seconds: int = 2,
        video_quality: str = "720p"
    ):
        """
        初始化剪輯器

        Args:
            output_dir: 輸出目錄
            temp_dir: 臨時檔案目錄
            buffer_seconds: 片段前後緩衝時間（秒）
            video_quality: 影片品質
        """
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.buffer_seconds = buffer_seconds
        self.video_quality = video_quality

        # 確保目錄存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"影片剪輯器已初始化 - 輸出: {output_dir}, 暫存: {temp_dir}")

    def download_video(self, video_url: str, video_info: VideoInfo) -> Optional[Path]:
        """
        下載 YouTube 影片

        Args:
            video_url: YouTube 影片 URL
            video_info: 影片資訊

        Returns:
            下載的影片路徑，如果失敗則返回 None
        """
        try:
            # 設定下載選項
            output_template = str(self.temp_dir / f"{video_info.video_id}.%(ext)s")

            ydl_opts = {
                'format': self._get_format_string(),
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
            }

            logger.info(f"開始下載影片: {video_info.title}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                video_path = Path(filename)

                if video_path.exists():
                    logger.info(f"影片下載完成: {video_path}")
                    return video_path
                else:
                    logger.error("影片下載失敗：檔案不存在")
                    return None

        except Exception as e:
            logger.error(f"下載影片時發生錯誤: {e}")
            return None

    def clip_segment(
        self,
        video_path: Path,
        timestamp: SongTimestamp,
        video_info: VideoInfo,
        output_filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        剪輯影片片段

        Args:
            video_path: 原影片路徑
            timestamp: 時間戳資訊
            video_info: 影片資訊
            output_filename: 自訂輸出檔名（可選）

        Returns:
            剪輯後的影片路徑，如果失敗則返回 None
        """
        try:
            # 計算實際的開始和結束時間（加上緩衝）
            start_time = max(0, timestamp.start_time - self.buffer_seconds)

            if timestamp.end_time:
                # 如果有結束時間，使用它
                end_time = min(
                    video_info.duration,
                    timestamp.end_time + self.buffer_seconds
                )
                duration = end_time - start_time
            else:
                # 如果沒有結束時間，預設剪輯 4 分鐘（一般歌曲長度）
                default_duration = 240  # 4 分鐘
                duration = min(
                    default_duration + 2 * self.buffer_seconds,
                    video_info.duration - start_time
                )

            # 生成輸出檔名
            if not output_filename:
                # 清理檔名中的特殊字元
                safe_song_name = self._sanitize_filename(timestamp.song_name)
                output_filename = f"{video_info.channel_name}_{safe_song_name}.mp4"

            output_path = self.output_dir / output_filename

            # 使用 FFmpeg 剪輯
            # -ss: 開始時間, -t: 持續時間, -c copy: 快速複製不重新編碼
            command = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', str(video_path),
                '-t', str(duration),
                '-c', 'copy',
                '-avoid_negative_ts', '1',
                '-y',  # 覆蓋現有檔案
                str(output_path)
            ]

            logger.info(f"開始剪輯: {timestamp.song_name} ({start_time}s - {start_time + duration}s)")

            # 執行 FFmpeg
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )

            if output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"剪輯完成: {output_path.name} ({file_size:.2f} MB)")
                return output_path
            else:
                logger.error("剪輯失敗：輸出檔案不存在")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg 執行失敗: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"剪輯影片時發生錯誤: {e}")
            return None

    def batch_clip(
        self,
        video_url: str,
        timestamps: List[SongTimestamp],
        video_info: VideoInfo
    ) -> List[Path]:
        """
        批次剪輯多個片段

        Args:
            video_url: YouTube 影片 URL
            timestamps: 時間戳列表
            video_info: 影片資訊

        Returns:
            成功剪輯的檔案路徑列表
        """
        clipped_files = []

        # 下載影片
        video_path = self.download_video(video_url, video_info)
        if not video_path:
            logger.error("無法下載影片，批次剪輯中止")
            return clipped_files

        try:
            # 剪輯每個片段
            for i, timestamp in enumerate(timestamps, 1):
                logger.info(f"處理片段 {i}/{len(timestamps)}: {timestamp.song_name}")

                output_path = self.clip_segment(video_path, timestamp, video_info)
                if output_path:
                    clipped_files.append(output_path)

            logger.info(f"批次剪輯完成: {len(clipped_files)}/{len(timestamps)} 個片段成功")

        finally:
            # 清理臨時檔案
            if video_path.exists():
                try:
                    video_path.unlink()
                    logger.info(f"已刪除臨時檔案: {video_path}")
                except Exception as e:
                    logger.warning(f"刪除臨時檔案失敗: {e}")

        return clipped_files

    def _get_format_string(self) -> str:
        """
        根據設定的品質返回 yt-dlp 格式字串

        Returns:
            格式字串
        """
        quality_map = {
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            'best': 'bestvideo+bestaudio/best',
            'worst': 'worstvideo+worstaudio/worst'
        }

        return quality_map.get(self.video_quality, quality_map['720p'])

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        清理檔名中的非法字元

        Args:
            filename: 原始檔名

        Returns:
            清理後的檔名
        """
        # 移除或替換不合法的檔名字元
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '')

        # 移除前後空白
        filename = filename.strip()

        # 限制檔名長度
        max_length = 100
        if len(filename) > max_length:
            filename = filename[:max_length]

        return filename
