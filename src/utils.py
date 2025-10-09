"""
工具函数模块
提供资源路径管理、配置管理等通用功能
"""
import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any


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
    if hasattr(sys, '_MEIPASS'):
        # 打包后使用可执行文件所在目录的download文件夹
        exe_dir = os.path.dirname(sys.executable)
        download_dir = os.path.join(exe_dir, 'download')
    else:
        # 开发环境使用项目根目录的download文件夹
        project_root = os.path.dirname(os.path.dirname(__file__))
        download_dir = os.path.join(project_root, 'download')

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


def get_icon_path(icon_name: str) -> str:
    """获取图标文件路径"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后的环境
        return os.path.join(sys._MEIPASS, 'icon', icon_name)
    else:
        # 开发环境
        project_root = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(project_root, 'icon', icon_name)


def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "download": {
            "default_path": get_download_path(),
            "video_quality": "best",  # best, 1080p, 720p, 480p, worst
            "audio_quality": "best",  # best, 192k, 128k, 96k, worst
            "format": "mp4",  # mp4, webm, mkv
            "audio_format": "mp3",  # mp3, m4a, wav, aac
            "subtitle": False,  # 是否下载字幕
            "thumbnail": True,  # 是否下载封面
        },
        "network": {
            "proxy": "",  # 代理设置，格式: http://host:port
            "timeout": 30,  # 连接超时时间（秒）
            "retry_times": 3,  # 重试次数
            "concurrent_downloads": 1,  # 并发下载数
        },
        "ui": {
            "theme": "dark",  # light, dark
            "language": "zh_CN",  # zh_CN, en_US
            "show_log": True,  # 是否显示日志
            "auto_clear_log": True,  # 是否自动清除日志
        },
        "advanced": {
            "use_cookies": False,  # 是否使用cookies
            "cookies_file": "",  # cookies文件路径
            "user_agent": "",  # 自定义User-Agent
            "extract_audio": False,  # 是否提取音频
        }
    }


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = get_config_path()

    # 如果配置文件不存在，返回默认配置并创建文件
    if not os.path.exists(config_path):
        default_config = get_default_config()
        save_config(default_config)
        return default_config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 合并默认配置，确保所有字段都存在
        default_config = get_default_config()
        merged_config = merge_config(default_config, config)

        return merged_config

    except Exception as e:
        print(f"加载配置文件失败: {e}，使用默认配置")
        return get_default_config()


def save_config(config: Dict[str, Any]) -> bool:
    """保存配置文件"""
    config_path = get_config_path()

    try:
        # 确保配置目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

        return True

    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False


def merge_config(default_config: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
    """合并用户配置和默认配置，确保所有字段都存在"""
    merged = default_config.copy()

    for key, value in user_config.items():
        if key in merged:
            if isinstance(value, dict) and isinstance(merged[key], dict):
                merged[key] = merge_config(merged[key], value)
            else:
                merged[key] = value
        else:
            merged[key] = value

    return merged


def get_config_value(key_path: str, default=None) -> Any:
    """获取配置值，支持嵌套键路径，如 'download.video_quality'"""
    config = load_config()

    keys = key_path.split('.')
    value = config

    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def set_config_value(key_path: str, value: Any) -> bool:
    """设置配置值，支持嵌套键路径"""
    config = load_config()

    keys = key_path.split('.')
    current = config

    try:
        # 遍历到倒数第二级
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 设置最后一级的值
        current[keys[-1]] = value

        return save_config(config)

    except Exception as e:
        print(f"设置配置值失败: {e}")
        return False
