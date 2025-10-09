@echo off
chcp 65001
echo =====================================
echo       Q_DLP 项目构建脚本
echo =====================================
echo.

:: 切换到项目根目录
cd /d "%~dp0\.."

:: 检查虚拟环境
if not exist ".venv" (
    echo ❌ 未找到虚拟环境，请先运行: python -m venv .venv
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 🔄 激活虚拟环境...
call .venv\Scripts\activate

:: 检查依赖
echo 🔄 检查并安装依赖...
# 检查并安装依赖...
pip install -r config/requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

:: 安装打包工具
echo 🔄 安装打包工具...
pip install pyinstaller
if %ERRORLEVEL% neq 0 (
    echo ❌ PyInstaller 安装失败
    pause
    exit /b 1
)

:: 清理之前的构建文件
echo 🧹 清理构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

:: 开始打包
echo 📦 开始打包应用程序...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name=Q_DLP ^
    --icon=icon/q_dlp.ico ^
    --add-data="icon;icon" ^
    --add-data="config;config" ^
    --add-data="download;download" ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=yt_dlp ^
    --hidden-import=sqlite3 ^
    src/main.py

if %ERRORLEVEL% neq 0 (
    echo ❌ 打包失败
    pause
    exit /b 1
)

:: 检查结果
if exist "dist\Q_DLP.exe" (
    echo ✅ 打包成功！
    echo 📁 可执行文件位置: %CD%\dist\Q_DLP.exe
    echo 📏 文件大小:
    dir "dist\Q_DLP.exe" | findstr "Q_DLP.exe"
) else (
    echo ❌ 打包失败，未找到输出文件
    pause
    exit /b 1
)

echo.
echo =====================================
echo          构建完成
echo =====================================
echo.
echo 💡 提示：
echo   - 可执行文件：dist\Q_DLP.exe
echo   - 可以将此文件复制到其他电脑运行
echo   - 首次运行会在同目录创建必要的文件夹
echo.

:: 询问是否运行测试
set /p choice="🚀 是否现在运行测试？(y/n): "
if /i "%choice%"=="y" (
    echo 🔄 启动程序测试...
    "dist\Q_DLP.exe"
)

pause