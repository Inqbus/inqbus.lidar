# -*- mode: python -*-
block_cipher = None


a = Analysis(['app.py'],
             pathex=['c:\\path\\to\\inqbus.lidar.scc_gui\\src\\inqbus\\lidar\\scc_gui'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
a.datas += [('UI/app_design.ui', '.\\UI\\app_design.ui', 'DATA'),
            ('UI/axisCtrlTemplate.ui', '.\\UI\\axisCtrlTemplate.ui', 'DATA'),
            ('UI/plotConfigTemplate.ui', '.\\UI\\plotConfigTemplate.ui', 'DATA'),
            ('UI/design.ui', '.\\UI\\design.ui', 'DATA'),
            ('UI/region_dialog.ui', '.\\UI\\region_dialog.ui', 'DATA'),
            ('UI/save_as_scc_dialog.ui', '.\\UI\\save_as_scc_dialog.ui', 'DATA'),
            ('UI/save_as_sccDPcal_dialog.ui', '.\\UI\\save_as_sccDPcal_dialog.ui', 'DATA'),
            ]
#a.binaries += [('mkl_avx.dll', 'C:\Anaconda2\\Library\\bin\\mkl_avx.dll', 'BINARY')]
a.binaries += [('mkl_mc3.dll', 'C:\Anaconda2\\Library\\bin\\mkl_mc3.dll', 'BINARY')]
#a.binaries += [('mkl_mc3.dll', 'C:\\Benutzer\\gmueller\\AppData\\local\\Continuum\\Anaconda2\\Library\\mkl_mc3.dll', 'BINARY')]

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='SCC_interface',
          debug=False,
          strip=False,
          upx=True,
          console=True )
