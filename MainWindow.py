import logging
import os
import re
from typing import Optional

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLineEdit, QToolBar, QListWidget, QSizePolicy, QDialog, QDialogButtonBox
)

from db import DownloadRecord, clear_downloads_at_db, gen_id, get_all_downloads_at_db


def url_checker(url: str) -> Optional[str]:
    """
    检查输入的 URL 是否为有效的 Bilibili 或 YouTube 链接。
    返回:
        'bilibili' | 'youtube' 如果合法
        None 如果无效
    """
    url = url.strip()

    # YouTube: 支持 youtu.be 和 youtube.com
    youtube_patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://youtu\.be/[\w-]+'
    ]

    # Bilibili: 支持 www.bilibili.com/video/BVxxx 和 avxxx
    bilibili_patterns = [
        r'^https?://(www\.)?bilibili\.com/video/(BV[\w]+)',
        r'^https?://(www\.)?bilibili\.com/video/(av\d+)',
        r'^https?://b23\.tv/[\w]+'
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return 'youtube'

    for pattern in bilibili_patterns:
        if re.match(pattern, url):
            return 'bilibili'

    return None


class DownloadTaskListWidget(QListWidget):
    """
    自定义的 QListWidget，用于显示下载任务列表。
    可以在此基础上添加更多功能，如右键菜单、拖拽排序等。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setObjectName("DListWidget")
        self.setStyleSheet("""
            QListWidget#DListWidget {
                background-color: #f0f0f0;
                border: 1px solid #dcdcdc;
                border-radius: 1px;
            }
        """)

        self.download_records: list[DownloadRecord] = []
        for record in get_all_downloads_at_db():
            self.download_records.append(record)
            self.addItem(f"[已加载] {record.url}")
        clear_downloads_at_db()
        logging.info("已加载下载记录: %d 条", len(self.download_records))

    def add_download_record(self, record: DownloadRecord):
        """
        添加下载记录到列表和数据库。
        :param record: DownloadRecord 实例
        """
        self.download_records.append(record)
        self.addItem(f"[已加入] {record.url}")
        logging.info("添加下载记录: %s", record)

    def add_url_to_records(self, url: str):
        """
        添加下载记录到列表和数据库。
        """
        record = DownloadRecord(id=gen_id(), url=url)
        self.download_records.append(record)
        self.addItem(f"[已加入] {record.url}")
        logging.info("添加下载记录: %s", record)

    def save_download_records_on_app_exit(self):
        """
        应用退出时保存下载记录到数据库。
        """
        if not self.download_records:
            return

        for record in self.download_records:
            try:
                record.insert_to_db()
                logging.info("已保存下载记录: %s", record)
            except Exception as e:
                logging.error("保存下载记录失败: %s", e)


class MToolbarWidget(QWidget):
    def __init__(self, task_list: DownloadTaskListWidget, parent=None):
        super().__init__(parent)
        self.task_list = task_list
        self.layout = QVBoxLayout(self)
        self._create_toolbar()

        self.setObjectName("toolbar")
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 1px solid #dcdcdc;
                border-radius: 1px;
            }
            QWidget#toolbar {
                background-color: #16a4fa;
                border-radius: 1px;
            }
            QToolButton {
                background-color: #16a4fa;
                border-radius: 1px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #e6f7ff;
                border-color: #40a9ff;
            }
        """)

    def _create_toolbar(self):
        toolbar = QToolBar("顶部工具栏")
        toolbar.setIconSize(QSize(16, 16))

        # 左侧按钮（顺序添加）
        add_task_action = QAction(QIcon.fromTheme("list-add"), "添加任务", self)
        add_task_action.triggered.connect(self.add_task_dialog)

        run_task_action = QAction(QIcon.fromTheme("media-playback-start"), "开始下载", self)
        pause_task_action = QAction(QIcon.fromTheme("media-playback-pause"), "暂停任务", self)
        remove_task_action = QAction(QIcon.fromTheme("edit-delete"), "移除任务", self)

        toolbar.addAction(add_task_action)
        toolbar.addAction(run_task_action)
        toolbar.addAction(pause_task_action)
        toolbar.addAction(remove_task_action)

        # 实现右对齐
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # 右侧按钮
        search_action = QAction(QIcon.fromTheme("edit-find"), "查找任务", self)
        settings_icon_path = os.path.join(os.path.dirname(__file__), 'icon', 'settings.ico')
        settings_action = QAction(QIcon(settings_icon_path), "设置", self)

        toolbar.addAction(search_action)
        toolbar.addAction(settings_action)

        self.layout.addWidget(toolbar)

    def add_task_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("添加下载任务")
        layout = QVBoxLayout()

        url_input = QLineEdit()
        url_input.setPlaceholderText("请输入视频 URL")
        layout.addWidget(url_input)

        button_box = QDialogButtonBox()
        button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Apply
        )
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        def on_button_clicked(button):
            logging.info("button clicked: %s", button.text())

            role = button_box.buttonRole(button)
            url = url_input.text().strip()
            url_type = url_checker(url)

            if not url or not url_type:
                logging.warning("无效的 URL: %s", url)
                dialog.reject()
                return

            if role == QDialogButtonBox.ButtonRole.AcceptRole:  # Ok
                self.task_list.addItem(f"[已加入] {url}")
                logging.info("添加任务: %s", url)
                dialog.accept()
            elif role == QDialogButtonBox.ButtonRole.ApplyRole:  # Apply as "加入列表"
                self.task_list.addItem(f"[等待下载] {url}")
                logging.info("加入列表: %s", url)
                dialog.accept()
            else:
                dialog.reject()

        button_box.clicked.connect(on_button_clicked)
        dialog.exec()


class MainWindow(QMainWindow):
    """
    PyQt6 主窗口：集成了 URL 输入、保存路径选择、格式下拉、日志显示、进度条 等控件，
    并通过 DownloadThread 调用 yt_dlp API 下载视频/音频。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("q_dlp 下载器")
        icon_path = os.path.join(os.path.dirname(__file__), 'icon', 'q_dlp.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(500, 350)

        # 创建中央 Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 垂直主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.top_tool_bar_task_list = DownloadTaskListWidget()
        self.top_tool_bar = MToolbarWidget(self.top_tool_bar_task_list, self)
        main_layout.addWidget(self.top_tool_bar)
        main_layout.addWidget(self.top_tool_bar_task_list)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
                border: 1px solid #dcdcdc;
            }
        """)

    def closeEvent(self, event):
        """
        窗口关闭事件，保存下载记录。
        """
        self.top_tool_bar_task_list.save_download_records_on_app_exit()
        super().closeEvent(event)
