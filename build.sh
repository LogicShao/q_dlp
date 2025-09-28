#!/bin/bash

echo "====================================="
echo "      Q_DLP 项目构建脚本 (Linux/Mac)"
echo "====================================="
echo

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 未找到虚拟环境，请先运行: python -m venv .venv"
    exit 1
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source .venv/bin/activate

# 检查依赖
echo "🔄 检查并安装依赖..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

# 安装打包工具
echo "🔄 安装打包工具..."
pip install pyinstaller
if [ $? -ne 0 ]; then
    echo "❌ PyInstaller 安装失败"
    exit 1
fi

# 清理之前的构建文件
echo "🧹 清理构建文件..."
rm -rf build dist *.spec

# 开始打包
echo "📦 开始打包应用程序..."
pyinstaller \
    --onefile \
    --windowed \
    --name=Q_DLP \
    --icon=icon/q_dlp.ico \
    --add-data="icon:icon" \
    --add-data="download:download" \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=yt_dlp \
    --hidden-import=sqlite3 \
    main.py

if [ $? -ne 0 ]; then
    echo "❌ 打包失败"
    exit 1
fi

# 检查结果
if [ -f "dist/Q_DLP" ]; then
    echo "✅ 打包成功！"
    echo "📁 可执行文件位置: $(pwd)/dist/Q_DLP"
    echo "📏 文件大小: $(ls -lh dist/Q_DLP | awk '{print $5}')"
    
    # 添加执行权限
    chmod +x dist/Q_DLP
else
    echo "❌ 打包失败，未找到输出文件"
    exit 1
fi

echo
echo "====================================="
echo "         构建完成"
echo "====================================="
echo
echo "💡 提示："
echo "  - 可执行文件：dist/Q_DLP"
echo "  - 可以将此文件复制到其他Linux/Mac电脑运行"
echo "  - 首次运行会在同目录创建必要的文件夹"
echo

# 询问是否运行测试
read -p "🚀 是否现在运行测试？(y/n): " choice
if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    echo "🔄 启动程序测试..."
    ./dist/Q_DLP
fi