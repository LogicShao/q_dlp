import os
import re

from PyQt6.QtCore import QThread, pyqtSignal
from yt_dlp import YoutubeDL
from typing import Dict, Any


def clean_ansi_codes(text: str) -> str:
    """清理文本中的ANSI颜色代码和控制字符"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


class DownloadThread(QThread):
    """
    后台下载线程，使用 yt_dlp Python API。
    进度、日志和完成情况都会以信号的形式发射给 UI。
    """
    # 用于传递日志（字符串，每一行）
    log_signal = pyqtSignal(str)
    # 用于更新进度条（整数，0~100）
    progress_signal = pyqtSignal(int)
    # 用于告知下载结束（bool: 是否成功, str: 信息）
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, url: str, path: str, audio_only: bool = False, config: Dict[str, Any] = None):
        super().__init__()
        self.url = url
        self.path = path
        self.audio_only = audio_only
        self.config = config or {}

    def run(self):
        # 1. 确保下载目录存在
        if not os.path.isdir(self.path):
            try:
                os.makedirs(self.path, exist_ok=True)
            except Exception as e:
                self.log_signal.emit(f"[错误] 无法创建下载目录: {e}")
                self.finished_signal.emit(False, f"无法创建下载目录: {e}")
                return

        def hook(d):
            status = d.get('status')
            if status == 'downloading':
                # 清理ANSI颜色代码
                percent_str = clean_ansi_codes(
                    d.get('_percent_str', '')).strip()
                speed_str = clean_ansi_codes(d.get('_speed_str', ''))
                eta_str = clean_ansi_codes(d.get('_eta_str', ''))

                self.log_signal.emit(
                    f"[下载中] {percent_str} | 速度: {speed_str} | 剩余: {eta_str}")
                try:
                    percent_float = d.get('_percent_float', 0.0)
                    self.progress_signal.emit(int(percent_float))
                except Exception:
                    pass
            elif status == 'finished':
                filename = d.get('filename', '')
                self.log_signal.emit(f"[完成] 文件保存为: {filename}")
                self.progress_signal.emit(100)

        # 从配置获取设置
        download_config = self.config.get('download', {})
        network_config = self.config.get('network', {})
        advanced_config = self.config.get('advanced', {})

        ydl_opts = {
            'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'progress_hooks': [hook],
            'quiet': True,
            'no_warnings': True,
        }

        # 网络设置
        if network_config.get('proxy'):
            ydl_opts['proxy'] = network_config['proxy']

        if network_config.get('timeout'):
            ydl_opts['socket_timeout'] = network_config['timeout']

        # Cookies设置
        if advanced_config.get('use_cookies') and advanced_config.get('cookies_file'):
            cookies_file = advanced_config['cookies_file']
            if os.path.exists(cookies_file):
                ydl_opts['cookiefile'] = cookies_file

        # User-Agent设置
        if advanced_config.get('user_agent'):
            ydl_opts['http_headers'] = {
                'User-Agent': advanced_config['user_agent']}

        # 字幕设置
        if download_config.get('subtitle'):
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True

        # 缩略图设置
        if download_config.get('thumbnail'):
            ydl_opts['writethumbnail'] = True

        if self.audio_only:
            # 仅下载音频
            audio_quality = download_config.get('audio_quality', 'best')
            audio_format = download_config.get('audio_format', 'mp3')

            if audio_quality == 'best':
                format_selector = 'bestaudio/best'
            elif audio_quality == 'worst':
                format_selector = 'worstaudio/worst'
            else:
                # 具体比特率，如 192k
                format_selector = f'bestaudio[abr<={audio_quality.replace("k", "")}]/best'

            ydl_opts.update({
                'format': format_selector,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': audio_quality if audio_quality not in ['best', 'worst'] else '192',
                }],
            })
        else:
            # 下载视频
            video_quality = download_config.get('video_quality', 'best')
            video_format = download_config.get('format', 'mp4')

            if video_quality == 'best':
                format_selector = 'bestvideo+bestaudio/best'
            elif video_quality == 'worst':
                format_selector = 'worstvideo+worstaudio/worst'
            else:
                # 具体分辨率，如 1080p
                height = video_quality.replace('p', '')
                format_selector = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'

            ydl_opts.update({
                'format': format_selector,
                'merge_output_format': video_format,
            })

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            # 下载成功
            self.finished_signal.emit(True, "下载完成")
        except Exception as e:
            self.log_signal.emit(f"[错误] 下载失败: {e}")
            self.finished_signal.emit(False, f"下载失败: {e}")
