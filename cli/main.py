#!/usr/bin/env python3
"""YouTube 歌回剪輯器 - CLI 主程式"""
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

from src.api.youtube_service import YouTubeService
from src.parser.comment_parser import CommentParser
from src.clipper.video_clipper import VideoClipper
from src.utils.config import settings

# 建立 CLI 應用程式
app = typer.Typer(
    name="youtube-clipper",
    help="YouTube 歌回自動剪輯工具",
    add_completion=False
)
console = Console()


def setup_logger():
    """設定日誌"""
    logger.remove()  # 移除預設處理器
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=settings.log_level
    )


@app.command()
def process(
    video_url: str = typer.Argument(..., help="YouTube 影片 URL 或影片 ID"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="YouTube API 金鑰（或從 .env 讀取）"),
    max_comments: int = typer.Option(100, "--max-comments", "-m", help="最多獲取的留言數量"),
    output_dir: str = typer.Option(None, "--output", "-o", help="輸出目錄"),
    auto_clip: bool = typer.Option(True, "--auto-clip/--no-auto-clip", help="自動開始剪輯"),
):
    """
    處理單個 YouTube 影片，自動剪輯歌曲片段
    """
    setup_logger()

    # 確保目錄存在
    settings.ensure_dirs()

    # 使用自訂輸出目錄（如果提供）
    if output_dir:
        settings.output_dir = Path(output_dir)
        settings.output_dir.mkdir(parents=True, exist_ok=True)

    # 取得 API 金鑰
    api_key = api_key or settings.youtube_api_key
    if not api_key:
        console.print("[red]錯誤：未提供 YouTube API 金鑰[/red]")
        console.print("請使用 --api-key 參數或在 .env 檔案中設定 YOUTUBE_API_KEY")
        raise typer.Exit(1)

    try:
        # 初始化服務
        youtube_service = YouTubeService(api_key)
        comment_parser = CommentParser()
        video_clipper = VideoClipper(
            output_dir=settings.output_dir,
            temp_dir=settings.temp_dir,
            buffer_seconds=settings.clip_buffer_seconds,
            video_quality=settings.video_quality
        )

        # Step 1: 取得影片資訊
        console.print(f"\n[bold cyan]步驟 1/4:[/bold cyan] 獲取影片資訊...")
        video_id = youtube_service.extract_video_id(video_url)
        if not video_id:
            console.print(f"[red]錯誤：無法從 URL 提取影片 ID: {video_url}[/red]")
            raise typer.Exit(1)

        video_info = youtube_service.get_video_info(video_id)
        if not video_info:
            console.print("[red]錯誤：無法獲取影片資訊[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓[/green] 影片: {video_info.title}")
        console.print(f"[green]✓[/green] 頻道: {video_info.channel_name}")
        console.print(f"[green]✓[/green] 長度: {video_info.duration} 秒")

        # Step 2: 獲取留言
        console.print(f"\n[bold cyan]步驟 2/4:[/bold cyan] 獲取影片留言...")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("正在獲取留言...", total=None)
            comments = youtube_service.get_comments(video_id, max_results=max_comments)
            progress.update(task, completed=True)

        console.print(f"[green]✓[/green] 成功獲取 {len(comments)} 則留言")

        # Step 3: 解析時間戳
        console.print(f"\n[bold cyan]步驟 3/4:[/bold cyan] 解析歌曲時間戳...")
        timestamps = comment_parser.extract_all_timestamps(comments)

        if not timestamps:
            console.print("[yellow]警告：未找到任何時間戳[/yellow]")
            console.print("請確認影片留言區是否包含時間戳格式的歌曲清單")
            raise typer.Exit(0)

        # 驗證並過濾時間戳
        valid_timestamps = [
            ts for ts in timestamps
            if comment_parser.validate_timestamp(ts, video_info.duration)
        ]

        console.print(f"[green]✓[/green] 找到 {len(valid_timestamps)} 個有效時間戳")

        # 顯示時間戳表格
        table = Table(title="解析到的歌曲清單")
        table.add_column("序號", style="cyan", width=6)
        table.add_column("時間", style="green", width=12)
        table.add_column("歌名", style="yellow")
        table.add_column("讚數", style="magenta", width=8)

        for i, ts in enumerate(valid_timestamps, 1):
            table.add_row(
                str(i),
                str(ts),
                ts.song_name,
                str(ts.comment_likes)
            )

        console.print(table)

        # Step 4: 剪輯影片
        if not auto_clip:
            proceed = typer.confirm("\n是否開始剪輯？")
            if not proceed:
                console.print("[yellow]已取消剪輯[/yellow]")
                raise typer.Exit(0)

        console.print(f"\n[bold cyan]步驟 4/4:[/bold cyan] 剪輯影片片段...")
        console.print(f"[dim]這可能需要一些時間，請稍候...[/dim]\n")

        clipped_files = video_clipper.batch_clip(
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            timestamps=valid_timestamps,
            video_info=video_info
        )

        # 顯示結果
        console.print(f"\n[bold green]✓ 完成！[/bold green]")
        console.print(f"成功剪輯 {len(clipped_files)}/{len(valid_timestamps)} 個片段")
        console.print(f"輸出目錄: {settings.output_dir.absolute()}")

        if clipped_files:
            console.print("\n[bold]剪輯完成的檔案：[/bold]")
            for file in clipped_files:
                file_size = file.stat().st_size / (1024 * 1024)
                console.print(f"  • {file.name} ({file_size:.2f} MB)")

    except KeyboardInterrupt:
        console.print("\n[yellow]已中斷處理[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]錯誤：{e}[/red]")
        logger.exception("處理過程中發生錯誤")
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="顯示目前設定"),
):
    """
    管理設定
    """
    if show:
        console.print("[bold]目前設定：[/bold]")
        console.print(f"API 金鑰: {'已設定' if settings.youtube_api_key else '未設定'}")
        console.print(f"輸出目錄: {settings.output_dir}")
        console.print(f"暫存目錄: {settings.temp_dir}")
        console.print(f"緩衝時間: {settings.clip_buffer_seconds} 秒")
        console.print(f"影片品質: {settings.video_quality}")
        console.print(f"日誌等級: {settings.log_level}")
    else:
        console.print("使用 --show 參數顯示設定")


@app.command()
def version():
    """
    顯示版本資訊
    """
    console.print("[bold]YouTube 歌回剪輯器[/bold]")
    console.print("版本: 1.0.0")
    console.print("作者: Claude Code")


if __name__ == "__main__":
    app()
