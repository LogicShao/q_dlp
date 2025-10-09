#!/bin/bash
# Q_DLP 视频下载器启动脚本 (Linux/macOS)
# 使用项目虚拟环境中的Python

echo "启动 Q_DLP 视频下载器..."
echo "使用虚拟环境: $(pwd)/.venv"

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 使用虚拟环境中的Python启动程序
if [ -f ".venv/bin/python" ]; then
    ".venv/bin/python" "src/main.py"
else
    echo "错误: 虚拟环境不存在或Python不可用"
    exit 1
fi