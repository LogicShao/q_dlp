import logging
import os
import re
from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog, QLabel,
    QFormLayout, QGroupBox, QFileDialog
)

# Fluent Widgets 导入
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, setTheme, Theme,
    LineEdit, PushButton, PrimaryPushButton, ListWidget,
    ProgressBar, TextEdit, ComboBox, CheckBox, SpinBox,
    MessageBox, Dialog, SmoothScrollArea, BodyLabel,
    SubtitleLabel, TitleLabel, FluentIcon as FIF,
    ToolButton, CommandBar, Action, TransparentToolButton,
    InfoBar, InfoBarPosition, StateToolTip, SegmentedWidget,
    CardWidget, TabBar, SettingCardGroup, ExpandSettingCard,
    RangeSettingCard, SwitchSettingCard, OptionsSettingCard,
    PushSettingCard, ScrollArea, setThemeColor
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


class DownloadTaskListWidget(ListWidget):
    """
    自定义的下载任务列表组件，使用 Fluent 风格。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(ListWidget.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

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


class SettingsDialog(Dialog):
    """设置对话框 - 使用 Fluent 风格"""

    def __init__(self, parent=None):
        super().__init__("设置", "配置下载器参数", parent)
        self.resize(950, 680)

        # 加载当前配置
        self.config = load_config()

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """设置界面"""
        # 创建滚动区域
        scroll_area = SmoothScrollArea(self)
        scroll_area.setMinimumSize(850, 520)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        scroll_layout.setContentsMargins(20, 20, 20, 20)

        # 下载设置组
        download_group = self.create_download_group()
        scroll_layout.addWidget(download_group)

        # 网络设置组
        network_group = self.create_network_group()
        scroll_layout.addWidget(network_group)

        # 界面设置组
        ui_group = self.create_ui_group()
        scroll_layout.addWidget(ui_group)

        # 高级设置组
        advanced_group = self.create_advanced_group()
        scroll_layout.addWidget(advanced_group)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        # 添加到对话框布局
        self.textLayout.addWidget(scroll_area)

        # 按钮组
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        # 连接信号
        self.yesButton.clicked.connect(self.accept_settings)
        self.cancelButton.clicked.connect(self.reject)

    def create_download_group(self):
        """创建下载设置组"""
        group = CardWidget()
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        # 标题
        title = SubtitleLabel("下载设置")
        title.setMinimumHeight(40)
        layout.addWidget(title)

        # 基本设置
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 10, 0, 10)
        form_layout.setVerticalSpacing(15)

        # 默认下载路径
        path_layout = QHBoxLayout()
        self.download_path_edit = LineEdit()
        self.download_path_edit.setPlaceholderText("选择默认下载路径...")
        self.download_path_edit.setMinimumHeight(40)
        path_browse_button = PushButton("浏览", group)
        path_browse_button.setMinimumHeight(40)
        path_browse_button.clicked.connect(self.browse_download_path)
        path_layout.addWidget(self.download_path_edit)
        path_layout.addWidget(path_browse_button)

        path_label = BodyLabel("下载路径:")
        path_label.setMinimumHeight(40)
        form_layout.addRow(path_label, path_layout)

        # 视频质量
        self.video_quality_combo = ComboBox()
        self.video_quality_combo.addItems(["best", "1080p", "720p", "480p", "worst"])
        self.video_quality_combo.setMinimumHeight(40)
        quality_label = BodyLabel("视频质量:")
        quality_label.setMinimumHeight(40)
        form_layout.addRow(quality_label, self.video_quality_combo)

        # 音频质量
        self.audio_quality_combo = ComboBox()
        self.audio_quality_combo.addItems(["best", "192k", "128k", "96k", "worst"])
        self.audio_quality_combo.setMinimumHeight(40)
        audio_quality_label = BodyLabel("音频质量:")
        audio_quality_label.setMinimumHeight(40)
        form_layout.addRow(audio_quality_label, self.audio_quality_combo)

        # 视频格式
        self.video_format_combo = ComboBox()
        self.video_format_combo.addItems(["mp4", "webm", "mkv"])
        self.video_format_combo.setMinimumHeight(40)
        video_format_label = BodyLabel("视频格式:")
        video_format_label.setMinimumHeight(40)
        form_layout.addRow(video_format_label, self.video_format_combo)

        # 音频格式
        self.audio_format_combo = ComboBox()
        self.audio_format_combo.addItems(["mp3", "m4a", "wav", "aac"])
        self.audio_format_combo.setMinimumHeight(40)
        audio_format_label = BodyLabel("音频格式:")
        audio_format_label.setMinimumHeight(40)
        form_layout.addRow(audio_format_label, self.audio_format_combo)

        layout.addWidget(form_widget)

        # 附加选项
        self.subtitle_checkbox = CheckBox("下载字幕", group)
        self.subtitle_checkbox.setMinimumHeight(35)
        self.thumbnail_checkbox = CheckBox("下载封面", group)
        self.thumbnail_checkbox.setMinimumHeight(35)
        layout.addWidget(self.subtitle_checkbox)
        layout.addWidget(self.thumbnail_checkbox)

        return group

    def create_network_group(self):
        """创建网络设置组"""
        group = CardWidget()
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        # 标题
        title = SubtitleLabel("网络设置")
        title.setMinimumHeight(40)
        layout.addWidget(title)

        # 表单
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 10, 0, 10)
        form_layout.setVerticalSpacing(15)

        # 代理设置
        self.proxy_edit = LineEdit()
        self.proxy_edit.setPlaceholderText("http://host:port 或留空不使用代理")
        self.proxy_edit.setMinimumHeight(40)
        proxy_label = BodyLabel("代理地址:")
        proxy_label.setMinimumHeight(40)
        form_layout.addRow(proxy_label, self.proxy_edit)

        # 连接设置
        self.timeout_spin = SpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSuffix(" 秒")
        self.timeout_spin.setMinimumHeight(40)
        timeout_label = BodyLabel("连接超时:")
        timeout_label.setMinimumHeight(40)
        form_layout.addRow(timeout_label, self.timeout_spin)

        self.retry_spin = SpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setMinimumHeight(40)
        retry_label = BodyLabel("重试次数:")
        retry_label.setMinimumHeight(40)
        form_layout.addRow(retry_label, self.retry_spin)

        self.concurrent_spin = SpinBox()
        self.concurrent_spin.setRange(1, 5)
        self.concurrent_spin.setMinimumHeight(40)
        concurrent_label = BodyLabel("并发下载数:")
        concurrent_label.setMinimumHeight(40)
        form_layout.addRow(concurrent_label, self.concurrent_spin)

        layout.addWidget(form_widget)
        return group

    def create_ui_group(self):
        """创建界面设置组"""
        group = CardWidget()
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        # 标题
        title = SubtitleLabel("界面设置")
        title.setMinimumHeight(40)
        layout.addWidget(title)

        # 表单
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 10, 0, 10)
        form_layout.setVerticalSpacing(15)

        # 主题选择
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["light", "dark", "auto"])
        self.theme_combo.currentTextChanged.connect(self.preview_theme)
        self.theme_combo.setMinimumHeight(40)
        theme_label = BodyLabel("主题:")
        theme_label.setMinimumHeight(40)
        form_layout.addRow(theme_label, self.theme_combo)

        # 语言
        self.language_combo = ComboBox()
        self.language_combo.addItems(["zh_CN", "en_US"])
        self.language_combo.setMinimumHeight(40)
        language_label = BodyLabel("语言:")
        language_label.setMinimumHeight(40)
        form_layout.addRow(language_label, self.language_combo)

        layout.addWidget(form_widget)

        # 日志设置
        self.show_log_checkbox = CheckBox("显示日志", group)
        self.show_log_checkbox.setMinimumHeight(35)
        self.auto_clear_log_checkbox = CheckBox("自动清除日志", group)
        self.auto_clear_log_checkbox.setMinimumHeight(35)
        layout.addWidget(self.show_log_checkbox)
        layout.addWidget(self.auto_clear_log_checkbox)

        return group

    def create_advanced_group(self):
        """创建高级设置组"""
        group = CardWidget()
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        # 标题
        title = SubtitleLabel("高级设置")
        title.setMinimumHeight(40)
        layout.addWidget(title)

        # Cookies设置
        self.use_cookies_checkbox = CheckBox("使用Cookies", group)
        self.use_cookies_checkbox.setMinimumHeight(35)
        layout.addWidget(self.use_cookies_checkbox)

        cookies_file_layout = QHBoxLayout()
        cookies_label = BodyLabel("Cookies文件:")
        cookies_label.setMinimumHeight(40)
        self.cookies_file_edit = LineEdit()
        self.cookies_file_edit.setPlaceholderText("选择cookies文件...")
        self.cookies_file_edit.setMinimumHeight(40)
        cookies_browse_button = PushButton("浏览", group)
        cookies_browse_button.setMinimumHeight(40)
        cookies_browse_button.clicked.connect(self.browse_cookies_file)
        cookies_file_layout.addWidget(cookies_label)
        cookies_file_layout.addWidget(self.cookies_file_edit)
        cookies_file_layout.addWidget(cookies_browse_button)
        layout.addLayout(cookies_file_layout)

        # User-Agent
        ua_layout = QHBoxLayout()
        ua_label = BodyLabel("User-Agent:")
        ua_label.setMinimumHeight(40)
        self.user_agent_edit = LineEdit()
        self.user_agent_edit.setPlaceholderText("自定义User-Agent（留空使用默认）")
        self.user_agent_edit.setMinimumHeight(40)
        ua_layout.addWidget(ua_label)
        ua_layout.addWidget(self.user_agent_edit)
        layout.addLayout(ua_layout)

        # 提取音频选项
        self.extract_audio_checkbox = CheckBox("默认提取音频", group)
        self.extract_audio_checkbox.setMinimumHeight(35)
        layout.addWidget(self.extract_audio_checkbox)

        return group

    def load_settings(self):
        """从配置文件加载设置到界面"""
        # 下载设置
        download_config = self.config.get("download", {})
        self.download_path_edit.setText(download_config.get("default_path", ""))

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

        self.subtitle_checkbox.setChecked(download_config.get("subtitle", False))
        self.thumbnail_checkbox.setChecked(download_config.get("thumbnail", True))

        # 网络设置
        network_config = self.config.get("network", {})
        self.proxy_edit.setText(network_config.get("proxy", ""))
        self.timeout_spin.setValue(network_config.get("timeout", 30))
        self.retry_spin.setValue(network_config.get("retry_times", 3))
        self.concurrent_spin.setValue(network_config.get("concurrent_downloads", 1))

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
        self.auto_clear_log_checkbox.setChecked(ui_config.get("auto_clear_log", True))

        # 高级设置
        advanced_config = self.config.get("advanced", {})
        self.use_cookies_checkbox.setChecked(advanced_config.get("use_cookies", False))
        self.cookies_file_edit.setText(advanced_config.get("cookies_file", ""))
        self.user_agent_edit.setText(advanced_config.get("user_agent", ""))
        self.extract_audio_checkbox.setChecked(advanced_config.get("extract_audio", False))

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

    def accept_settings(self):
        """确定并保存设置"""
        if self.save_settings():
            InfoBar.success(
                title='设置已保存',
                content='配置已成功保存',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.parent()
            )
            self.accept()
        else:
            InfoBar.error(
                title='保存失败',
                content='设置保存失败，请重试',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.parent()
            )

    def preview_theme(self, theme_name):
        """预览主题效果"""
        try:
            if theme_name == "dark":
                setTheme(Theme.DARK)
            elif theme_name == "light":
                setTheme(Theme.LIGHT)
            elif theme_name == "auto":
                setTheme(Theme.AUTO)

            logging.info(f"预览{theme_name}主题")
        except Exception as e:
            logging.error(f"预览主题失败: {e}")


class AddTaskDialog(Dialog):
    """自定义添加任务对话框 - 使用 Fluent 风格"""

    def __init__(self, parent=None):
        super().__init__("添加下载任务", "输入视频链接并选择下载格式", parent)
        self.resize(500, 250)

        # 加载配置
        self.config = load_config()

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # URL 输入框
        url_label = BodyLabel("视频URL:")
        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("请输入B站或YouTube视频链接")
        self.url_input.setClearButtonEnabled(True)

        # 格式选择
        format_label = BodyLabel("下载格式:")
        self.format_combo = ComboBox()
        self.format_combo.addItems(["最高质量", "1080P", "720P", "480P", "仅音频"])

        # 根据配置设置默认格式
        default_extract_audio = self.config.get("advanced", {}).get("extract_audio", False)
        if default_extract_audio:
            self.format_combo.setCurrentText("仅音频")

        # 添加到布局
        self.textLayout.addWidget(url_label)
        self.textLayout.addWidget(self.url_input)
        self.textLayout.addSpacing(10)
        self.textLayout.addWidget(format_label)
        self.textLayout.addWidget(self.format_combo)

        # 按钮
        self.yesButton.setText("添加到队列")
        self.cancelButton.setText("取消")

        # 添加立即下载按钮
        self.download_button = PrimaryPushButton("立即下载", self)
        self.buttonLayout.insertWidget(0, self.download_button)

        # 连接信号
        self.yesButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.download_button.clicked.connect(self.download_now)

    def download_now(self):
        """立即下载按钮的处理函数"""
        url = self.get_url()
        url_type = url_checker(url)

        if not url or not url_type:
            InfoBar.warning(
                title='无效URL',
                content='请输入有效的B站或YouTube视频链接',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.parent()
            )
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
                InfoBar.error(
                    title='下载失败',
                    content=f'下载功能调用失败: {e}',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.parent()
                )
        else:
            InfoBar.error(
                title='错误',
                content='无法找到主窗口或下载功能',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.parent()
            )

    def get_url(self):
        return self.url_input.text().strip()

    def get_format(self):
        return self.format_combo.currentText()


class MainWindow(FluentWindow):
    """
    主窗口：使用 FluentWindow 作为基础，提供现代化的 Fluent Design 风格界面。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Q_DLP - 视频下载器")

        # 设置应用程序图标
        icon_path = get_icon_path('q_dlp.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1000, 700)

        # 加载配置
        self.config = load_config()

        # 设置主题
        self.apply_theme()

        # 下载线程相关属性
        self.download_thread = None
        self.is_downloading = False

        # 创建子界面
        self.downloadInterface = self.create_download_interface()

        # 添加子界面到导航
        self.addSubInterface(self.downloadInterface, FIF.DOWNLOAD, '下载')

        # 添加设置页到底部导航
        self.navigationInterface.addItem(
            routeKey='settings',
            icon=FIF.SETTING,
            text='设置',
            onClick=self.show_settings,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )

        # 添加帮助页到底部导航
        self.navigationInterface.addItem(
            routeKey='help',
            icon=FIF.HELP,
            text='帮助',
            onClick=self.show_help,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )

    def apply_theme(self):
        """应用主题"""
        try:
            theme = self.config.get("ui", {}).get("theme", "light")
            if theme == "dark":
                setTheme(Theme.DARK)
            elif theme == "light":
                setTheme(Theme.LIGHT)
            elif theme == "auto":
                setTheme(Theme.AUTO)

            # 设置主题色（可选）
            # setThemeColor('#0078d4')

            logging.info(f"已应用{theme}主题")
        except Exception as e:
            logging.error(f"应用主题失败: {e}")

    def create_download_interface(self):
        """创建下载界面"""
        interface = QWidget()
        interface.setObjectName("downloadInterface")
        layout = QVBoxLayout(interface)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题
        title = TitleLabel("视频下载")
        layout.addWidget(title)

        # 工具栏
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        # 下载路径选择卡片
        path_card = CardWidget()
        path_layout = QVBoxLayout(path_card)
        path_layout.setContentsMargins(20, 15, 20, 15)

        path_label = SubtitleLabel("下载路径")
        path_layout.addWidget(path_label)

        path_input_layout = QHBoxLayout()
        self.path_edit = LineEdit()
        self.path_edit.setPlaceholderText("选择下载保存路径...")
        self.path_edit.setClearButtonEnabled(True)

        # 从配置加载默认下载路径
        default_download_path = self.config.get("download", {}).get(
            "default_path", os.path.join(os.path.dirname(__file__), 'download'))
        self.path_edit.setText(default_download_path)

        browse_button = PushButton(FIF.FOLDER, "浏览")
        browse_button.clicked.connect(self.browse_download_path)

        path_input_layout.addWidget(self.path_edit)
        path_input_layout.addWidget(browse_button)
        path_layout.addLayout(path_input_layout)

        layout.addWidget(path_card)

        # 任务列表卡片
        task_card = CardWidget()
        task_layout = QVBoxLayout(task_card)
        task_layout.setContentsMargins(20, 15, 20, 15)

        task_label = SubtitleLabel("下载队列")
        task_layout.addWidget(task_label)

        self.task_list = DownloadTaskListWidget()
        task_layout.addWidget(self.task_list)

        layout.addWidget(task_card)

        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 日志显示区域
        log_card = CardWidget()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 15, 20, 15)

        log_label = SubtitleLabel("下载日志")
        log_layout.addWidget(log_label)

        self.log_text = TextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("下载日志将在这里显示...")
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_card)

        return interface

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)

        # 添加任务按钮
        add_button = PrimaryPushButton(FIF.ADD, "添加任务")
        add_button.clicked.connect(self.add_task_dialog)
        toolbar_layout.addWidget(add_button)

        # 开始下载按钮
        start_button = PushButton(FIF.PLAY, "开始")
        start_button.clicked.connect(self.start_selected_download)
        toolbar_layout.addWidget(start_button)

        # 删除任务按钮
        remove_button = PushButton(FIF.DELETE, "删除")
        remove_button.clicked.connect(self.remove_selected_tasks)
        toolbar_layout.addWidget(remove_button)

        # 清空队列按钮
        clear_button = PushButton(FIF.CANCEL, "清空")
        clear_button.clicked.connect(self.clear_all_tasks)
        toolbar_layout.addWidget(clear_button)

        # 添加伸缩空间
        toolbar_layout.addStretch()

        return toolbar

    def add_task_dialog(self):
        """显示添加任务对话框"""
        dialog = AddTaskDialog(self)
        if dialog.exec():
            url = dialog.get_url()
            url_type = url_checker(url)

            if not url or not url_type:
                InfoBar.warning(
                    title='无效URL',
                    content='请输入有效的B站或YouTube视频链接',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return

            download_format = dialog.get_format()
            self.task_list.add_url_to_records(url)

            InfoBar.success(
                title='任务已添加',
                content=f'已将任务添加到下载队列',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

            logging.info(f"添加任务: URL={url}, 格式={download_format}")

    def start_selected_download(self):
        """开始下载选中的任务"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            # 如果没有选中项，尝试下载第一个任务
            if self.task_list.count() > 0 and len(self.task_list.download_records) > 0:
                first_record = self.task_list.download_records[0]
                try:
                    audio_only = False
                    self.start_download(first_record.url, audio_only)
                except Exception as e:
                    InfoBar.error(
                        title='下载失败',
                        content=f'下载功能调用失败: {e}',
                        orient=Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
            else:
                InfoBar.info(
                    title='提示',
                    content='请先添加下载任务',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            return

        # 下载选中的第一个任务
        selected_item = selected_items[0]
        item_row = self.task_list.row(selected_item)
        if 0 <= item_row < len(self.task_list.download_records):
            record = self.task_list.download_records[item_row]
            try:
                audio_only = False
                self.start_download(record.url, audio_only)
            except Exception as e:
                InfoBar.error(
                    title='下载失败',
                    content=f'下载功能调用失败: {e}',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        else:
            InfoBar.error(
                title='错误',
                content='无法找到对应的下载记录',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def remove_selected_tasks(self):
        """删除选中的任务"""
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            InfoBar.info(
                title='提示',
                content='请先选择要删除的任务',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 使用 Fluent MessageBox
        w = MessageBox("确认删除", f"确定要删除选中的 {len(selected_items)} 个任务吗？", self)
        if w.exec():
            for item in selected_items:
                row = self.task_list.row(item)
                self.task_list.takeItem(row)
                # 同时删除对应的记录
                if 0 <= row < len(self.task_list.download_records):
                    self.task_list.download_records.pop(row)

    def clear_all_tasks(self):
        """清空所有任务"""
        if self.task_list.count() == 0:
            return

        w = MessageBox("确认清空", "确定要清空所有任务吗？", self)
        if w.exec():
            self.task_list.clear()
            self.task_list.download_records.clear()

    def browse_download_path(self):
        """选择下载路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.path_edit.text())
        if path:
            self.path_edit.setText(path)

    def start_download(self, url: str, audio_only: bool = False):
        """开始下载指定URL的视频/音频"""
        if self.is_downloading:
            InfoBar.warning(
                title='下载中',
                content='当前已有下载任务正在进行中，请等待完成后再试',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        download_path = self.path_edit.text().strip()
        if not download_path:
            InfoBar.warning(
                title='路径错误',
                content='请先选择下载保存路径',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 检查路径是否存在
        if not os.path.exists(download_path):
            try:
                os.makedirs(download_path, exist_ok=True)
            except Exception as e:
                InfoBar.error(
                    title='路径错误',
                    content=f'无法创建下载目录: {e}',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return

        # 创建并启动下载线程
        self.download_thread = DownloadThread(url, download_path, audio_only, self.config)

        # 连接信号
        self.download_thread.log_signal.connect(self.on_log_update)
        self.download_thread.progress_signal.connect(self.on_progress_update)
        self.download_thread.finished_signal.connect(self.on_download_finished)

        # 更新UI状态
        self.is_downloading = True
        self.progress_bar.setValue(0)
        self.log_text.clear()

        # 启动线程
        self.download_thread.start()

        # 显示状态提示
        self.stateTooltip = StateToolTip('正在下载', '下载任务已开始', self)
        self.stateTooltip.move(self.stateTooltip.getSuitablePos())
        self.stateTooltip.show()

        # 记录到日志
        self.log_text.append(f"[开始下载] {url}")
        logging.info(f"开始下载: {url}, 保存路径: {download_path}, 仅音频: {audio_only}")

    def on_log_update(self, message: str):
        """处理下载日志更新"""
        clean_message = clean_ansi_codes(message)
        self.log_text.append(clean_message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def on_progress_update(self, progress: int):
        """处理下载进度更新"""
        self.progress_bar.setValue(progress)
        if hasattr(self, 'stateTooltip'):
            self.stateTooltip.setContent(f'下载进度: {progress}%')

    def on_download_finished(self, success: bool, message: str):
        """处理下载完成"""
        self.is_downloading = False

        # 关闭状态提示
        if hasattr(self, 'stateTooltip'):
            self.stateTooltip.setState(True)
            self.stateTooltip = None

        if success:
            self.log_text.append(f"[成功] {message}")
            InfoBar.success(
                title='下载完成',
                content=f'下载成功完成！{message}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            self.log_text.append(f"[失败] {message}")
            InfoBar.error(
                title='下载失败',
                content=f'下载失败：{message}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

        # 清理下载线程
        if self.download_thread:
            self.download_thread.deleteLater()
            self.download_thread = None

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # 设置保存后，重新加载配置
            self.reload_config()

    def show_help(self):
        """显示帮助信息"""
        help_text = """<h3>Q_DLP 使用说明</h3>
<p><b>1. 添加下载任务</b></p>
<p>   点击"添加任务"按钮，输入B站或YouTube视频链接</p>
<p><b>2. 选择下载格式</b></p>
<p>   在对话框中选择视频质量或仅下载音频</p>
<p><b>3. 开始下载</b></p>
<p>   点击"开始"按钮或在添加任务时选择"立即下载"</p>
<p><b>4. 查看进度</b></p>
<p>   实时查看下载进度和详细日志</p>
<br>
<p><b>支持的平台：</b>Bilibili、YouTube</p>
<p><b>支持的格式：</b>MP4、MP3、WebM 等</p>"""

        # 创建自定义的帮助对话框
        w = Dialog("帮助", help_text, self)
        w.setTitleBarVisible(True)
        w.resize(600, 500)
        w.yesButton.setText("确定")
        w.cancelButton.hide()  # 隐藏取消按钮
        w.exec()

    def reload_config(self):
        """重新加载配置并应用到界面"""
        self.config = load_config()

        # 更新下载路径
        default_download_path = self.config.get("download", {}).get(
            "default_path", os.path.join(os.path.dirname(__file__), 'download'))
        self.path_edit.setText(default_download_path)

        # 重新应用主题
        self.apply_theme()

        logging.info("配置已重新加载")

    def closeEvent(self, event):
        """
        窗口关闭事件，保存下载记录并清理资源。
        """
        # 如果有正在进行的下载，询问用户是否继续
        if self.is_downloading:
            w = MessageBox(
                '确认退出',
                '当前有下载任务正在进行，确定要退出吗？\n（退出将中断下载）',
                self
            )
            if not w.exec():
                event.ignore()
                return

            # 中断下载线程
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.terminate()
                self.download_thread.wait(3000)

        self.task_list.save_download_records_on_app_exit()
        super().closeEvent(event)
