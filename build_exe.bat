@echo off
chcp 65001 > nul
echo.
echo =======================================================
echo Building Feishu Finance Assistant (Standalone Version)...
echo =======================================================
echo.

:: 1. Check PyInstaller
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] PyInstaller not found. Installing...
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
)

:: 2. Clean
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.spec del *.spec

:: 3. Build
echo [INFO] Packaging CW.py...
pyinstaller --noconfirm --onedir --console --name "Feishu_Finance_Assistant" --clean --hidden-import=lark_oapi --hidden-import=pandas --hidden-import=openpyxl CW.py

:: 4. Copy
echo [INFO] Copying resources...
set DIST_DIR=dist\Feishu_Finance_Assistant

if exist partner_aliases.json copy partner_aliases.json "%DIST_DIR%\" >nul
if exist category_rules.json copy category_rules.json "%DIST_DIR%\" >nul
if exist subject_mapping.json copy subject_mapping.json "%DIST_DIR%\" >nul
if exist ai_category_cache.json copy ai_category_cache.json "%DIST_DIR%\" >nul
if exist "使用手册_小白必读.txt" copy "使用手册_小白必读.txt" "%DIST_DIR%\" >nul
if exist README.md copy README.md "%DIST_DIR%\" >nul
if exist .env copy .env "%DIST_DIR%\.env.example" >nul
if exist .env copy .env "%DIST_DIR%\" >nul

echo.
echo =======================================================
echo Build Complete!
echo Program Location: %CD%\%DIST_DIR%\Feishu_Finance_Assistant.exe
echo =======================================================
echo.
pause
