@echo off
setlocal enabledelayedexpansion
chcp 65001

echo ===============================================
echo       Q_DLP 代码格式化工具 (Windows)
echo ===============================================
echo.

:: 检查虚拟环境
if not exist ".venv" (
    echo ❌ 未找到虚拟环境 .venv
    echo 💡 请先运行: python -m venv .venv
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 🔄 激活虚拟环境...
call .venv\Scripts\activate
if %ERRORLEVEL% neq 0 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)

:: 检查参数
set "MODE=format"
set "AGGRESSIVE=1"
set "MAX_LINE_LENGTH=88"

if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="--dry-run" set "MODE=dry-run"
if "%1"=="-d" set "MODE=dry-run"
if "%1"=="--install" set "MODE=install"
if "%1"=="--config" set "MODE=config"
if "%1"=="--stats" set "MODE=stats"

:: 根据模式执行不同操作
if "%MODE%"=="install" goto :install_autopep8
if "%MODE%"=="config" goto :create_config
if "%MODE%"=="stats" goto :show_stats
if "%MODE%"=="dry-run" goto :dry_run_format
goto :format_code

:install_autopep8
echo 🔄 安装 autopep8...
pip install autopep8
if %ERRORLEVEL% neq 0 (
    echo ❌ autopep8 安装失败
    pause
    exit /b 1
)
echo ✅ autopep8 安装成功
goto :end

:create_config
echo 🔧 创建 autopep8 配置文件...
(
echo [tool:autopep8]
echo max_line_length = 88
echo aggressive = 1
echo in-place = true
echo recursive = true
echo exclude = .venv,__pycache__,.git,.idea,.vscode,build,dist,temp
) > .autopep8
echo ✅ 配置文件 .autopep8 已创建
goto :end

:show_stats
echo 📊 代码统计信息:
python format_code.py --stats
goto :end

:dry_run_format
echo 🔍 预览模式 - 检查需要格式化的文件...
python format_code.py --dry-run --aggressive=%AGGRESSIVE% --max-line-length=%MAX_LINE_LENGTH%
echo.
echo 💡 这是预览模式，文件未被修改
echo 💡 要执行实际格式化，请运行: format_code.bat
goto :end

:format_code
echo 🐍 开始格式化 Python 代码...
echo.

:: 检查 autopep8 是否安装
autopep8 --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 未找到 autopep8，正在安装...
    pip install autopep8
    if %ERRORLEVEL% neq 0 (
        echo ❌ autopep8 安装失败
        echo 💡 请手动运行: pip install autopep8
        pause
        exit /b 1
    )
    echo ✅ autopep8 安装成功
    echo.
)

:: 执行格式化
python format_code.py --aggressive=%AGGRESSIVE% --max-line-length=%MAX_LINE_LENGTH%
if %ERRORLEVEL% neq 0 (
    echo ❌ 格式化过程中出现错误
    pause
    exit /b 1
)

echo.
echo ✅ 代码格式化完成！
echo 💡 建议运行测试确保代码功能正常: python -m pytest
goto :end

:show_help
echo 用法: format_code.bat [选项]
echo.
echo 选项:
echo   无参数          执行代码格式化
echo   --dry-run, -d   预览模式，显示需要修改的内容但不修改文件
echo   --install       只安装 autopep8
echo   --config        创建 .autopep8 配置文件
echo   --stats         显示代码统计信息
echo   --help, -h      显示此帮助信息
echo.
echo 示例:
echo   format_code.bat                # 格式化所有代码
echo   format_code.bat --dry-run      # 预览需要修改的内容
echo   format_code.bat --install      # 安装 autopep8
echo   format_code.bat --config       # 创建配置文件
echo   format_code.bat --stats        # 显示统计信息
goto :end

:end
pause