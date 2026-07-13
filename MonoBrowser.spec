# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/monobrowser/main.py'],
    pathex=['src/monobrowser'],
    binaries=[],
    datas=[('src/assets/icon.icns', '.'), ('src/assets/icon.png', '.'), ('pyproject.toml', '.'), ('src/monobrowser/about-pages', 'about-pages')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MonoBrowser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['src/assets/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MonoBrowser',
)
app = BUNDLE(
    coll,
    name='MonoBrowser.app',
    icon='src/assets/icon.icns',
    bundle_identifier=None,
)
