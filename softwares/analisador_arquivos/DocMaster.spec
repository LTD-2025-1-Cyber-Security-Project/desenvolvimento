# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\RESTAU~1\\AppData\\Local\\Temp\\docmaster_bootstrap.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('static', 'static'), ('utils', 'utils'), ('.env.example', '.'), ('app.py', '.'), ('config.py', '.'), ('fix_nltk_ssl.py', '.'), ('setup_db.py', '.'), ('DocMasterInitializerFixed.py', '.')],
    hiddenimports=['flask', 'werkzeug', 'jinja2', 'itsdangerous', 'click', 'importlib', 'sqlite3', 'flask_sqlalchemy', 'PIL', 'email', 'json', 'urllib', 'datetime', 'flask_cors', 'flask_limiter'],
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
    a.binaries,
    a.datas,
    [],
    name='DocMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['static\\images\\icon.ico'],
)
