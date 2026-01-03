@echo off
:: 切换到当前脚本所在的目录
cd /d "%~dp0"

echo ==========================================
echo    Travel Map AI 启动器 (定制版)
echo ==========================================

echo.
echo [1/2] 正在启动后端...
echo 目标 Python: "D:\travel map\.venv\Scripts\python.exe"

:: 关键修改：
:: 1. 路径改为 .venv
:: 2. 因为 "travel map" 有空格，所以整个路径加了引号
:: 3. cmd /k 后面那一长串引号是为了防止路径空格导致命令截断

start "TravelMap_Backend" cmd /k ""D:\travel map\.venv\Scripts\python.exe" -m uvicorn main:app --reload"

echo.
echo [2/2] 等待服务启动 (3秒)...
timeout /t 3 /nobreak >nul

echo.
echo [3/3] 打开网页...
start index.html

echo.
echo 启动完成！
timeout /t 5 >nul
exit