@echo off
REM Q_DLP 视频下载器启动脚本
REM 使用项目虚拟环境中的Python

echo 启动 Q_DLP 视频下载器...
echo 使用虚拟环境: %~dp0.venv

REM 切换到项目根目录
cd /d "%~dp0"

REM 使用虚拟环境中的Python启动程序
".venv\Scripts\python.exe" "src\main.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 程序启动失败，错误代码: %ERRORLEVEL%
    pause
)