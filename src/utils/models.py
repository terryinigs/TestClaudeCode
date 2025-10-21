"""資料模型定義"""
from typing import Optional
from pydantic import BaseModel, Field


class SongTimestamp(BaseModel):
    """歌曲時間戳資料模型"""
    start_time: int = Field(..., description="開始時間（秒）")
    end_time: Optional[int] = Field(None, description="結束時間（秒）")
    song_name: str = Field(..., description="歌曲名稱")
    original_comment: str = Field(..., description="原始留言內容")
    comment_likes: int = Field(default=0, description="留言讚數")
    comment_author: str = Field(default="", description="留言作者")

    def duration(self) -> Optional[int]:
        """取得片段長度"""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    def __str__(self) -> str:
        """字串表示"""
        start = self._format_time(self.start_time)
        if self.end_time:
            end = self._format_time(self.end_time)
            return f"{start}-{end} {self.song_name}"
        return f"{start} {self.song_name}"

    @staticmethod
    def _format_time(seconds: int) -> str:
        """將秒數轉換為時:分:秒格式"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"


class VideoInfo(BaseModel):
    """影片資訊模型"""
    video_id: str = Field(..., description="YouTube 影片 ID")
    title: str = Field(..., description="影片標題")
    channel_name: str = Field(..., description="頻道名稱")
    duration: int = Field(..., description="影片長度（秒）")
    published_at: Optional[str] = Field(None, description="發布時間")

    def __str__(self) -> str:
        return f"{self.title} by {self.channel_name}"


class Comment(BaseModel):
    """留言模型"""
    text: str = Field(..., description="留言內容")
    author: str = Field(..., description="留言作者")
    likes: int = Field(default=0, description="讚數")
    published_at: Optional[str] = Field(None, description="發布時間")
