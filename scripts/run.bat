@echo off
chcp 65001 >nul
REM Q_DLP 视频下载器启动脚本
REM 使用项目虚拟环境中的Python

echo =====================================
echo    Q_DLP 视频下载器
echo =====================================
echo.

REM 切换到项目根目录
cd /d "%~dp0\.."

REM 检查虚拟环境是否存在
if not exist ".venv\Scripts\python.exe" (
    echo ❌ 错误: 虚拟环境不存在
    echo 💡 请先运行: python -m venv .venv
    echo 💡 然后安装依赖: .venv\Scripts\pip install -r config\requirements.txt
    pause
    exit /b 1
)

echo 🚀 正在启动程序...
echo 📁 工作目录: %CD%
echo 🐍 Python: .venv\Scripts\python.exe
echo.

REM 使用虚拟环境中的Python启动程序
".venv\Scripts\python.exe" "src\main.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 程序启动失败，错误代码: %ERRORLEVEL%
    pause
)