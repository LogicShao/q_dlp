"""
工具函数模块
提供资源路径管理、配置管理等通用功能
"""
import os
import sys
from pathlib import Path
from typing import Optional


def get_resource_path(relative_path: str) -> str:
    """获取资源文件路径，兼容开发环境和打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后的环境
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # 开发环境
        return os.path.join(os.path.dirname(__file__), relative_path)


def get_app_data_path() -> str:
    """获取应用数据目录路径"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后使用可执行文件所在目录
        exe_dir = os.path.dirname(sys.executable)
        app_data_dir = os.path.join(exe_dir, 'app_data')
    else:
        # 开发环境使用项目根目录
        app_data_dir = os.path.dirname(__file__)

    # 确保目录存在
    os.makedirs(app_data_dir, exist_ok=True)
    return app_data_dir


def get_download_path() -> str:
    """获取默认下载目录路径"""
    download_dir = os.path.join(get_app_data_path(), 'download')
    os.makedirs(download_dir, exist_ok=True)
    return download_dir


def validate_url(url: str) -> bool:
    """验证URL是否有效"""
    if not url or not url.strip():
        return False

    url = url.strip()
    return url.startswith(('http://', 'https://'))


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f}{size_names[i]}"


def ensure_directory(path: str) -> bool:
    """确保目录存在，如不存在则创建"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


def is_packaged() -> bool:
    """检测是否运行在打包后的环境中"""
    return hasattr(sys, '_MEIPASS')


def get_app_version() -> str:
    """获取应用程序版本号"""
    return "1.0.0"


def get_config_path() -> str:
    """获取配置文件路径"""
    config_file = os.path.join(get_app_data_path(), 'config.json')
    return config_file
