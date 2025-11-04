#!/bin/bash
# Q_DLP 视频下载器启动脚本 (Linux/macOS)
# 使用项目虚拟环境中的Python

echo "====================================="
echo "    Q_DLP 视频下载器"
echo "====================================="
echo

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 检查虚拟环境是否存在
if [ ! -f ".venv/bin/python" ]; then
    echo "❌ 错误: 虚拟环境不存在"
    echo "💡 请先运行: python -m venv .venv"
    echo "💡 然后安装依赖: .venv/bin/pip install -r config/requirements.txt"
    exit 1
fi

echo "🚀 正在启动程序..."
echo "📁 工作目录: $(pwd)"
echo "🐍 Python: .venv/bin/python"
echo

# 使用虚拟环境中的Python启动程序
.venv/bin/python src/main.py

# 检查退出状态
if [ $? -ne 0 ]; then
    echo
    echo "❌ 程序启动失败，错误代码: $?"
    exit 1
fi