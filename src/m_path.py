import os
import sys


def resource_path(relative_path):
    """兼容 PyInstaller 打包后和开发环境的资源路径"""
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
