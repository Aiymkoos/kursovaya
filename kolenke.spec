# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: pyinstaller kolenke.spec   ->   dist/Kolenke(.exe)
# Ресурстар (шрифт, JSON) exe ішіне салынады; sys._MEIPASS арқылы оқылады.
from PyInstaller.utils.hooks import collect_data_files

datas = [
    ("assets/fonts", "assets/fonts"),
    ("kolenke/data", "kolenke/data"),
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib", "pytest", "tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Kolenke",
    debug=False,
    strip=False,
    upx=False,
    console=False,          # терезе ғана (консольсіз)
    runtime_tmpdir=None,
)
