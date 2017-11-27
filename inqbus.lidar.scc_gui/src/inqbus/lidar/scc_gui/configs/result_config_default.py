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
        'e355bsc':{'color':'cyan', 'exists':False}, \
        'e532bsc':{'color':'lime', 'exists':False}, \
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