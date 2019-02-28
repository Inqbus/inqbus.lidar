from datetime import datetime

RES_VAR_NAMES = {'b355': {'Backscatter': 'b355', 'VolumeDepolarization': 'vldr355', 'ParticleDepolarization': 'pldr355'},
             'b532': {'Backscatter':'b532',
                      'VolumeDepol': 'vldr532', 'VolumeDepolarization':'vldr532',
                      'ParticleDepol':'pldr532', 'ParticleDepolarization': 'pldr532'},
             'b1064': {'Backscatter': 'b1064'},
             'e355': {'Backscatter': 'e355bsc', 'Extinction': 'e355'},
             'e532': {'Backscatter': 'e532bsc', 'Extinction': 'e532'},
             }

RES_VAR_NAMES_CF = {
    'b355': {'backscatter': 'b355', 'volumedepolarization': 'vldr355', 'particledepolarization': 'pldr355'},
    'b532': {'backscatter': 'b532', 'volumedepolarization': 'vldr532', 'particledepolarization': 'pldr532'},
    'b1064': {'backscatter': 'b1064'},
    'e355': {'backscatter': 'e355bsc', 'extinction': 'e355'},
    'e532': {'backscatter': 'e532bsc', 'extinction': 'e532'},
    }

GLOBAL_VARS_CF = {'latitude':{},
                  'longitude':{},
                  'station_altitude':{},
                  'cirrus_contamination': {},
                  'cirrus_contamination_source': {},
                  'atmospheric_molecular_calculation_source': {},
                  'atmospheric_molecular_calculation_source_file': {},
                  'zenith_angle': {},
                  'user_defined_category':{},
                  'altitude':{},
                  'cloud_mask':{},
                  'time':{},
                  'time_bounds':{},
                  'error_retrieval_method':{},
                  'shots':{},
                  'input_file':{},
                  }

VARIABLE_ATTRIBUTES = { 'altitude': {'long_name': "height above sea level",
                                     'units': "m",
                                     'axis': "Z",
                                     'positive': "up",
                                     'standard_name': "altitude"},
                        'vertical_resolution': {'long_name': "effective vertical resolution according to Pappalardo et al., appl. opt. 2004",
                                                'units': "m"},
                        'cloud_mask': {'long_name': "1: no cloud; 2: cirrus; 4: low cloud",
#                                        '_FillValue': -127,
                                       },

                        'backscatter': {'long_name': "aerosol backscatter coefficient",
                                        'units': "1/(m*sr)",
                                        'ancillary_variables': "error_backscatter vertical_resolution",
                                        'coordinates': "longitude latitude",
#                                        '_FillValue': 9.969209968386869E36,
                                         },
                        'error_backscatter': {'long_name': "absolute statistical uncertainty of backscatter",
                                             'units': "1/(m*sr)",
                                             'coordinates': "longitude latitude",
#                                             '_FillValue': 9.969209968386869E36,
                                              },

                        'extinction': {'long_name': "aerosol extinction coefficient",
                                       'units': "1/m",
                                       'ancillary_variables': "error_extinction vertical_resolution",
                                       'coordinates': "longitude latitude",
#                                       '_FillValue': 9.969209968386869E36,
                                       },
                        'error_extinction': {'long_name': "absolute statistical uncertainty of extinction",
                                             'units': "1/m",
                                             'coordinates': "longitude latitude",
#                                             '_FillValue': 9.969209968386869E36,
                                             },

                        'volumedepolarization' :{'long_name': "volume linear depolarization ratio",
                                                 'ancillary_variables': "error_volumedepolarization vertical_resolution",
                                                 'coordinates': "longitude latitude",
#                                                 '_FillValue': 9.969209968386869E36,
                                                 },
                        'error_volumedepolarization': {'long_name': "absolute statistical uncertainty of volumedepolarization",
                                                       'coordinates': "longitude latitude",
#                                                       '_FillValue': 9.969209968386869E36,
                                                       },

                        'particledepolarization': {'long_name': "particle linear depolarization ratio",
                                                   'ancillary_variables': "error_particledepolarization vertical_resolution",
                                                   'coordinates': "longitude latitude",
#                                                   '_FillValue': 9.969209968386869E36,
                                                   },
                        'error_particledepolarization': {'long_name': "absolute statistical uncertainty of particledepolarization",
                                                         'coordinates': "longitude latitude",
#                                                         '_FillValue': 9.969209968386869E36,
                                                         },
                        }

RES_VAR_NAME_ALIAS = {'VolumeDepol': 'VolumeDepolarization',
                      'ParticleDepol': 'ParticleDepolarization',
                  'volume_depolarization': 'VolumeDepol',
                  'particle_depolarization': 'ParticleDepol',
                  'volumedepolarization': 'VolumeDepol',
                  'particledepolarization': 'ParticleDepol',
                  'backscatter': 'Backscatter',
                  'extinction': 'Extinction',}

# scale_factor us used for plotting: data_in_plot = data_in_ncfile * scale_factor
RES_DATA_SETTINGS = {'b355':{'color':'b', 'exists':False, 'scale_factor': 1.0E6},
        'b532':{'color':'g', 'exists':False, 'scale_factor': 1.0E6},
        'b1064':{'color':'r', 'exists':False, 'scale_factor': 1.0E6},
        'vldr532':{'color':'g', 'exists':False, 'scale_factor': 100.0},
        'vldr355':{'color':'b', 'exists':False, 'scale_factor': 100.0},
        'pldr532':{'color':'k', 'exists':False, 'scale_factor': 100.0},
        'pldr355':{'color':0.75, 'exists':False, 'scale_factor': 100.0},
        'e355':{'color':'b', 'exists':False, 'scale_factor': 1.0E6},
        'e532':{'color':'g', 'exists':False, 'scale_factor': 1.0E6},
        'lr355':{'color':'b', 'exists':False, 'scale_factor': 1.0},
        'lr532':{'color':'g', 'exists':False, 'scale_factor': 1.0},
        'e355bsc':{'color':'#00FFFF', 'exists':False, 'scale_factor': 1.0E6},
        'e532bsc':{'color':'#32cd32', 'exists':False, 'scale_factor': 1.0E6},
        'aeb_uv_vis':{'color':'b', 'exists':False, 'scale_factor': 1.0},
        'aeb_vis_ir':{'color':'r', 'exists':False, 'scale_factor': 1.0},
        'ae_ext':{'color':'g', 'exists':False, 'scale_factor': 1.0},
        'max_alt': 0, 
        'start_time': datetime(2030,1,1), 'end_time': datetime(2000,1,1)}

LIDAR_RATIO_CALCULATIONS = {'lr355': {'bsc': 'e355bsc', 'ext': 'e355'},
                            'lr532': {'bsc': 'e532bsc', 'ext': 'e532'},
                            }
ANGSTROEM_CALCULATIONS = {'aeb_uv_vis': {'profile_1': 'b355', 'profile_2': 'b532', 'wl_1': 355., 'wl_2': 532.},
                          'aeb_vis_ir': {'profile_1': 'b532', 'profile_2': 'b1064', 'wl_1': 532., 'wl_2': 1064.},
                          'ae_ext': {'profile_1': 'e355', 'profile_2': 'e532', 'wl_1': 355., 'wl_2': 532.},
                          }

# if plots should be scaled automatically (AUTO_SCALE = True), axes are scaled to the values with RES_AXES_LIMITS as initial values
# if plots should not be scaled automatically (AUTO_SCALE = False), axes are scaled according to RES_AXES_LIMITS
AUTO_SCALE = True
INI_AUTO_SCALE = False
RES_AXES_LIMITS = {'Backscatter': {'min':-.5, 'max':5, 'min_percentile':0, 'max_percentile':100},
               'Extinction': {'min':-20, 'max':150, 'min_percentile':0, 'max_percentile':100},
               'lidar_ratio': {'min':-20, 'max':120, 'min_percentile':10, 'max_percentile':90},
               'angstroem': {'min':-2., 'max':5., 'min_percentile':5, 'max_percentile':95},
               'Depol': {'min':-1, 'max':20, 'min_percentile':5, 'max_percentile':95},
               }

PROFILES_IN_PLOT = {'Backscatter': ['b355', 'b532', 'b1064', 'e355bsc', 'e532bsc'],
                    'Extinction': ['e355', 'e532'],
                    'lidar_ratio': ['lr355', 'lr532'],
                    'angstroem': ['aeb_uv_vis', 'aeb_vis_ir', 'ae_ext'],
                    'Depol': ['vldr532', 'pldr532', 'vldr355', 'pldr355'],
                    }

RES_DTYPES_FOR_MEAN_PROFILE = ['b355','b532','b1064','e355','e532','e355bsc', 'e532bsc','vldr355', 'vldr532', 'pldr355', 'pldr532']

# add here to clear them of masked values, because pyqtplot behaves different with masked values. Masked values are replaced by NaN.
#RES_CLEAR_DTYPES_DATA = ['lr355', 'lr532', 'aeb_uv_vis', 'aeb_vis_ir', 'ae_ext']
#RES_CLEAR_DTYPES_BACKSCATTER_MEAN = ['b355', 'b532', 'b1064', 'e355', 'e532']
#RES_CLEAR_DTYPES_EXTINCTION_MEAN = ['e355', 'e532']
#RES_CLEAR_DTYPES_MEAN = ['vldr532', 'pldr532', 'vldr355', 'pldr355']

RES_MIN_ALT = 0

RES_LEGEND_LABEL_STYLE = {'color': '#000', 'size': '10pt', 'bold': False, 'italic': False}

RES_SHOW_LEGEND = True

RES_PLOT_NAMES = ['bsc_plot', 'ext_plot', 'lr_plot', 'angstroem_plot', 'depol_plot']

# menu config for setting plots Invalid/Valid
# orders plot -> menu entry -> related graphs
# possible plots are: 'bsc_plot', 'ext_plot', 'lr_plot', 'angstroem_plot', 'depol_plot'
# related graphs are given as path-tuples e.g. ('b355', 'Backscatter', 'mean') or ('lr255',)

RES_VALIDATION_MENU = {
    'bsc_plot' : {
        '355': ['b355','aeb_uv_vis','pldr355'],
        '532': ['b532', 'aeb_uv_vis', 'pldr532', 'aeb_vis_ir'],
        '1064': ['b1064', 'aeb_vis_ir'],
        'e355bsc': ['e355bsc', 'lr355'],
        'e532bsc': ['e532bsc', 'lr532'],
    },
    'ext_plot' : {
        '355': ['e355', 'lr355', 'e355bsc', 'ae_ext'],
        '532': ['e532', 'lr532', 'e532bsc', 'ae_ext'],
    },
    'lr_plot': {
        '355': ['e355bsc', 'lr355'],
        '532': ['e532bsc', 'lr532'],
    },
    'depol_plot': {
        'VLDR 355': ['vldr355', 'pldr355'],
        'PLDR 355': ['pldr355'],
        'VLDR 532': ['vldr532', 'pldr532'],
        'PLDR 532': ['pldr532'],
    },
    'angstroem_plot': {
        'bsc 355': [],
        'bsc 532': [],
        'bsc 1064': [],
        'ext 355': [],
        'ext 532': [],
    },
}

# menu config for marking clouds
RES_DISPLAY_CLOUD_MENU = {
    'bsc_plot': ['vldr355', 'pldr355', 'vldr532', 'pldr532',
                 'b355', 'b532', 'b1064' ],
    'ext_plot': [ 'e355', 'e532', 'e355bsc', 'e532bsc', 'lr355', 'lr532' ]
}

RES_INITIAL_REGION_WIDTH = 1000

# hsv color to make it transparent
RES_CLOUD_LINE_COLOR = (0, 0, 0.5, 0.5)