@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ========================================
echo  手写生成器 - Windows 桌面打包
echo ========================================
echo.

set "ROOT=%~dp0.."
cd /d "%ROOT%"

REM ── 1. 前端构建 ──
echo [1/7] 构建前端...
cd /d "%ROOT%\frontendVite"
call npm ci
if errorlevel 1 goto :error
call npm run build
if errorlevel 1 goto :error
cd /d "%ROOT%"
echo ✓ 前端构建完成
echo.

REM ── 2. 准备打包环境（独立 venv）──
echo [2/7] 准备后端打包环境...
if not exist "%ROOT%\packaging\build_venv" (
    python -m venv "%ROOT%\packaging\build_venv"
)
call "%ROOT%\packaging\build_venv\Scripts\activate.bat"
pip install --upgrade pip
pip install -r "%ROOT%\backend\requirements.txt"
pip install pyinstaller pystray pillow
if errorlevel 1 goto :error
echo ✓ 打包环境准备完成
echo.

REM ── 3. 准备 Pandoc ──
echo [3/7] 检查 Pandoc...
if not exist "%ROOT%\packaging\pandoc\pandoc.exe" (
    echo   Pandoc 不存在，正在解压...
    cd /d "%ROOT%\packaging"
    python fetch_pandoc.py
    if errorlevel 1 goto :error
    cd /d "%ROOT%"
) else (
    echo   Pandoc 已存在，跳过
)
echo.

REM ── 4. 清理旧产物 ──
echo [4/7] 清理旧构建...
if exist "%ROOT%\packaging\build" rmdir /s /q "%ROOT%\packaging\build"
if exist "%ROOT%\packaging\dist" rmdir /s /q "%ROOT%\packaging\dist"
echo ✓ 清理完成
echo.

REM ── 5. PyInstaller 打包后端 ──
echo [5/7] 打包后端 backend.exe...
cd /d "%ROOT%\packaging"
pyinstaller backend.spec --noconfirm --distpath "%ROOT%\packaging\dist" --workpath "%ROOT%\packaging\build"
if errorlevel 1 goto :error
cd /d "%ROOT%"
echo ✓ 后端打包完成
echo.

REM ── 6. PyInstaller 打包启动器 ──
echo [6/7] 打包启动器 launcher.exe...
cd /d "%ROOT%\packaging"
pyinstaller launcher.spec --noconfirm --distpath "%ROOT%\packaging\dist" --workpath "%ROOT%\packaging\build"
if errorlevel 1 goto :error
cd /d "%ROOT%"
echo ✓ 启动器打包完成
echo.

REM ── 7. 组装最终产物 ──
echo [7/7] 组装最终产物...
if not exist "%ROOT%\packaging\dist\手写生成器" mkdir "%ROOT%\packaging\dist\手写生成器"
move /Y "%ROOT%\packaging\dist\launcher.exe" "%ROOT%\packaging\dist\手写生成器\手写生成器.exe"
echo ✓ 组装完成
echo.

echo ========================================
echo  打包成功!
echo  产物: %ROOT%\packaging\dist\手写生成器\
echo  双击「手写生成器.exe」即可使用
echo ========================================
goto :eof

:error
echo.
echo 打包失败，请检查上方日志
exit /b 1
