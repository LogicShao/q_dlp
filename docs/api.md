# Q_DLP API 文档

## 📋 概览

Q_DLP 提供了完整的 Python API，允许开发者集成下载功能到自己的应用中，或者通过脚本进行批量操作。

## 🗂️ 模块结构

```python
q_dlp/
├── db.py              # 数据库操作模块
├── dlp.py             # 下载核心模块  
├── utils.py           # 工具函数模块
├── MainWindow.py      # GUI 界面模块
└── main.py           # 应用入口
```

## 📊 数据库操作 (db.py)

### DownloadRecord 类

```python
@dataclass
class DownloadRecord:
    id: int
    url: str
    title: str = ""
    file_path: str = ""
    platform: str = ""
    time: str = ""
    is_finished: bool = False
    created_at: str = ""
    updated_at: str = ""
```

#### 类方法

##### `from_db_row(cls, row) -> DownloadRecord`
从数据库行创建记录实例

```python
record = DownloadRecord.from_db_row(db_row)
```

##### `insert_to_db(self) -> Optional[int]`
将记录插入数据库

```python
record = DownloadRecord(id=1, url="https://example.com/video")
record_id = record.insert_to_db()
```

##### `update_status(self, is_finished: bool, file_path: str = "") -> bool`
更新下载状态

```python
success = record.update_status(True, "/path/to/video.mp4")
```

##### `delete(self) -> bool`
删除当前记录

```python
success = record.delete()
```

### 数据库函数

#### 初始化和配置

##### `init_db() -> bool`
初始化数据库，创建表结构和索引

```python
from db import init_db

if init_db():
    print("数据库初始化成功")
else:
    print("数据库初始化失败")
```

##### `get_db_path() -> str`
获取数据库文件路径

```python
from db import get_db_path
db_path = get_db_path()
print(f"数据库位置: {db_path}")
```

#### 记录操作

##### `insert_download(url, title="", file_path="", platform="", is_finished=False) -> Optional[int]`
插入下载记录

```python
from db import insert_download

record_id = insert_download(
    url="https://www.bilibili.com/video/BV1xx411xxx",
    title="测试视频",
    platform="bilibili",
    is_finished=False
)
```

##### `update_download_status(url: str, is_finished: bool, file_path: str = "") -> bool`
更新下载状态

```python
from db import update_download_status

success = update_download_status(
    url="https://example.com/video",
    is_finished=True,
    file_path="/download/video.mp4"
)
```

##### `delete_download_record(record_id: int) -> bool`
删除指定记录

```python
from db import delete_download_record
success = delete_download_record(123)
```

#### 查询操作

##### `get_all_downloads_at_db() -> List[DownloadRecord]`
获取所有下载记录

```python
from db import get_all_downloads_at_db

records = get_all_downloads_at_db()
for record in records:
    print(f"{record.title}: {'完成' if record.is_finished else '未完成'}")
```

##### `get_downloads_by_platform(platform: str) -> List[DownloadRecord]`
按平台查询记录

```python
from db import get_downloads_by_platform

bilibili_records = get_downloads_by_platform("bilibili")
youtube_records = get_downloads_by_platform("youtube")
```

##### `get_finished_downloads() -> List[DownloadRecord]`
获取已完成的下载

```python
from db import get_finished_downloads

finished = get_finished_downloads()
print(f"已完成下载: {len(finished)} 个")
```

##### `get_unfinished_downloads() -> List[DownloadRecord]`
获取未完成的下载

```python
from db import get_unfinished_downloads

pending = get_unfinished_downloads()
print(f"待下载任务: {len(pending)} 个")
```

##### `search_downloads(keyword: str) -> List[DownloadRecord]`
搜索下载记录

```python
from db import search_downloads

results = search_downloads("Python教程")
for record in results:
    print(f"找到: {record.title}")
```

#### 统计分析

##### `get_download_stats() -> dict`
获取下载统计信息

```python
from db import get_download_stats

stats = get_download_stats()
print(f"总下载数: {stats['total_count']}")
print(f"完成数: {stats['finished_count']}")
print(f"成功率: {stats['success_rate']:.1f}%")
print(f"平台分布: {stats['platform_stats']}")
```

#### 维护操作

##### `clear_downloads_at_db() -> bool`
清空所有下载记录

```python
from db import clear_downloads_at_db

if clear_downloads_at_db():
    print("记录清空成功")
```

##### `backup_database(backup_path: Optional[str] = None) -> bool`
备份数据库

```python
from db import backup_database

# 使用默认文件名备份
backup_database()

# 指定备份文件名
backup_database("my_backup.db")
```

##### `restore_database(backup_path: str) -> bool`
恢复数据库

```python
from db import restore_database

if restore_database("backup.db"):
    print("数据库恢复成功")
```

##### `optimize_database() -> bool`
优化数据库性能

```python
from db import optimize_database

if optimize_database():
    print("数据库优化完成")
```

## 📥 下载核心 (dlp.py)

### DownloadThread 类

继承自 `QThread`，提供异步下载功能。

#### 构造函数

```python
DownloadThread(url: str, path: str, audio_only: bool = False)
```

参数：
- `url`: 视频URL
- `path`: 保存路径
- `audio_only`: 是否仅下载音频

#### 信号 (Signals)

##### `log_signal = pyqtSignal(str)`
日志消息信号

```python
def on_log_message(message):
    print(f"日志: {message}")

thread.log_signal.connect(on_log_message)
```

##### `progress_signal = pyqtSignal(int)`
进度更新信号

```python
def on_progress_update(progress):
    print(f"进度: {progress}%")

thread.progress_signal.connect(on_progress_update)
```

##### `finished_signal = pyqtSignal(bool, str)`
下载完成信号

```python
def on_download_finished(success, message):
    if success:
        print(f"下载成功: {message}")
    else:
        print(f"下载失败: {message}")

thread.finished_signal.connect(on_download_finished)
```

#### 使用示例

```python
from dlp import DownloadThread
from PyQt6.QtCore import QObject

class DownloadManager(QObject):
    def __init__(self):
        super().__init__()
        self.thread = None
    
    def start_download(self, url, save_path, audio_only=False):
        self.thread = DownloadThread(url, save_path, audio_only)
        
        # 连接信号
        self.thread.log_signal.connect(self.on_log)
        self.thread.progress_signal.connect(self.on_progress)
        self.thread.finished_signal.connect(self.on_finished)
        
        # 启动下载
        self.thread.start()
    
    def on_log(self, message):
        print(f"[日志] {message}")
    
    def on_progress(self, progress):
        print(f"[进度] {progress}%")
    
    def on_finished(self, success, message):
        print(f"[完成] 成功={success}, 消息={message}")
        self.thread = None
```

### 辅助函数

##### `clean_ansi_codes(text: str) -> str`
清理ANSI颜色代码

```python
from dlp import clean_ansi_codes

clean_text = clean_ansi_codes("\x1b[32m绿色文字\x1b[0m")
print(clean_text)  # 输出: 绿色文字
```

## 🛠️ 工具函数 (utils.py)

### 路径管理

##### `get_resource_path(relative_path: str) -> str`
获取资源文件路径，兼容开发和打包环境

```python
from utils import get_resource_path

icon_path = get_resource_path("icon/app.ico")
```

##### `get_app_data_path() -> str`
获取应用数据目录

```python
from utils import get_app_data_path

data_dir = get_app_data_path()
print(f"数据目录: {data_dir}")
```

##### `get_download_path() -> str`
获取默认下载目录

```python
from utils import get_download_path

download_dir = get_download_path()
print(f"下载目录: {download_dir}")
```

### 验证和格式化

##### `validate_url(url: str) -> bool`
验证URL格式

```python
from utils import validate_url

if validate_url("https://example.com"):
    print("URL格式正确")
```

##### `format_file_size(size_bytes: int) -> str`
格式化文件大小

```python
from utils import format_file_size

print(format_file_size(1024))      # 输出: 1.0KB
print(format_file_size(1048576))   # 输出: 1.0MB
```

### 系统检测

##### `is_packaged() -> bool`
检测是否运行在打包环境

```python
from utils import is_packaged

if is_packaged():
    print("运行在打包后的环境中")
else:
    print("运行在开发环境中")
```

##### `get_app_version() -> str`
获取应用版本

```python
from utils import get_app_version
print(f"应用版本: {get_app_version()}")
```

## 🖥️ GUI 组件 (MainWindow.py)

### URL 验证

##### `url_checker(url: str) -> Optional[str]`
检查URL并返回平台类型

```python
from MainWindow import url_checker

platform = url_checker("https://www.bilibili.com/video/BV1xx411xxx")
if platform == "bilibili":
    print("这是B站视频")
elif platform == "youtube":
    print("这是YouTube视频")
else:
    print("不支持的平台")
```

### 清理函数

##### `clean_ansi_codes(text: str) -> str`
清理ANSI控制字符

```python
from MainWindow import clean_ansi_codes

clean_text = clean_ansi_codes(log_message)
```

## 📝 完整示例

### 简单下载脚本

```python
#!/usr/bin/env python3
"""
简单的下载脚本示例
"""
import sys
import os
from PyQt6.QtCore import QCoreApplication

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from db import init_db, insert_download, get_download_stats
from dlp import DownloadThread
from utils import get_download_path

class SimpleDownloader:
    def __init__(self):
        self.app = QCoreApplication(sys.argv)
        init_db()  # 初始化数据库
    
    def download_video(self, url, audio_only=False):
        """下载单个视频"""
        download_path = get_download_path()
        
        # 记录到数据库
        record_id = insert_download(url, "", "", "auto")
        if not record_id:
            print("记录添加失败")
            return False
        
        # 创建下载线程
        self.thread = DownloadThread(url, download_path, audio_only)
        
        # 连接信号
        self.thread.log_signal.connect(lambda msg: print(f"[日志] {msg}"))
        self.thread.progress_signal.connect(lambda p: print(f"[进度] {p}%"))
        self.thread.finished_signal.connect(self.on_finished)
        
        print(f"开始下载: {url}")
        self.thread.start()
        
        return True
    
    def on_finished(self, success, message):
        """下载完成回调"""
        if success:
            print(f"✅ 下载成功: {message}")
        else:
            print(f"❌ 下载失败: {message}")
        
        # 显示统计信息
        stats = get_download_stats()
        print(f"📊 统计信息: 总计 {stats['total_count']}, 成功率 {stats['success_rate']:.1f}%")
        
        self.app.quit()
    
    def run(self):
        """运行应用"""
        return self.app.exec()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python simple_download.py <URL> [--audio-only]")
        sys.exit(1)
    
    url = sys.argv[1]
    audio_only = "--audio-only" in sys.argv
    
    downloader = SimpleDownloader()
    
    if downloader.download_video(url, audio_only):
        sys.exit(downloader.run())
    else:
        print("下载启动失败")
        sys.exit(1)
```

### 批量下载脚本

```python
#!/usr/bin/env python3
"""
批量下载脚本示例
"""
import sys
import time
from PyQt6.QtCore import QCoreApplication, QTimer

from db import init_db, insert_download
from dlp import DownloadThread
from utils import get_download_path

class BatchDownloader:
    def __init__(self, urls):
        self.app = QCoreApplication(sys.argv)
        self.urls = urls
        self.current_index = 0
        self.download_path = get_download_path()
        
        init_db()
        
        # 定时器用于处理下载队列
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_next)
    
    def start(self):
        """开始批量下载"""
        print(f"准备下载 {len(self.urls)} 个视频")
        
        # 批量添加到数据库
        for url in self.urls:
            insert_download(url, "", "", "batch")
        
        # 开始处理第一个
        self.process_next()
        return self.app.exec()
    
    def process_next(self):
        """处理下一个下载任务"""
        if self.current_index >= len(self.urls):
            print("✅ 所有任务完成")
            self.app.quit()
            return
        
        url = self.urls[self.current_index]
        print(f"\n📥 [{self.current_index + 1}/{len(self.urls)}] {url}")
        
        # 创建下载线程
        self.thread = DownloadThread(url, self.download_path)
        self.thread.log_signal.connect(lambda msg: print(f"  {msg}"))
        self.thread.finished_signal.connect(self.on_download_finished)
        
        self.thread.start()
    
    def on_download_finished(self, success, message):
        """单个下载完成"""
        if success:
            print(f"  ✅ 成功: {message}")
        else:
            print(f"  ❌ 失败: {message}")
        
        self.current_index += 1
        
        # 等待1秒后处理下一个
        self.timer.start(1000)

if __name__ == "__main__":
    # 示例URL列表
    urls = [
        "https://www.bilibili.com/video/BV1xx411xxx1",
        "https://www.bilibili.com/video/BV1xx411xxx2",
        "https://www.youtube.com/watch?v=example1",
    ]
    
    downloader = BatchDownloader(urls)
    sys.exit(downloader.start())
```

## 📚 错误处理

### 异常类型

API 中可能抛出以下异常：

- `sqlite3.Error`: 数据库操作错误
- `OSError`: 文件系统相关错误
- `ValueError`: 参数错误
- `RuntimeError`: 运行时错误

### 最佳实践

```python
import logging
from db import insert_download, get_all_downloads_at_db

# 配置日志
logging.basicConfig(level=logging.INFO)

try:
    # 数据库操作
    records = get_all_downloads_at_db()
    
    # 添加记录
    record_id = insert_download("https://example.com/video")
    if record_id:
        logging.info(f"记录添加成功，ID: {record_id}")
    else:
        logging.error("记录添加失败")
        
except Exception as e:
    logging.error(f"操作失败: {e}")
```

---

*API文档最后更新：2025年9月28日*