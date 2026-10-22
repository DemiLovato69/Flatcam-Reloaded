# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys


root = Path(SPECPATH).resolve()

a = Analysis(
    [str(root / 'flatcam')],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'share'), 'share'),
        (str(root / 'LICENSE'), '.'),
        (str(root / 'README.md'), '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='FlatCAM', console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='FlatCAM')

if sys.platform == 'darwin':
    app = BUNDLE(coll, name='FlatCAM.app', bundle_identifier='org.flatcam.flatcam')
