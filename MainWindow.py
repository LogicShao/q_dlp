import os

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox,
    QTextEdit, QComboBox, QProgressBar
)

from dlp import DownloadThread


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
        self.resize(600, 450)

        # 创建中央 Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 垂直主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ——— 第 1 行：URL 输入 ———
        url_layout = QHBoxLayout()
        lbl_url = QLabel("视频 URL：")
        lbl_url.setMinimumWidth(70)
        self.edit_url = QLineEdit()
        self.edit_url.setPlaceholderText("在此输入 B 站或 YouTube 视频链接")
        url_layout.addWidget(lbl_url)
        url_layout.addWidget(self.edit_url)
        main_layout.addLayout(url_layout)

        # ——— 第 2 行：保存目录选择 ———
        path_layout = QHBoxLayout()
        lbl_path = QLabel("保存目录：")
        lbl_path.setMinimumWidth(70)
        self.edit_path = QLineEdit()
        self.edit_path.setPlaceholderText("下载目录")
        btn_browse = QPushButton("浏览")
        btn_browse.clicked.connect(self.on_browse)
        path_layout.addWidget(lbl_path)
        path_layout.addWidget(self.edit_path)
        path_layout.addWidget(btn_browse)
        main_layout.addLayout(path_layout)

        # 设置默认下载目录为项目根目录下的 ./download
        project_dir = os.path.dirname(os.path.abspath(__file__))
        default_download_dir = os.path.join(project_dir, 'download')
        self.edit_path.setText(default_download_dir)

        # ——— 第 3 行：格式选择 ———
        fmt_layout = QHBoxLayout()
        lbl_fmt = QLabel("下载格式：")
        lbl_fmt.setMinimumWidth(70)
        self.combo_fmt = QComboBox()
        self.combo_fmt.addItems(["视频+音频 (默认)", "仅音频 (mp3)"])
        fmt_layout.addWidget(lbl_fmt)
        fmt_layout.addWidget(self.combo_fmt)
        fmt_layout.addStretch(1)
        main_layout.addLayout(fmt_layout)

        # ——— 第 4 行：开始下载按钮 ———
        btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("开始下载")
        self.btn_download.setFixedHeight(32)
        self.btn_download.clicked.connect(self.on_download)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_download)
        btn_layout.addStretch(1)
        main_layout.addLayout(btn_layout)

        # ——— 第 5 区：日志输出 ———
        lbl_log = QLabel("下载日志：")
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        main_layout.addWidget(lbl_log)
        main_layout.addWidget(self.text_log, stretch=1)

        # ——— 第 6 区：进度条 ———
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        main_layout.addWidget(self.progress)

        # 保存当前下载线程的引用，防止被垃圾回收
        self.download_thread = None

    @pyqtSlot()
    def on_browse(self):
        """
        打开文件夹选择对话框，让用户选择下载保存目录。
        """
        directory = QFileDialog.getExistingDirectory(
            self, "选择保存目录", os.getcwd(),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if directory:
            self.edit_path.setText(directory)

    @pyqtSlot()
    def on_download(self):
        """
        “开始下载”按钮的槽函数：
        - 验证输入
        - 禁用按钮，清空日志、重置进度条
        - 启动 DownloadThread
        """
        url = self.edit_url.text().strip()
        save_path = self.edit_path.text().strip()
        fmt_index = self.combo_fmt.currentIndex()  # 0: 视频+音频，1: 仅音频

        if not url:
            QMessageBox.warning(self, "提示", "请先输入视频 URL。")
            return
        if not save_path:
            QMessageBox.warning(self, "提示", "请先选择保存目录。")
            return

        # 禁用按钮，防止重复点击
        self.btn_download.setEnabled(False)
        # 清空日志
        self.text_log.clear()
        # 重置进度条
        self.progress.setValue(0)

        # 创建并启动后台下载线程
        audio_only = (fmt_index == 1)
        self.download_thread = DownloadThread(url, save_path, audio_only)

        # 连接信号
        self.download_thread.log_signal.connect(self.append_log)
        self.download_thread.progress_signal.connect(self.progress.setValue)
        self.download_thread.finished_signal.connect(self.on_finished)

        self.download_thread.start()

    @pyqtSlot(str)
    def append_log(self, message: str):
        """
        接收到下载线程发射的日志后，追加到 QTextEdit 中。
        """
        self.text_log.append(message)

    @pyqtSlot(bool, str)
    def on_finished(self, success: bool, info: str):
        """
        下载线程结束时回调：
        - 把按钮重新启用
        - 弹窗提示结果（可选）
        """
        if success:
            self.text_log.append("\n=== 下载成功 ===")
            QMessageBox.information(self, "提示", "下载完成！")
        else:
            self.text_log.append(f"\n=== 下载失败: {info} ===")
            QMessageBox.critical(self, "错误", f"下载失败：{info}")
        self.btn_download.setEnabled(True)
