REM packaging/zip_release.bat
@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set "VER=%1"
if "%VER%"=="" set "VER=dev"

set "ZIP_NAME=手写生成器-v%VER%.zip"
set "SOURCE_DIR=%~dp0dist\手写生成器"

if not exist "%SOURCE_DIR%" (
    echo ❌ 未找到产物目录: %SOURCE_DIR%
    echo    请先运行 build.bat
    exit /b 1
)

echo 正在压缩...
powershell -Command "Compress-Archive -Path '%SOURCE_DIR%\*' -DestinationPath '%~dp0dist\%ZIP_NAME%' -Force"

if exist "%~dp0dist\%ZIP_NAME%" (
    echo ✓ 生成: dist\%ZIP_NAME%
    echo   体积:
    dir "%~dp0dist\%ZIP_NAME%" | find ".zip"
) else (
    echo ❌ 压缩失败
    exit /b 1
)
