import os
import re

from PyQt6.QtCore import QThread, pyqtSignal
from yt_dlp import YoutubeDL


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

    def __init__(self, url: str, path: str, audio_only: bool = False):
        super().__init__()
        self.url = url
        self.path = path
        self.audio_only = audio_only

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
                percent_str = clean_ansi_codes(d.get('_percent_str', '')).strip()
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

        ydl_opts = {
            'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'progress_hooks': [hook],
            'quiet': True,
            'no_warnings': True,
        }

        if self.audio_only:
            # 仅下载音频并转为 mp3
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # 下载最佳画质+音质并合并成 mp4
            ydl_opts.update({
                'format': 'bestvideo+bestaudio',
                'merge_output_format': 'mp4',
            })

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            # 下载成功
            self.finished_signal.emit(True, "下载完成")
        except Exception as e:
            self.log_signal.emit(f"[错误] 下载失败: {e}")
            self.finished_signal.emit(False, f"下载失败: {e}")
