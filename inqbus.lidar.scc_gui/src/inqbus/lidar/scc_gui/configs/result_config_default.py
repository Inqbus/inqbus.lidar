from datetime import datetime

RES_VAR_NAMES = {'b355': ['Backscatter', 'VolumeDepolarization', 'ParticleDepolarization'], \
             'b532': ['Backscatter', 'VolumeDepol', 'ParticleDepol', 'VolumeDepolarization', 'ParticleDepolarization'], \
             'b1064': ['Backscatter'], \
             'e355': ['Backscatter', 'Extinction'], \
             'e532': ['Backscatter', 'Extinction'], \
             }

RES_VAR_NAME_ALIAS = {'VolumeDepolarization': 'VolumeDepol', 'ParticleDepolarization': 'ParticleDepol'}

RES_DATA_SETTINGS = {'b355':{'color':'b', 'exists':False}, \
        'b532':{'color':'g', 'exists':False}, \
        'b1064':{'color':'r', 'exists':False}, \
        'vldr532':{'color':'g', 'exists':False}, \
        'vldr355':{'color':'b', 'exists':False}, \
        'pldr532':{'color':'k', 'exists':False}, \
        'pldr355':{'color':0.75, 'exists':False}, \
        'e355':{'color':'b', 'exists':False}, \
        'e532':{'color':'g', 'exists':False}, \
        'lr355':{'color':'b', 'exists':False}, \
        'lr532':{'color':'g', 'exists':False}, \
        'e355bsc':{'color':'#00FFFF', 'exists':False}, \
        'e532bsc':{'color':'#32cd32', 'exists':False}, \
        'aeb_uv_vis':{'color':'b', 'exists':False}, \
        'aeb_vis_ir':{'color':'r', 'exists':False}, \
        'ae_ext':{'color':'g', 'exists':False}, \
        'max_alt': 0, \
        'start_time': datetime(2030,1,1), 'end_time': datetime(2000,1,1)}

RES_AXES_LIMITS = {'Backscatter': (-.01, .1), \
               'Extinction': (-5, 50), \
               'lidar_ratio': (-20, 120), \
               'angstroem': (-1., 3.), \
               'Depol': (-.001, .01), \
               }

RES_DTYPES_FOR_MEAN_PROFILE = ['b355','b532','b1064','e355','e532']
RES_DTYPES_FOR_LR = ['e355', 'e532']

# add here to clear them of masked values, because pyqtplot behaves different with masked values. Masked values are replaced by NaN.
RES_CLEAR_DTYPES_DATA = ['lr355', 'lr532', 'aeb_uv_vis', 'aeb_vis_ir', 'ae_ext']
RES_CLEAR_DTYPES_BACKSCATTER_MEAN = ['b355', 'b532', 'b1064', 'e355', 'e532']
RES_CLEAR_DTYPES_EXTINCTION_MEAN = ['e355', 'e532']
RES_CLEAR_DTYPES_MEAN = ['vldr532', 'pldr532', 'vldr355', 'pldr355']

RES_MIN_ALT = 0

LEGEND_LABEL_STYLE = {'color': '#000', 'size': '10pt', 'bold': False, 'italic': False}

RES_SHOW_LEGEND = True

# menu config for setting plots Invalid/Valid
# orders plot -> menu entry -> related graphs
# possible plots are: 'bsc_plot', 'ext_plot', 'lidar_plot', 'angstroem_plot', 'depol_plot'
# related graphs are given as path-tuples e.g. ('b355', 'Backscatter', 'mean') or ('lr255',)

VALIDATION_MENU = {
    'bsc_plot' : {
        '355': [('b355', 'Backscatter', 'mean'), ('aeb_uv_vis',), ('pldr355', 'mean'),],
        '532': [('b532', 'Backscatter', 'mean'), ('aeb_uv_vis',), ('pldr532', 'mean'), ('aeb_vis_ir',)],
        '1064': [('b1064', 'Backscatter', 'mean'), ('aeb_vis_ir',)],
        'e355bsc': [('e355', 'Backscatter', 'mean'), ('lr355',)],
        'e532bsc': [('e532', 'Backscatter', 'mean'), ('lr532',)],
    },
    'ext_plot' : {
        '355': [('e355', 'Extinction', 'mean'), ('lr355',), ('ae_ext',)],
        '532': [('e532', 'Extinction', 'mean'), ('lr532',), ('ae_ext',)],

    },
    'lidar_plot': {
        '355': [('e355', 'Backscatter', 'mean'), ('lr355',)],
        '532': [('e532', 'Backscatter', 'mean'), ('lr532',)],

    },
    'angstroem_plot': {
        'VLDR 355': [('vldr355', 'mean')],
        'PLDR 355': [('pldr355', 'mean')],
        'VLDR 532': [('vldr532', 'mean')],
        'PLDR 532': [('pldr532', 'mean')],

    },
    'depol_plot': {
        'bsc 355': [],
        'bsc 532': [],
        'bsc 1064': [],
        'ext 355': [],
        'ext 532': [],
    },
}

# menu config for marking clouds
DISPLAY_MENU = {
    'bsc_plot': [
        ('vldr355', 'mean'),
        ('pldr355', 'mean'),
        ('vldr532', 'mean'),
        ('pldr532', 'mean'),
        ('b355', 'Backscatter', 'mean'),
        ('b532', 'Backscatter', 'mean'),
        ('b1064', 'Backscatter', 'mean'),
    ],
    'ext_plot': [
        ('e355', 'Backscatter', 'mean'),
        ('e532', 'Backscatter', 'mean'),
        ('e355', 'Extinction', 'mean'),
        ('e532', 'Extinction', 'mean'),
    ]
}