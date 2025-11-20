import os
import re
from typing import Dict, Any

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
    # 用于告知下载结束（bool: 是否成功, str: 信息, str: 文件路径）
    finished_signal = pyqtSignal(bool, str, str)

    def __init__(self, url: str, path: str, audio_only: bool = False, config: Dict[str, Any] = None):
        super().__init__()
        self.url = url
        self.path = path
        self.audio_only = audio_only
        self.config = config or {}
        self.downloaded_file_path = ""  # 记录下载的文件路径

    def run(self):
        # 1. 确保下载目录存在
        if not os.path.isdir(self.path):
            try:
                os.makedirs(self.path, exist_ok=True)
            except Exception as e:
                self.log_signal.emit(f"[错误] 无法创建下载目录: {e}")
                self.finished_signal.emit(False, f"无法创建下载目录: {e}", "")
                return

        def hook(d):
            status = d.get('status')
            if status == 'downloading':
                # 清理ANSI颜色代码
                percent_str = clean_ansi_codes(
                    d.get('_percent_str', '')).strip()
                speed_str = clean_ansi_codes(d.get('_speed_str', ''))
                eta_str = clean_ansi_codes(d.get('_eta_str', ''))

                # 计算进度百分比
                progress_percent = 0
                try:
                    # 优先使用 downloaded_bytes 和 total_bytes 计算精确进度
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)

                    if total > 0:
                        progress_percent = int((downloaded / total) * 100)
                    else:
                        # 回退到使用 _percent_float
                        percent_float = d.get('_percent_float', 0.0)
                        # 判断是否为 0-1 之间的小数,如果是则乘以 100
                        if 0 < percent_float <= 1:
                            progress_percent = int(percent_float * 100)
                        else:
                            progress_percent = int(percent_float)
                except Exception:
                    progress_percent = 0

                self.log_signal.emit(
                    f"[下载中] {percent_str} | 速度: {speed_str} | 剩余: {eta_str}")
                self.progress_signal.emit(progress_percent)
            elif status == 'finished':
                filename = d.get('filename', '')
                # 这里只是下载完成,可能还需要后处理
                self.log_signal.emit(f"[下载完成] 文件: {filename}")
                self.progress_signal.emit(100)

        def postprocessor_hook(d):
            """后处理钩子,获取最终处理后的文件路径"""
            if d.get('status') == 'finished':
                # 后处理完成,这才是最终文件
                final_file = d.get('info_dict', {}).get('filepath') or d.get('filepath', '')
                if final_file:
                    self.downloaded_file_path = final_file
                    self.log_signal.emit(f"[处理完成] 最终文件: {final_file}")

        # 从配置获取设置
        download_config = self.config.get('download', {})
        network_config = self.config.get('network', {})
        advanced_config = self.config.get('advanced', {})

        ydl_opts = {
            'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'progress_hooks': [hook],
            'postprocessor_hooks': [postprocessor_hook],  # 添加后处理钩子
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
                info = ydl.extract_info(self.url, download=True)
                # 如果没有通过postprocessor_hook获取到路径,尝试从info中获取
                if not self.downloaded_file_path:
                    if info:
                        # 尝试多种方式获取最终文件路径
                        self.downloaded_file_path = (
                                info.get('filepath') or
                                info.get('requested_downloads', [{}])[0].get('filepath') or
                                ydl.prepare_filename(info)
                        )
            # 下载成功
            self.finished_signal.emit(True, "下载完成", self.downloaded_file_path)
        except Exception as e:
            self.log_signal.emit(f"[错误] 下载失败: {e}")
            self.finished_signal.emit(False, f"下载失败: {e}", "")
