@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
setlocal enabledelayedexpansion
title Dola Render Gateway
color 0b

echo =====================================================================
echo                DOLA RENDER GATEWAY - KHOI DONG HE THONG
echo =====================================================================
echo.

cd /d "%~dp0"
set "PYTHONPATH=%~dp0"

if exist "%~dp0runtime\browsers" set "PLAYWRIGHT_BROWSERS_PATH=%~dp0runtime\browsers"

if not exist "%~dp0runtime\python\python.exe" goto :use_system_python

set "PY_EXE=%~dp0runtime\python\python.exe"
for /f "tokens=2 delims= " %%v in ('"%PY_EXE%" --version 2^>^&1') do set PY_VER=%%v
echo [1/4] Che do PORTABLE: Da tim thay Python tich hop - !PY_VER!
echo [2/4] Da kich hoat thu vien va Chromium Portable san co.
goto :check_env

:use_system_python
:: 1. Kiem tra Python he thong
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python tren he thong!
    echo Vui long cai dat Python 3.11 hoac 3.12 tu python.org va tich chon "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [1/5] Da tim thay Python: !PY_VER!

:: 2. Kiem tra va tao moi virtual environment
if exist ".venv\Scripts\activate.bat" goto :venv_exists
echo [2/5] Chua co moi truong ao .venv. Dang khoi tao...
python -m venv .venv
if !errorlevel! neq 0 (
    echo [LOI] Khong the tao virtual environment!
    pause
    exit /b 1
)
echo    -^> Khoi tao .venv thanh cong!
goto :activate_venv

:venv_exists
echo [2/5] Da tim thay moi truong ao .venv.

:activate_venv
call .venv\Scripts\activate.bat
set "PY_EXE=python"

:: 3. Kiem tra va cai dat dependencies
echo [3/5] Kiem tra thu vien phu thuoc...
python -c "import fastapi, uvicorn, patchright, PIL, cv2" >nul 2>&1
if !errorlevel! equ 0 goto :deps_ok
echo    -^> Dang cai dat dependencies tu requirements.txt...
call python -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [LOI] Cai dat dependencies that bai!
    pause
    exit /b 1
)
echo    -^> Dang cai dat Chromium cho patchright...
call patchright install chromium
goto :check_env

:deps_ok
echo    -^> Cac thu vien da duoc cai dat day du.

:check_env
:: 4. Kiem tra file cau hinh .env.local
echo [4/5] Kiem tra file cau hinh moi truong...
if exist ".env.local" goto :env_exists
echo    -^> Chua co file .env.local. Dang tao file mau...
> .env.local echo # Cau hinh Dola Render Gateway
>> .env.local echo DOLA_HOST=0.0.0.0
>> .env.local echo DOLA_PORT=8000
>> .env.local echo.
>> .env.local echo # Proxy HTTP neu co
>> .env.local echo DOLA_PROXY=
>> .env.local echo.
>> .env.local echo # So luong tien trinh render dong thoi
>> .env.local echo DOLA_MAX_CONCURRENCY=3
>> .env.local echo.
>> .env.local echo # API Key xac thuc client
>> .env.local echo DOLA_API_KEYS=
>> .env.local echo.
>> .env.local echo # Mat khau trang Admin Web Dashboard
>> .env.local echo DOLA_ADMIN_KEY=
echo    -^> Da tao file .env.local!
goto :make_dirs

:env_exists
echo    -^> Tim thay file .env.local.

:make_dirs
if not exist "downloads" mkdir downloads
if not exist "accounts" mkdir accounts

:: 5. Khoi chay FastAPI server
echo.
echo [5/5] Dang khoi chay Dola Render Gateway Server...
echo ---------------------------------------------------------------------
echo  * Admin Dashboard:  http://127.0.0.1:8000 (hoac http://127.0.0.1:8000/web)
echo  * Swagger API Docs: http://127.0.0.1:8000/docs
echo ---------------------------------------------------------------------
echo.

"%PY_EXE%" -c "import uvicorn, config; uvicorn.run('server:app', host=config.HOST, port=config.PORT)"

echo.
echo [THONG BAO] Server da ket thuc hoac bi dung!
pause
