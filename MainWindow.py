import logging
import os
import re
from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLineEdit, QToolBar, QListWidget, QSizePolicy, QDialog, QDialogButtonBox, QLabel,
    QHBoxLayout, QPushButton, QStatusBar, QMessageBox, QFileDialog, QComboBox, QProgressBar, QTextEdit
)

from db import DownloadRecord, clear_downloads_at_db, gen_id, get_all_downloads_at_db
from dlp import DownloadThread


def clean_ansi_codes(text: str) -> str:
    """清理文本中的ANSI颜色代码和控制字符"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


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

        # 设置字体
        font = QFont()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(10)
        self.setFont(font)

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
        # 使用当前时间戳作为id
        import time
        record = DownloadRecord(id=int(time.time()), url=url)
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


class AddTaskDialog(QDialog):
    """自定义添加任务对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加下载任务")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icon', 'add.ico')))
        self.resize(400, 150)

        layout = QVBoxLayout()

        # URL 输入框
        url_layout = QHBoxLayout()
        url_label = QLabel("视频URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入B站或YouTube视频链接")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)

        # 格式选择
        format_layout = QHBoxLayout()
        format_label = QLabel("下载格式:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["最高质量", "1080P", "720P", "480P", "仅音频"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)

        # 按钮组
        button_box = QDialogButtonBox()
        self.add_button = button_box.addButton("添加到队列", QDialogButtonBox.ButtonRole.AcceptRole)
        self.download_button = button_box.addButton("立即下载", QDialogButtonBox.ButtonRole.ApplyRole)
        self.cancel_button = button_box.addButton("取消", QDialogButtonBox.ButtonRole.RejectRole)

        # 布局
        layout.addLayout(url_layout)
        layout.addLayout(format_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

        # 连接信号
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 单独处理立即下载按钮
        button_box.clicked.connect(self.handle_button_click)

    def handle_button_click(self, button):
        """处理按钮点击事件"""
        if button == self.download_button:
            self.download_now()

    def download_now(self):
        """立即下载按钮的处理函数"""
        url = self.get_url()
        url_type = url_checker(url)

        if not url or not url_type:
            QMessageBox.warning(self, "无效URL", "请输入有效的B站或YouTube视频链接!")
            return

        # 判断是否仅音频
        audio_only = self.get_format() == "仅音频"
        
        # 获取主窗口并调用下载函数
        main_window = self.parent()
        # 确保找到正确的MainWindow实例
        while main_window and not hasattr(main_window, 'start_download'):
            main_window = main_window.parent()
        
        if main_window and hasattr(main_window, 'start_download'):
            try:
                main_window.start_download(url, audio_only)
                self.accept()  # 关闭对话框
            except Exception as e:
                QMessageBox.warning(self, "错误", f"下载功能调用失败: {e}")
        else:
            QMessageBox.warning(self, "错误", "无法找到主窗口或下载功能!")

    def get_url(self):
        return self.url_input.text().strip()

    def get_format(self):
        return self.format_combo.currentText()


class MToolbarWidget(QWidget):
    def __init__(self, task_list: DownloadTaskListWidget, main_window=None):
        super().__init__(main_window)
        self.task_list = task_list
        self.main_window = main_window  # 保存主窗口引用
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._create_toolbar(layout)
        self.setObjectName("toolbar")

    def _create_toolbar(self, layout):
        toolbar = QToolBar("顶部工具栏")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        # 创建动作
        self.add_task_action = QAction(QIcon.fromTheme("list-add"), "添加", self)
        self.run_task_action = QAction(QIcon.fromTheme("media-playback-start"), "开始", self)
        self.pause_task_action = QAction(QIcon.fromTheme("media-playback-pause"), "暂停", self)
        self.remove_task_action = QAction(QIcon.fromTheme("edit-delete"), "删除", self)
        self.clear_task_action = QAction(QIcon.fromTheme("edit-clear"), "清空", self)

        # 添加动作到工具栏
        toolbar.addAction(self.add_task_action)
        toolbar.addAction(self.run_task_action)
        toolbar.addAction(self.pause_task_action)
        toolbar.addSeparator()
        toolbar.addAction(self.remove_task_action)
        toolbar.addAction(self.clear_task_action)

        # 添加伸缩空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # 右侧按钮
        self.settings_action = QAction(QIcon.fromTheme("preferences-system"), "设置", self)
        self.help_action = QAction(QIcon.fromTheme("help-contents"), "帮助", self)

        toolbar.addAction(self.settings_action)
        toolbar.addAction(self.help_action)

        # 连接信号
        self.add_task_action.triggered.connect(self.add_task_dialog)
        self.run_task_action.triggered.connect(self.start_selected_download)
        self.remove_task_action.triggered.connect(self.remove_selected_tasks)
        self.clear_task_action.triggered.connect(self.clear_all_tasks)
        self.help_action.triggered.connect(self.show_help)

        layout.addWidget(toolbar)

    def add_task_dialog(self):
        dialog = AddTaskDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url = dialog.get_url()
            url_type = url_checker(url)

            if not url or not url_type:
                QMessageBox.warning(self, "无效URL", "请输入有效的B站或YouTube视频链接!")
                return

            download_format = dialog.get_format()
            self.task_list.add_url_to_records(url)

            # 在实际应用中，这里可以添加格式选择逻辑
            logging.info(f"添加任务: URL={url}, 格式={download_format}")

    def start_selected_download(self):
        """开始下载选中的任务"""
        # 检查主窗口引用
        if not self.main_window or not hasattr(self.main_window, 'start_download'):
            QMessageBox.warning(self, "错误", "无法找到主窗口或下载功能!")
            return

        selected_items = self.task_list.selectedItems()
        if not selected_items:
            # 如果没有选中项，尝试下载第一个任务
            if self.task_list.count() > 0 and len(self.task_list.download_records) > 0:
                first_record = self.task_list.download_records[0]
                try:
                    # 判断是否为仅音频下载（根据格式选择）
                    audio_only = False  # 这里可以根据实际需求调整
                    self.main_window.start_download(first_record.url, audio_only)
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"下载功能调用失败: {e}")
            else:
                QMessageBox.information(self, "提示", "请先添加下载任务!")
            return

        # 下载选中的第一个任务
        selected_item = selected_items[0]
        item_text = selected_item.text()
        
        # 从任务列表中找到对应的记录
        item_row = self.task_list.row(selected_item)
        if 0 <= item_row < len(self.task_list.download_records):
            record = self.task_list.download_records[item_row]
            try:
                # 判断是否为仅音频下载
                audio_only = False  # 这里可以根据实际需求调整
                self.main_window.start_download(record.url, audio_only)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"下载功能调用失败: {e}")
        else:
            QMessageBox.warning(self, "错误", "无法找到对应的下载记录!")

    def remove_selected_tasks(self):
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的任务!")
            return

        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除选中的 {len(selected_items)} 个任务吗?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                self.task_list.takeItem(self.task_list.row(item))

    def clear_all_tasks(self):
        if self.task_list.count() == 0:
            return

        reply = QMessageBox.question(
            self, '确认清空',
            '确定要清空所有任务吗?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.task_list.clear()

    def show_help(self):
        help_text = """
        <h3>B站视频下载器使用说明</h3>
        <p>1. 点击"添加"按钮输入B站或YouTube视频链接</p>
        <p>2. 选择下载格式后添加到队列</p>
        <p>3. 点击"开始"按钮开始下载</p>
        <p>4. 下载完成后视频将保存在默认下载目录</p>
        """
        QMessageBox.information(self, "帮助", help_text)


class MainWindow(QMainWindow):
    """
    PyQt6 主窗口：集成了 URL 输入、保存路径选择、格式下拉、日志显示、进度条 等控件，
    并通过 DownloadThread 调用 yt_dlp API 下载视频/音频。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("B站视频下载器")
        icon_path = os.path.join(os.path.dirname(__file__), 'icon', 'q_dlp.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(800, 600)

        # 加载样式表
        self.load_stylesheet()

        # 创建中央 Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 垂直主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 创建工具栏和任务列表
        self.top_tool_bar_task_list = DownloadTaskListWidget()
        self.top_tool_bar = MToolbarWidget(self.top_tool_bar_task_list, self)

        # 添加下载路径选择
        path_layout = QHBoxLayout()
        path_label = QLabel("下载路径:")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择下载保存路径...")
        # 设置默认路径为项目根目录下的download文件夹
        default_download_path = os.path.join(os.path.dirname(__file__), 'download')
        self.path_edit.setText(default_download_path)
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_download_path)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)

        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        # 添加日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("下载日志将在这里显示...")

        # 添加状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("准备就绪")

        # 下载线程相关属性
        self.download_thread = None
        self.is_downloading = False

        # 添加到主布局
        main_layout.addWidget(self.top_tool_bar)
        main_layout.addLayout(path_layout)
        main_layout.addWidget(self.top_tool_bar_task_list)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.log_text)

    def load_stylesheet(self):
        """加载样式表"""
        try:
            style_path = os.path.join(os.path.dirname(__file__), 'style.qss')
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            logging.error("加载样式表失败: %s", e)

    def browse_download_path(self):
        """选择下载路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.path_edit.text())
        if path:
            self.path_edit.setText(path)

    def start_download(self, url: str, audio_only: bool = False):
        """开始下载指定URL的视频/音频"""
        if self.is_downloading:
            QMessageBox.warning(self, "下载中", "当前已有下载任务正在进行中，请等待完成后再试!")
            return

        download_path = self.path_edit.text().strip()
        if not download_path:
            QMessageBox.warning(self, "路径错误", "请先选择下载保存路径!")
            return

        # 检查路径是否存在
        if not os.path.exists(download_path):
            try:
                os.makedirs(download_path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "路径错误", f"无法创建下载目录: {e}")
                return

        # 创建并启动下载线程
        self.download_thread = DownloadThread(url, download_path, audio_only)
        
        # 连接信号
        self.download_thread.log_signal.connect(self.on_log_update)
        self.download_thread.progress_signal.connect(self.on_progress_update)
        self.download_thread.finished_signal.connect(self.on_download_finished)

        # 更新UI状态
        self.is_downloading = True
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.status_bar.showMessage(f"正在下载: {url}")
        
        # 启动线程
        self.download_thread.start()
        
        # 记录到日志
        self.log_text.append(f"[开始下载] {url}")
        logging.info(f"开始下载: {url}, 保存路径: {download_path}, 仅音频: {audio_only}")

    def on_log_update(self, message: str):
        """处理下载日志更新"""
        # 清理ANSI颜色代码
        clean_message = clean_ansi_codes(message)
        self.log_text.append(clean_message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def on_progress_update(self, progress: int):
        """处理下载进度更新"""
        self.progress_bar.setValue(progress)

    def on_download_finished(self, success: bool, message: str):
        """处理下载完成"""
        self.is_downloading = False
        
        if success:
            self.log_text.append(f"[成功] {message}")
            self.status_bar.showMessage("下载完成")
            QMessageBox.information(self, "下载完成", f"下载成功完成!\n{message}")
        else:
            self.log_text.append(f"[失败] {message}")
            self.status_bar.showMessage("下载失败")
            QMessageBox.critical(self, "下载失败", f"下载失败:\n{message}")
        
        # 清理下载线程
        if self.download_thread:
            self.download_thread.deleteLater()
            self.download_thread = None

    def closeEvent(self, event):
        """
        窗口关闭事件，保存下载记录并清理资源。
        """
        # 如果有正在进行的下载，询问用户是否继续
        if self.is_downloading:
            reply = QMessageBox.question(
                self, '确认退出',
                '当前有下载任务正在进行，确定要退出吗？\n（退出将中断下载）',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            # 中断下载线程
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.terminate()
                self.download_thread.wait(3000)  # 等待最多3秒

        self.top_tool_bar_task_list.save_download_records_on_app_exit()
        super().closeEvent(event)
