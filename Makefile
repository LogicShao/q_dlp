# Q_DLP 项目 Makefile
# 提供便捷的开发命令

.PHONY: help install format format-check lint test build clean setup

# 默认目标
help:
	@echo "Q_DLP 项目开发命令"
	@echo "=================="
	@echo ""
	@echo "setup          - 初始化开发环境"
	@echo "install        - 安装项目依赖"
	@echo "format         - 格式化所有Python代码"
	@echo "format-check   - 检查代码格式(预览模式)"
	@echo "lint           - 运行代码检查(flake8)"
	@echo "test           - 运行单元测试"
	@echo "build          - 构建可执行文件"
	@echo "clean          - 清理构建文件"
	@echo "run            - 运行应用程序"
	@echo ""

# 初始化开发环境
setup:
	@echo "🔧 初始化开发环境..."
	python -m venv .venv
	@echo "✅ 虚拟环境创建完成"
	@echo "💡 请运行以下命令激活虚拟环境："
	@echo "   Windows: .venv\\Scripts\\activate"
	@echo "   Linux/Mac: source .venv/bin/activate"

# 安装依赖
install:
	@echo "📦 安装项目依赖..."
	pip install -r config/requirements.txt
	pip install autopep8 flake8 pytest
	@echo "✅ 依赖安装完成"

# 格式化代码
format:
	@echo "🐍 格式化Python代码..."
	python scripts/format_code.py
	@echo "✅ 代码格式化完成"

# 检查代码格式
format-check:
	@echo "🔍 检查代码格式..."
	python scripts/format_code.py --dry-run

# 代码检查
lint:
	@echo "🔍 运行代码检查..."
	flake8 --exclude=.venv,__pycache__,.git --max-line-length=88 --select=E,W,F .
	@echo "✅ 代码检查完成"

# 运行测试
test:
	@echo "🧪 运行单元测试..."
	python -m pytest tests/ -v
	@echo "✅ 测试完成"

# 构建应用
build:
	@echo "📦 构建可执行文件..."
ifeq ($(OS),Windows_NT)
	build.bat
else
	./build.sh
endif
	@echo "✅ 构建完成"

# 清理文件
clean:
	@echo "🧹 清理构建文件..."
	rm -rf build/ dist/ *.spec __pycache__/ *.pyc
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ 清理完成"

# 运行应用
run:
	@echo "🚀 启动应用程序..."
	python src/main.py

# 代码统计
stats:
	@echo "📊 代码统计信息..."
	python scripts/format_code.py --stats

# 创建配置文件
config:
	@echo "⚙️ 创建配置文件..."
	python scripts/format_code.py --config

# 完整的代码质量检查
quality: format lint
	@echo "✅ 代码质量检查完成"

# 开发环境完整设置
dev-setup: setup install config
	@echo "✅ 开发环境设置完成"