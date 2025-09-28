# Project Info

**项目名称**: Q_DLP - 视频下载器  
**版本**: 1.0.0  
**作者**: LogicShao  
**创建时间**: 2025年9月28日  

## 技术栈

- **界面框架**: PyQt6 6.9.0
- **下载引擎**: yt-dlp 2025.5.22  
- **数据库**: SQLite3
- **图像处理**: Pillow 11.2.1
- **SVG支持**: CairoSVG 2.8.2

## 支持平台

- ✅ Bilibili
- ✅ YouTube  
- ✅ YouTube Music

## 文件结构

```
q_dlp/
├── 📄 main.py              # 程序入口
├── 🖼️ MainWindow.py        # 主界面
├── ⬇️ dlp.py              # 下载核心  
├── 🗄️ db.py               # 数据库
├── 🔧 utils.py            # 工具函数
├── 🎨 style.qss           # 样式表
├── 📋 requirements.txt    # 依赖清单
├── 📁 icon/               # 图标资源
├── 📁 download/           # 下载目录
├── 📁 docs/               # 文档目录
├── 🔨 build.bat           # Windows构建脚本
└── 🔨 build.sh            # Linux/Mac构建脚本
```

## 快速开始

1. **环境准备**
   ```bash
   git clone https://github.com/LogicShao/q_dlp.git
   cd q_dlp
   python -m venv .venv
   ```

2. **安装依赖**  
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac  
   source .venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python main.py
   ```

4. **打包发布**
   ```bash
   # Windows
   build.bat
   
   # Linux/Mac
   chmod +x build.sh && ./build.sh
   ```

## 核心功能

- 🎥 **视频下载**: 支持多平台视频下载
- 🎵 **音频提取**: 支持仅音频下载  
- 📊 **实时监控**: 显示下载进度和日志
- 📝 **任务管理**: 批量添加和管理下载任务
- 💾 **历史记录**: 自动保存下载历史
- 🎯 **智能识别**: 自动识别视频平台和格式

## 使用统计

- 📦 **可执行文件大小**: ~15-20MB
- ⚡ **启动时间**: <3秒  
- 💾 **内存占用**: ~50-100MB
- 🔋 **支持的最大并发**: 1个任务（稳定性考虑）

---

*更多详细信息请查看 [README.md](README.md)*