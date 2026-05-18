# PyInstaller spec file — run with: pyinstaller build.spec --clean --noconfirm
# Output: dist/SmartTextToSpeech/SmartTextToSpeech.exe

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static',    'static'),
    ],
    hiddenimports=[
        # Flask & Werkzeug internals
        'flask', 'jinja2', 'jinja2.ext', 'werkzeug', 'werkzeug.serving',
        'werkzeug.debug', 'click',
        # edge-tts
        'edge_tts', 'edge_tts.communicate', 'edge_tts.exceptions',
        'edge_tts.list_voices', 'edge_tts.models',
        # aiohttp and its native extensions
        'aiohttp', 'aiohttp.web', 'aiosignal', 'frozenlist',
        'multidict', 'yarl', 'aiohappyeyeballs', 'certifi',
        # Async
        'asyncio', 'concurrent.futures',
        # Tray icon
        'pystray', 'pystray._win32',
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
        # Stdlib fallback
        'tkinter', 'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'IPython'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SmartTextToSpeech',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,      # No black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SmartTextToSpeech',
)
