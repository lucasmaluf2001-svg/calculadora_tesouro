@echo off
setlocal
cd /d "%~dp0"

python -m pip install -r requirements.txt
if errorlevel 1 goto :error

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --name CarteiraTesouro ^
  --add-data "app\static\index.html;app\static" ^
  --add-data "data\snapshot_base.json;data" ^
  --add-data "data\snapshot_seed.json;data" ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops.auto ^
  --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.websockets.auto ^
  --hidden-import uvicorn.lifespan.on ^
  launcher.py

if errorlevel 1 goto :error

echo.
echo Executavel criado em:
echo %CD%\dist\CarteiraTesouro.exe
echo.
pause
exit /b 0

:error
echo.
echo Ocorreu um erro durante a compilacao.
pause
exit /b 1
