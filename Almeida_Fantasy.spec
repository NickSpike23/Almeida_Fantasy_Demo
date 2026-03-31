# -*- mode: python ; coding: utf-8 -*-

import os

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath('menu.py'))

# Definir los datos a incluir
datas = [
    ('img', 'img'),
    ('music', 'music'),
    ('video', 'video')
]

# Buscar todos los archivos Python del proyecto para incluir como módulos ocultos
hiddenimports = [
    'rafa_intro',
    'javier_intro',
    'combate',
    'mapa',
    'character_intro'
]

a = Analysis(
    ['menu.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Almeida_Fantasy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)