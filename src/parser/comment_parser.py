"""留言解析模組"""
import re
from typing import List, Optional
from loguru import logger

from src.utils.models import Comment, SongTimestamp


class CommentParser:
    """留言解析器類別"""

    # 支援的時間戳格式
    PATTERNS = [
        # 格式: 1:23:45 - 歌名 或 1:23:45 – 歌名
        r'(\d{1,2}):(\d{2}):(\d{2})\s*[-–—~～]\s*(.+)',
        # 格式: 12:34 - 歌名
        r'(\d{1,2}):(\d{2})\s*[-–—~～]\s*(.+)',
        # 格式: 1:23:45 歌名 （沒有分隔符號）
        r'(\d{1,2}):(\d{2}):(\d{2})\s+(.+)',
        # 格式: 12:34 歌名
        r'(\d{1,2}):(\d{2})\s+([^\d\s].+)',
        # 格式: [1:23:45] 歌名
        r'\[(\d{1,2}):(\d{2}):(\d{2})\]\s*(.+)',
        # 格式: [12:34] 歌名
        r'\[(\d{1,2}):(\d{2})\]\s*(.+)',
        # 格式: 1:23:45-1:25:00 歌名 (包含結束時間)
        r'(\d{1,2}):(\d{2}):(\d{2})\s*[-–—~～]\s*(\d{1,2}):(\d{2}):(\d{2})\s+(.+)',
        # 格式: 12:34-15:20 歌名 (包含結束時間)
        r'(\d{1,2}):(\d{2})\s*[-–—~～]\s*(\d{1,2}):(\d{2})\s+(.+)',
    ]

    def __init__(self, min_song_name_length: int = 2):
        """
        初始化解析器

        Args:
            min_song_name_length: 歌曲名稱最小長度
        """
        self.min_song_name_length = min_song_name_length

    def parse_comment(self, comment: Comment) -> Optional[SongTimestamp]:
        """
        解析單條留言

        Args:
            comment: Comment 物件

        Returns:
            SongTimestamp 物件，如果無法解析則返回 None
        """
        text = comment.text

        # 移除 HTML 標籤
        text = re.sub(r'<[^>]+>', '', text)

        for pattern in self.PATTERNS:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()

                # 判斷是否包含結束時間
                if len(groups) == 7:  # 格式: HH:MM:SS-HH:MM:SS 歌名
                    start_time = self._time_to_seconds(
                        int(groups[0]), int(groups[1]), int(groups[2])
                    )
                    end_time = self._time_to_seconds(
                        int(groups[3]), int(groups[4]), int(groups[5])
                    )
                    song_name = groups[6].strip()
                elif len(groups) == 5:  # 格式: MM:SS-MM:SS 歌名
                    start_time = self._time_to_seconds(0, int(groups[0]), int(groups[1]))
                    end_time = self._time_to_seconds(0, int(groups[2]), int(groups[3]))
                    song_name = groups[4].strip()
                elif len(groups) == 4:  # 格式: HH:MM:SS 歌名 或 MM:SS 歌名
                    # 檢查是否為 HH:MM:SS 格式
                    if ':' in str(groups[2]):
                        # 可能是 MM:SS 格式但被誤判，重新處理
                        start_time = self._time_to_seconds(0, int(groups[0]), int(groups[1]))
                        song_name = groups[2].strip() + (groups[3].strip() if len(groups) > 3 else "")
                        end_time = None
                    else:
                        start_time = self._time_to_seconds(
                            int(groups[0]), int(groups[1]), int(groups[2])
                        )
                        song_name = groups[3].strip()
                        end_time = None
                elif len(groups) == 3:  # 格式: MM:SS 歌名
                    start_time = self._time_to_seconds(0, int(groups[0]), int(groups[1]))
                    song_name = groups[2].strip()
                    end_time = None
                else:
                    continue

                # 驗證歌曲名稱
                if len(song_name) < self.min_song_name_length:
                    continue

                # 清理歌曲名稱
                song_name = self._clean_song_name(song_name)

                return SongTimestamp(
                    start_time=start_time,
                    end_time=end_time,
                    song_name=song_name,
                    original_comment=comment.text,
                    comment_likes=comment.likes,
                    comment_author=comment.author
                )

        return None

    def extract_all_timestamps(self, comments: List[Comment]) -> List[SongTimestamp]:
        """
        批次提取時間戳

        Args:
            comments: Comment 物件列表

        Returns:
            SongTimestamp 物件列表
        """
        timestamps = []

        for comment in comments:
            timestamp = self.parse_comment(comment)
            if timestamp:
                timestamps.append(timestamp)

        logger.info(f"從 {len(comments)} 則留言中解析出 {len(timestamps)} 個時間戳")
        return timestamps

    def validate_timestamp(
        self,
        timestamp: SongTimestamp,
        video_duration: int
    ) -> bool:
        """
        驗證時間戳有效性

        Args:
            timestamp: SongTimestamp 物件
            video_duration: 影片總長度（秒）

        Returns:
            是否有效
        """
        # 檢查開始時間是否在影片範圍內
        if timestamp.start_time < 0 or timestamp.start_time >= video_duration:
            logger.warning(f"時間戳超出影片範圍: {timestamp}")
            return False

        # 檢查結束時間（如果有）
        if timestamp.end_time:
            if timestamp.end_time <= timestamp.start_time:
                logger.warning(f"結束時間早於開始時間: {timestamp}")
                return False
            if timestamp.end_time > video_duration:
                logger.warning(f"結束時間超出影片範圍: {timestamp}")
                return False

        return True

    @staticmethod
    def _time_to_seconds(hours: int, minutes: int, seconds: int) -> int:
        """
        將時:分:秒轉換為總秒數

        Args:
            hours: 小時
            minutes: 分鐘
            seconds: 秒

        Returns:
            總秒數
        """
        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def _clean_song_name(name: str) -> str:
        """
        清理歌曲名稱

        Args:
            name: 原始名稱

        Returns:
            清理後的名稱
        """
        # 移除前後空白
        name = name.strip()

        # 移除常見的括號註解
        # name = re.sub(r'\([^)]*\)', '', name)
        # name = re.sub(r'\[[^\]]*\]', '', name)

        # 移除多餘空白
        name = re.sub(r'\s+', ' ', name)

        # 移除不適合做檔名的字元
        name = re.sub(r'[<>:"/\\|?*]', '', name)

        return name.strip()
