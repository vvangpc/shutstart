# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for ShutStart (--onedir mode, packaged later by Inno Setup).
import os

block_cipher = None

ICON_PATH = os.path.join('shutstart', 'resources', 'icon.ico')
icon_arg = ICON_PATH if os.path.isfile(ICON_PATH) else None

VERSION_FILE = 'version.txt'
version_arg = VERSION_FILE if os.path.isfile(VERSION_FILE) else None


a = Analysis(
    ['run_shutstart.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Ship the resources folder so themes.icon_path() can find ICOs at runtime.
        ('shutstart/resources', 'shutstart/resources'),
    ],
    hiddenimports=[
        'shutstart',
        'shutstart.__main__',
        'shutstart.app',
        'shutstart.autostart',
        'shutstart.autostart_task',
        'shutstart.config',
        'shutstart.killer',
        'shutstart.launcher',
        'shutstart.startup_inventory',
        'shutstart.ui',
        'shutstart.ui.themes',
        'shutstart.ui.main_dialog',
        'shutstart.ui.settings_dialog',
        'shutstart.ui.startup_manager_dialog',
        'shutstart.ui.item_editor',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pydoc',
        'pdb',
        'doctest',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtSql',
        'PyQt5.Qt3DCore',
        'PyQt5.Qt3DRender',
        'PyQt5.Qt3DInput',
        'PyQt5.Qt3DLogic',
        'PyQt5.Qt3DAnimation',
        'PyQt5.QtCharts',
        'PyQt5.QtBluetooth',
        'PyQt5.QtNetworkAuth',
        'PyQt5.QtDataVisualization',
        'PyQt5.QtPositioning',
        'PyQt5.QtLocation',
        'PyQt5.QtSensors',
        'PyQt5.QtSerialPort',
        'PyQt5.QtTest',
        'PyQt5.QtXmlPatterns',
        'PyQt5.QtNfc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ShutStart',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
    version=version_arg,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ShutStart',
)
