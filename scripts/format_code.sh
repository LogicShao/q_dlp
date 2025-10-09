#!/bin/bash

echo "==============================================="
echo "      Q_DLP 代码格式化工具 (Linux/Mac)"
echo "==============================================="
echo

# 默认参数
MODE="format"
AGGRESSIVE=1
MAX_LINE_LENGTH=88

# 解析命令行参数
case "$1" in
    --help|-h)
        MODE="help"
        ;;
    --dry-run|-d)
        MODE="dry-run"
        ;;
    --install)
        MODE="install"
        ;;
    --config)
        MODE="config"
        ;;
    --stats)
        MODE="stats"
        ;;
esac

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 未找到虚拟环境 .venv"
    echo "💡 请先运行: python -m venv .venv"
    exit 1
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 虚拟环境激活失败"
    exit 1
fi

# 根据模式执行不同操作
case "$MODE" in
    help)
        echo "用法: ./format_code.sh [选项]"
        echo
        echo "选项:"
        echo "  无参数          执行代码格式化"
        echo "  --dry-run, -d   预览模式，显示需要修改的内容但不修改文件"
        echo "  --install       只安装 autopep8"
        echo "  --config        创建 .autopep8 配置文件"
        echo "  --stats         显示代码统计信息"
        echo "  --help, -h      显示此帮助信息"
        echo
        echo "示例:"
        echo "  ./format_code.sh                # 格式化所有代码"
        echo "  ./format_code.sh --dry-run      # 预览需要修改的内容"
        echo "  ./format_code.sh --install      # 安装 autopep8"
        echo "  ./format_code.sh --config       # 创建配置文件"
        echo "  ./format_code.sh --stats        # 显示统计信息"
        exit 0
        ;;
        
    install)
        echo "🔄 安装 autopep8..."
        pip install autopep8
        if [ $? -eq 0 ]; then
            echo "✅ autopep8 安装成功"
        else
            echo "❌ autopep8 安装失败"
            exit 1
        fi
        exit 0
        ;;
        
    config)
        echo "🔧 创建 autopep8 配置文件..."
        cat > .autopep8 << EOF
[tool:autopep8]
max_line_length = 88
aggressive = 1
in-place = true
recursive = true
exclude = .venv,__pycache__,.git,.idea,.vscode,build,dist,temp
EOF
        echo "✅ 配置文件 .autopep8 已创建"
        exit 0
        ;;
        
    stats)
        echo "📊 代码统计信息:"
        python format_code.py --stats
        exit 0
        ;;
        
    dry-run)
        echo "🔍 预览模式 - 检查需要格式化的文件..."
        python format_code.py --dry-run --aggressive=$AGGRESSIVE --max-line-length=$MAX_LINE_LENGTH
        echo
        echo "💡 这是预览模式，文件未被修改"
        echo "💡 要执行实际格式化，请运行: ./format_code.sh"
        exit 0
        ;;
        
    format)
        echo "🐍 开始格式化 Python 代码..."
        echo
        
        # 检查 autopep8 是否安装
        if ! command -v autopep8 &> /dev/null; then
            echo "❌ 未找到 autopep8，正在安装..."
            pip install autopep8
            if [ $? -ne 0 ]; then
                echo "❌ autopep8 安装失败"
                echo "💡 请手动运行: pip install autopep8"
                exit 1
            fi
            echo "✅ autopep8 安装成功"
            echo
        fi
        
        # 执行格式化
        python format_code.py --aggressive=$AGGRESSIVE --max-line-length=$MAX_LINE_LENGTH
        if [ $? -eq 0 ]; then
            echo
            echo "✅ 代码格式化完成！"
            echo "💡 建议运行测试确保代码功能正常: python -m pytest"
        else
            echo "❌ 格式化过程中出现错误"
            exit 1
        fi
        ;;
esac