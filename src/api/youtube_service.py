"""YouTube API 服務模組"""
import re
from typing import List, Optional
from googleapiclient.discovery import build
from loguru import logger

from src.utils.models import VideoInfo, Comment


class YouTubeService:
    """YouTube API 服務類別"""

    def __init__(self, api_key: str):
        """
        初始化 YouTube 服務

        Args:
            api_key: YouTube Data API v3 金鑰
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        logger.info("YouTube API 服務已初始化")

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        從 YouTube URL 提取影片 ID

        Args:
            url: YouTube 影片 URL

        Returns:
            影片 ID，如果無法提取則返回 None
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # 如果已經是 ID 格式（11 個字元）
        if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', url):
            return url

        return None

    def get_video_info(self, video_id: str) -> Optional[VideoInfo]:
        """
        獲取影片資訊

        Args:
            video_id: YouTube 影片 ID

        Returns:
            VideoInfo 物件，如果失敗則返回 None
        """
        try:
            request = self.youtube.videos().list(
                part='snippet,contentDetails',
                id=video_id
            )
            response = request.execute()

            if not response.get('items'):
                logger.error(f"找不到影片 ID: {video_id}")
                return None

            item = response['items'][0]
            snippet = item['snippet']
            duration_str = item['contentDetails']['duration']

            # 解析 ISO 8601 duration 格式 (例如: PT1H23M45S)
            duration = self._parse_duration(duration_str)

            video_info = VideoInfo(
                video_id=video_id,
                title=snippet['title'],
                channel_name=snippet['channelTitle'],
                duration=duration,
                published_at=snippet['publishedAt']
            )

            logger.info(f"獲取影片資訊成功: {video_info.title}")
            return video_info

        except Exception as e:
            logger.error(f"獲取影片資訊失敗: {e}")
            return None

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """
        解析 ISO 8601 duration 格式

        Args:
            duration_str: ISO 8601 格式的時間字串 (例如: PT1H23M45S)

        Returns:
            總秒數
        """
        hours = 0
        minutes = 0
        seconds = 0

        # 使用正規表達式提取時、分、秒
        hour_match = re.search(r'(\d+)H', duration_str)
        minute_match = re.search(r'(\d+)M', duration_str)
        second_match = re.search(r'(\d+)S', duration_str)

        if hour_match:
            hours = int(hour_match.group(1))
        if minute_match:
            minutes = int(minute_match.group(1))
        if second_match:
            seconds = int(second_match.group(1))

        return hours * 3600 + minutes * 60 + seconds

    def get_comments(self, video_id: str, max_results: int = 100) -> List[Comment]:
        """
        獲取影片留言

        Args:
            video_id: YouTube 影片 ID
            max_results: 最多獲取的留言數量

        Returns:
            Comment 物件列表
        """
        comments = []

        try:
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(max_results, 100),  # API 限制每次最多 100
                order='relevance'  # 按相關性排序（通常會優先顯示高讚留言）
            )

            while request and len(comments) < max_results:
                response = request.execute()

                for item in response.get('items', []):
                    snippet = item['snippet']['topLevelComment']['snippet']
                    comment = Comment(
                        text=snippet['textDisplay'],
                        author=snippet['authorDisplayName'],
                        likes=snippet.get('likeCount', 0),
                        published_at=snippet['publishedAt']
                    )
                    comments.append(comment)

                # 檢查是否有下一頁
                if len(comments) < max_results and 'nextPageToken' in response:
                    request = self.youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=min(max_results - len(comments), 100),
                        pageToken=response['nextPageToken'],
                        order='relevance'
                    )
                else:
                    break

            logger.info(f"成功獲取 {len(comments)} 則留言")
            return comments

        except Exception as e:
            logger.error(f"獲取留言失敗: {e}")
            return comments
