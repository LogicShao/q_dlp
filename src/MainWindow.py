import logging
import os
import re
from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLineEdit, QToolBar, QListWidget, QSizePolicy, QDialog, QDialogButtonBox, QLabel,
    QHBoxLayout, QPushButton, QStatusBar, QMessageBox, QFileDialog, QComboBox, QProgressBar, QTextEdit, QTabWidget,
    QFormLayout, QCheckBox, QSpinBox, QGroupBox
)

from db import DownloadRecord, clear_downloads_at_db, get_all_downloads_at_db
from dlp import DownloadThread
from utils import load_config, save_config, get_config_value, set_config_value, get_icon_path


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


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        # 设置对话框图标
        settings_icon_path = get_icon_path('settings.ico')
        if os.path.exists(settings_icon_path):
            self.setWindowIcon(QIcon(settings_icon_path))
        else:
            self.setWindowIcon(QIcon.fromTheme("preferences-system"))
        self.resize(500, 600)
        self.setModal(True)

        # 加载当前配置
        self.config = load_config()

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 创建选项卡
        tab_widget = QTabWidget()

        # 下载设置选项卡
        download_tab = self.create_download_tab()
        tab_widget.addTab(download_tab, "下载设置")

        # 网络设置选项卡
        network_tab = self.create_network_tab()
        tab_widget.addTab(network_tab, "网络设置")

        # 界面设置选项卡
        ui_tab = self.create_ui_tab()
        tab_widget.addTab(ui_tab, "界面设置")

        # 高级设置选项卡
        advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(advanced_tab, "高级设置")

        # 按钮组
        button_box = QDialogButtonBox()
        self.ok_button = button_box.addButton(
            "确定", QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_button = button_box.addButton(
            "取消", QDialogButtonBox.ButtonRole.RejectRole)
        self.apply_button = button_box.addButton(
            "应用", QDialogButtonBox.ButtonRole.ApplyRole)
        self.reset_button = button_box.addButton(
            "重置", QDialogButtonBox.ButtonRole.ResetRole)

        # 连接信号
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        button_box.clicked.connect(self.handle_button_click)

        # 连接主题预览信号
        self.theme_combo.currentTextChanged.connect(self.preview_theme)

        layout.addWidget(tab_widget)
        layout.addWidget(button_box)

    def create_download_tab(self):
        """创建下载设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 基本下载设置组
        basic_group = QGroupBox("基本设置")
        basic_layout = QFormLayout(basic_group)

        # 默认下载路径
        path_layout = QHBoxLayout()
        self.download_path_edit = QLineEdit()
        self.download_path_edit.setPlaceholderText("选择默认下载路径...")
        path_browse_button = QPushButton("浏览...")
        path_browse_button.clicked.connect(self.browse_download_path)
        path_layout.addWidget(self.download_path_edit)
        path_layout.addWidget(path_browse_button)
        basic_layout.addRow("下载路径:", path_layout)

        # 视频质量
        self.video_quality_combo = QComboBox()
        self.video_quality_combo.addItems(
            ["best", "1080p", "720p", "480p", "worst"])
        basic_layout.addRow("视频质量:", self.video_quality_combo)

        # 音频质量
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(
            ["best", "192k", "128k", "96k", "worst"])
        basic_layout.addRow("音频质量:", self.audio_quality_combo)

        # 视频格式
        self.video_format_combo = QComboBox()
        self.video_format_combo.addItems(["mp4", "webm", "mkv"])
        basic_layout.addRow("视频格式:", self.video_format_combo)

        # 音频格式
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "m4a", "wav", "aac"])
        basic_layout.addRow("音频格式:", self.audio_format_combo)

        # 附加选项组
        options_group = QGroupBox("附加选项")
        options_layout = QVBoxLayout(options_group)

        self.subtitle_checkbox = QCheckBox("下载字幕")
        self.thumbnail_checkbox = QCheckBox("下载封面")

        options_layout.addWidget(self.subtitle_checkbox)
        options_layout.addWidget(self.thumbnail_checkbox)

        layout.addWidget(basic_group)
        layout.addWidget(options_group)
        layout.addStretch()

        return widget

    def create_network_tab(self):
        """创建网络设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 代理设置组
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QFormLayout(proxy_group)

        self.proxy_edit = QLineEdit()
        self.proxy_edit.setPlaceholderText("http://host:port 或留空不使用代理")
        proxy_layout.addRow("代理地址:", self.proxy_edit)

        # 连接设置组
        connection_group = QGroupBox("连接设置")
        connection_layout = QFormLayout(connection_group)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSuffix(" 秒")
        connection_layout.addRow("连接超时:", self.timeout_spin)

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        connection_layout.addRow("重试次数:", self.retry_spin)

        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 5)
        connection_layout.addRow("并发下载数:", self.concurrent_spin)

        layout.addWidget(proxy_group)
        layout.addWidget(connection_group)
        layout.addStretch()

        return widget

    def create_ui_tab(self):
        """创建界面设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 外观设置组
        appearance_group = QGroupBox("外观设置")
        appearance_layout = QFormLayout(appearance_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        appearance_layout.addRow("主题:", self.theme_combo)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh_CN", "en_US"])
        appearance_layout.addRow("语言:", self.language_combo)

        # 日志设置组
        log_group = QGroupBox("日志设置")
        log_layout = QVBoxLayout(log_group)

        self.show_log_checkbox = QCheckBox("显示日志")
        self.auto_clear_log_checkbox = QCheckBox("自动清除日志")

        log_layout.addWidget(self.show_log_checkbox)
        log_layout.addWidget(self.auto_clear_log_checkbox)

        layout.addWidget(appearance_group)
        layout.addWidget(log_group)
        layout.addStretch()

        return widget

    def create_advanced_tab(self):
        """创建高级设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Cookies设置组
        cookies_group = QGroupBox("Cookies设置")
        cookies_layout = QFormLayout(cookies_group)

        self.use_cookies_checkbox = QCheckBox("使用Cookies")
        cookies_layout.addRow("", self.use_cookies_checkbox)

        cookies_file_layout = QHBoxLayout()
        self.cookies_file_edit = QLineEdit()
        self.cookies_file_edit.setPlaceholderText("选择cookies文件...")
        cookies_browse_button = QPushButton("浏览...")
        cookies_browse_button.clicked.connect(self.browse_cookies_file)
        cookies_file_layout.addWidget(self.cookies_file_edit)
        cookies_file_layout.addWidget(cookies_browse_button)
        cookies_layout.addRow("Cookies文件:", cookies_file_layout)

        # 其他高级设置组
        other_group = QGroupBox("其他设置")
        other_layout = QFormLayout(other_group)

        self.user_agent_edit = QLineEdit()
        self.user_agent_edit.setPlaceholderText("自定义User-Agent（留空使用默认）")
        other_layout.addRow("User-Agent:", self.user_agent_edit)

        self.extract_audio_checkbox = QCheckBox("默认提取音频")
        other_layout.addRow("", self.extract_audio_checkbox)

        layout.addWidget(cookies_group)
        layout.addWidget(other_group)
        layout.addStretch()

        return widget

    def load_settings(self):
        """从配置文件加载设置到界面"""
        # 下载设置
        download_config = self.config.get("download", {})
        self.download_path_edit.setText(
            download_config.get("default_path", ""))

        video_quality = download_config.get("video_quality", "best")
        index = self.video_quality_combo.findText(video_quality)
        if index >= 0:
            self.video_quality_combo.setCurrentIndex(index)

        audio_quality = download_config.get("audio_quality", "best")
        index = self.audio_quality_combo.findText(audio_quality)
        if index >= 0:
            self.audio_quality_combo.setCurrentIndex(index)

        video_format = download_config.get("format", "mp4")
        index = self.video_format_combo.findText(video_format)
        if index >= 0:
            self.video_format_combo.setCurrentIndex(index)

        audio_format = download_config.get("audio_format", "mp3")
        index = self.audio_format_combo.findText(audio_format)
        if index >= 0:
            self.audio_format_combo.setCurrentIndex(index)

        self.subtitle_checkbox.setChecked(
            download_config.get("subtitle", False))
        self.thumbnail_checkbox.setChecked(
            download_config.get("thumbnail", True))

        # 网络设置
        network_config = self.config.get("network", {})
        self.proxy_edit.setText(network_config.get("proxy", ""))
        self.timeout_spin.setValue(network_config.get("timeout", 30))
        self.retry_spin.setValue(network_config.get("retry_times", 3))
        self.concurrent_spin.setValue(
            network_config.get("concurrent_downloads", 1))

        # 界面设置
        ui_config = self.config.get("ui", {})
        theme = ui_config.get("theme", "light")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        language = ui_config.get("language", "zh_CN")
        index = self.language_combo.findText(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        self.show_log_checkbox.setChecked(ui_config.get("show_log", True))
        self.auto_clear_log_checkbox.setChecked(
            ui_config.get("auto_clear_log", True))

        # 高级设置
        advanced_config = self.config.get("advanced", {})
        self.use_cookies_checkbox.setChecked(
            advanced_config.get("use_cookies", False))
        self.cookies_file_edit.setText(advanced_config.get("cookies_file", ""))
        self.user_agent_edit.setText(advanced_config.get("user_agent", ""))
        self.extract_audio_checkbox.setChecked(
            advanced_config.get("extract_audio", False))

    def save_settings(self):
        """保存界面设置到配置文件"""
        # 下载设置
        self.config["download"]["default_path"] = self.download_path_edit.text()
        self.config["download"]["video_quality"] = self.video_quality_combo.currentText()
        self.config["download"]["audio_quality"] = self.audio_quality_combo.currentText()
        self.config["download"]["format"] = self.video_format_combo.currentText()
        self.config["download"]["audio_format"] = self.audio_format_combo.currentText()
        self.config["download"]["subtitle"] = self.subtitle_checkbox.isChecked()
        self.config["download"]["thumbnail"] = self.thumbnail_checkbox.isChecked()

        # 网络设置
        self.config["network"]["proxy"] = self.proxy_edit.text()
        self.config["network"]["timeout"] = self.timeout_spin.value()
        self.config["network"]["retry_times"] = self.retry_spin.value()
        self.config["network"]["concurrent_downloads"] = self.concurrent_spin.value()

        # 界面设置
        self.config["ui"]["theme"] = self.theme_combo.currentText()
        self.config["ui"]["language"] = self.language_combo.currentText()
        self.config["ui"]["show_log"] = self.show_log_checkbox.isChecked()
        self.config["ui"]["auto_clear_log"] = self.auto_clear_log_checkbox.isChecked()

        # 高级设置
        self.config["advanced"]["use_cookies"] = self.use_cookies_checkbox.isChecked()
        self.config["advanced"]["cookies_file"] = self.cookies_file_edit.text()
        self.config["advanced"]["user_agent"] = self.user_agent_edit.text()
        self.config["advanced"]["extract_audio"] = self.extract_audio_checkbox.isChecked()

        # 保存配置到文件
        return save_config(self.config)

    def browse_download_path(self):
        """浏览下载路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.download_path_edit.text())
        if path:
            self.download_path_edit.setText(path)

    def browse_cookies_file(self):
        """浏览cookies文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择Cookies文件", self.cookies_file_edit.text(),
            "Text Files (*.txt);;All Files (*)")
        if path:
            self.cookies_file_edit.setText(path)

    def handle_button_click(self, button):
        """处理按钮点击"""
        if button == self.apply_button:
            self.apply_settings()
        elif button == self.reset_button:
            self.reset_settings()

    def apply_settings(self):
        """应用设置"""
        if self.save_settings():
            QMessageBox.information(self, "设置", "设置已保存!")
        else:
            QMessageBox.warning(self, "设置", "保存设置失败!")

    def accept_settings(self):
        """确定并保存设置"""
        if self.save_settings():
            self.accept()
        else:
            QMessageBox.warning(self, "设置", "保存设置失败!")

    def reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self, "重置设置",
            "确定要重置所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            from utils import get_default_config
            self.config = get_default_config()
            self.load_settings()
            QMessageBox.information(self, "重置设置", "已重置为默认设置!")

    def preview_theme(self, theme_name):
        """预览主题效果"""
        try:
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(__file__))

            # 确定样式文件路径
            if theme_name == "dark":
                style_path = os.path.join(
                    project_root, 'config', 'dark_theme.qss')
            else:  # light主题
                style_path = os.path.join(
                    project_root, 'config', 'light_theme.qss')

            # 加载并应用样式
            with open(style_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()

            # 应用到设置对话框
            self.setStyleSheet(stylesheet)

            # 如果有父窗口，也应用到主窗口
            parent_window = self.parent()
            if parent_window and hasattr(parent_window, 'setStyleSheet'):
                parent_window.setStyleSheet(stylesheet)

            logging.info(f"预览{theme_name}主题")

        except Exception as e:
            logging.error(f"预览主题失败: {e}")

    def load_theme_stylesheet(self, theme_name):
        """加载指定主题的样式表内容"""
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))

            if theme_name == "dark":
                style_path = os.path.join(
                    project_root, 'config', 'dark_theme.qss')
            else:
                style_path = os.path.join(
                    project_root, 'config', 'light_theme.qss')

            with open(style_path, 'r', encoding='utf-8') as f:
                return f.read()

        except Exception as e:
            logging.error(f"加载主题样式表失败: {e}")
            return ""


class AddTaskDialog(QDialog):
    """自定义添加任务对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加下载任务")
        # 使用主程序图标
        icon_path = get_icon_path('q_dlp.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(400, 150)

        # 加载配置
        self.config = load_config()

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

        # 根据配置设置默认格式
        default_extract_audio = self.config.get(
            "advanced", {}).get("extract_audio", False)
        if default_extract_audio:
            self.format_combo.setCurrentText("仅音频")

        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)

        # 按钮组
        button_box = QDialogButtonBox()
        self.add_button = button_box.addButton(
            "添加到队列", QDialogButtonBox.ButtonRole.AcceptRole)
        self.download_button = button_box.addButton(
            "立即下载", QDialogButtonBox.ButtonRole.ApplyRole)
        self.cancel_button = button_box.addButton(
            "取消", QDialogButtonBox.ButtonRole.RejectRole)

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
        self.run_task_action = QAction(
            QIcon.fromTheme("media-playback-start"), "开始", self)
        self.pause_task_action = QAction(
            QIcon.fromTheme("media-playback-pause"), "暂停", self)
        self.remove_task_action = QAction(
            QIcon.fromTheme("edit-delete"), "删除", self)
        self.clear_task_action = QAction(
            QIcon.fromTheme("edit-clear"), "清空", self)

        # 添加动作到工具栏
        toolbar.addAction(self.add_task_action)
        toolbar.addAction(self.run_task_action)
        toolbar.addAction(self.pause_task_action)
        toolbar.addSeparator()
        toolbar.addAction(self.remove_task_action)
        toolbar.addAction(self.clear_task_action)

        # 添加伸缩空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # 右侧按钮
        self.settings_action = QAction(
            QIcon.fromTheme("preferences-system"), "设置", self)
        self.help_action = QAction(
            QIcon.fromTheme("help-contents"), "帮助", self)

        toolbar.addAction(self.settings_action)
        toolbar.addAction(self.help_action)

        # 连接信号
        self.add_task_action.triggered.connect(self.add_task_dialog)
        self.run_task_action.triggered.connect(self.start_selected_download)
        self.remove_task_action.triggered.connect(self.remove_selected_tasks)
        self.clear_task_action.triggered.connect(self.clear_all_tasks)
        self.settings_action.triggered.connect(self.show_settings)
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
                    self.main_window.start_download(
                        first_record.url, audio_only)
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

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.main_window if self.main_window else self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 设置保存后，刷新主窗口的配置
            if self.main_window:
                self.main_window.reload_config()


class MainWindow(QMainWindow):
    """
    PyQt6 主窗口：集成了 URL 输入、保存路径选择、格式下拉、日志显示、进度条 等控件，
    并通过 DownloadThread 调用 yt_dlp API 下载视频/音频。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("B站视频下载器")
        # 设置应用程序图标
        icon_path = get_icon_path('q_dlp.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(800, 600)

        # 加载配置
        self.config = load_config()

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
        # 从配置加载默认下载路径
        default_download_path = self.config.get("download", {}).get("default_path",
                                                                    os.path.join(os.path.dirname(__file__), 'download'))
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
        """根据配置加载主题样式表"""
        try:
            # 获取主题设置
            theme = self.config.get("ui", {}).get("theme", "light")

            # 确定样式文件路径
            project_root = os.path.dirname(os.path.dirname(__file__))
            if theme == "dark":
                style_path = os.path.join(
                    project_root, 'config', 'dark_theme.qss')
            else:  # 默认使用light主题
                style_path = os.path.join(
                    project_root, 'config', 'light_theme.qss')

            # 加载样式文件
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

            logging.info(f"已加载{theme}主题")

        except Exception as e:
            logging.error("加载样式表失败: %s", e)
            # 如果加载失败，尝试使用默认的浅色主题
            try:
                project_root = os.path.dirname(os.path.dirname(__file__))
                default_style_path = os.path.join(
                    project_root, 'config', 'light_theme.qss')
                with open(default_style_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
                logging.info("已使用默认浅色主题")
            except Exception as fallback_error:
                logging.error("加载默认样式表也失败: %s", fallback_error)

    def reload_config(self):
        """重新加载配置并应用到界面"""
        self.config = load_config()

        # 更新下载路径
        default_download_path = self.config.get("download", {}).get("default_path",
                                                                    os.path.join(os.path.dirname(__file__), 'download'))
        self.path_edit.setText(default_download_path)

        # 重新加载主题样式
        self.load_stylesheet()

        # 可以在这里添加更多UI更新逻辑
        logging.info("配置已重新加载")

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

        # 创建并启动下载线程，传递配置
        self.download_thread = DownloadThread(
            url, download_path, audio_only, self.config)

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
