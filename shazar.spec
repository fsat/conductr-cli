# -*- mode: python -*-

import os
block_cipher = None


a = Analysis(['conductr_cli/shazar.py'],
             pathex=[os.path.abspath(os.getcwd())],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='shazar',
          debug=False,
          strip=False,
          upx=True,
          console=True )
