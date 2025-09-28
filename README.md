# Q_DLP - 视频下载器

<div align="center">

![Q_DLP Logo](icon/q_dlp.ico)

一个基于 PyQt6 和 yt-dlp 的现代化视频下载工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.9.0-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-2025.5.22-red.svg)](https://github.com/yt-dlp/yt-dlp)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## ✨ 特性

- 🎥 **多平台支持**：支持 Bilibili、YouTube 等主流视频平台
- 🎵 **多格式下载**：支持视频和仅音频下载，多种清晰度选择
- 🖥️ **现代化界面**：基于 PyQt6 的直观用户界面
- 📊 **实时进度**：实时显示下载进度和详细日志
- 📝 **任务管理**：支持批量添加、管理下载任务
- 💾 **历史记录**：自动保存下载历史，支持数据库管理
- 🔧 **智能路径**：自动创建下载目录，支持自定义保存路径
- 📦 **一键打包**：支持 PyInstaller 打包为独立可执行文件

## 📸 预览

### 主界面
![主界面预览](temp/screenshot_main.png)

### 下载界面
![下载界面预览](temp/screenshot_download.png)

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Windows 10+ / macOS 10.14+ / Linux (Ubuntu 18.04+)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/LogicShao/q_dlp.git
cd q_dlp
```

2. **创建虚拟环境**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **运行程序**
```bash
python main.py
```

## 📋 使用说明

### 基本操作

1. **添加下载任务**
   - 点击工具栏的"添加"按钮
   - 输入视频 URL（支持 B站、YouTube）
   - 选择下载格式和质量
   - 点击"添加到队列"或"立即下载"

2. **开始下载**
   - 选择队列中的任务
   - 点击"开始"按钮
   - 实时查看下载进度和日志

3. **管理任务**
   - 删除不需要的任务
   - 清空整个下载队列
   - 查看下载历史记录

### 支持的网站

| 平台 | 支持状态 | 格式支持 |
|------|----------|----------|
| Bilibili | ✅ | 视频 + 音频 |
| YouTube | ✅ | 视频 + 音频 |
| YouTube Music | ✅ | 音频 |

### 下载格式选项

- **最高质量**：下载可用的最高画质
- **1080P**：1920x1080 分辨率
- **720P**：1280x720 分辨率  
- **480P**：854x480 分辨率
- **仅音频**：提取音频为 MP3 格式

## 🔧 配置说明

### 自定义下载路径

默认下载路径为项目根目录下的 `download/` 文件夹，可以通过以下方式修改：

1. 在主界面点击"浏览..."按钮选择新路径
2. 或直接在路径输入框中输入路径

### 数据库管理

程序使用 SQLite 数据库存储下载历史：

- 数据库文件：`download_history.db`
- 支持备份和恢复
- 自动清理和优化

```python
# 数据库操作示例
from db import get_download_stats, backup_database

# 获取下载统计
stats = get_download_stats()
print(f"总下载数：{stats['total_count']}")
print(f"成功率：{stats['success_rate']:.1f}%")

# 备份数据库
backup_database("backup_20231001.db")
```

## 📦 打包部署

### 使用 PyInstaller 打包

1. **安装 PyInstaller**
```bash
pip install pyinstaller
```

2. **创建规格文件**
```bash
pyi-makespec --onefile --windowed --name=Q_DLP main.py
```

3. **编辑 spec 文件** (可选)
```python
# Q_DLP.spec
a = Analysis(
    ['main.py'],
    datas=[
        ('icon', 'icon'),
        ('download', 'download'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'yt_dlp',
    ],
)
```

4. **执行打包**
```bash
pyinstaller Q_DLP.spec
```

5. **获取可执行文件**
生成的文件位于 `dist/Q_DLP.exe`

### 批处理脚本

项目提供了便捷的打包脚本：

**Windows (build.bat)**
```batch
@echo off
echo 开始打包 Q_DLP...
call .venv\Scripts\activate
pyinstaller --onefile --windowed --name=Q_DLP --icon=icon/q_dlp.ico main.py
echo 打包完成！可执行文件位于: dist\Q_DLP.exe
pause
```

## 🛠️ 开发指南

### 项目结构

```
q_dlp/
├── main.py              # 应用程序入口
├── MainWindow.py        # 主窗口界面
├── dlp.py              # 下载核心逻辑
├── db.py               # 数据库操作
├── utils.py            # 工具函数
├── style.qss           # 界面样式
├── requirements.txt    # 依赖清单
├── icon/              # 图标资源
├── download/          # 默认下载目录
└── temp/              # 临时文件
```

### 核心模块

#### MainWindow.py
- 主界面实现
- 任务列表管理
- 下载进度显示

#### dlp.py
- yt-dlp 封装
- 下载线程管理
- 进度回调处理

#### db.py
- SQLite 数据库操作
- 下载记录管理
- 数据统计分析

#### utils.py
- 路径管理工具
- 资源文件处理
- 通用辅助函数

### 添加新功能

1. **添加新的视频平台支持**
```python
# 在 MainWindow.py 的 url_checker 函数中添加新平台
def url_checker(url: str) -> Optional[str]:
    # 添加新平台的 URL 模式匹配
    new_platform_patterns = [
        r'^https?://(www\.)?newplatform\.com/video/[\w]+'
    ]
    
    for pattern in new_platform_patterns:
        if re.match(pattern, url):
            return 'newplatform'
```

2. **自定义下载后处理**
```python
# 在 dlp.py 中的 DownloadThread 类添加处理逻辑
def run(self):
    # ... 现有下载逻辑 ...
    
    # 添加下载后处理
    if self.post_process:
        self.custom_post_process(filename)
```

### 测试

```bash
# 运行单元测试
python -m pytest tests/

# 测试数据库功能
python db.py test

# 测试界面
python main.py
```

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 贡献方式

1. **报告 Bug**：在 Issues 中描述问题
2. **功能建议**：提出新功能想法
3. **代码贡献**：提交 Pull Request
4. **文档改进**：完善使用文档

### 开发流程

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 编码规范
- 添加适当的注释和文档字符串
- 确保新功能有相应的测试
- 保持代码简洁可读

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载库
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 跨平台GUI框架
- [FFmpeg](https://ffmpeg.org/) - 多媒体处理工具

## 📞 联系方式

- **作者**：LogicShao
- **邮箱**：[your-email@example.com]
- **项目链接**：https://github.com/LogicShao/q_dlp

## 🔗 相关链接

- [使用教程](docs/tutorial.md)
- [API 文档](docs/api.md)
- [常见问题](docs/faq.md)
- [更新日志](CHANGELOG.md)

---

<div align="center">

**如果这个项目对您有帮助，请给它一个 ⭐**

Made with ❤️ by LogicShao

</div>