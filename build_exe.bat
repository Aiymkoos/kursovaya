@echo off
REM Windows үшін .exe жинау (Python 3.10+ орнатылған болу керек)
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean kolenke.spec
echo.
echo Дайын: dist\Kolenke.exe
pause
