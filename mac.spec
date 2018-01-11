# -*- mode: python -*-

block_cipher = None

a = Analysis(['pyRouterJig.py'],
             pathex=['/Users/lowrie/Share/pyRouterJig/repo'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)

# Explicitly add libraries that pyinstaller misses
a.binaries += [('libQtCore.5.dylib', '/anaconda/lib/libQtCore.5.dylib', 'BINARY') ]
a.binaries += [('libQtGui.5.dylib', '/anaconda/lib/libQtGui.5.dylib', 'BINARY') ]
a.binaries += [('libpng16.16.dylib', '/anaconda/lib/libpng16.16.dylib', 'BINARY') ]

# Remove various unused files from distribution
a.datas = [x for x in a.datas if not x[0].endswith('.pyc')]
a.datas = [x for x in a.datas if not x[0].startswith('.git')]
a.datas = [x for x in a.datas if not x[0].startswith('woods')]
a.datas = [x for x in a.datas if not x[0].startswith('icons')]
# doc is different, because we need doc.py:
a.datas = [x for x in a.datas if os.path.dirname(x[1]).find('doc') < 0]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='pyRouterJig',
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='pyRouterJig')
app = BUNDLE(coll,
             name='pyRouterJig.app',
             icon='icons/pc_892.icns',
             bundle_identifier=None)
