# Constants do not change at all. They are consistent over runs of the
# application and the plattform and the environment.


from PyQt5 import QtGui

# Build chan-0 to chan_7 channames
CHANNEL_NAMES = {chan_id: "chan_%s" % chan_id for chan_id in range(9)}

CHANNEL_ID = [503,  504,  505,  506,  507,  508,  509,  510, 999] #Ralph operational scc
#CHANNEL_ID =  [387,  388,  389,  390,  395,  398,  397,  396, 445] #Ralph development scc

CHANNEL_ID_STR = ['oh000',  'oh001',  'oh002',  'oh003',  'oh008',  'oh011',  'oh010',  'oh009', 'oh012'] #Ralph


RANGE_ID = [1,    1,    1,    1,    1,    1,     0,    0,  1]

BG_FIRST    = [0,    0,    0,    0,    0,    0,    0,    0,   0]
BG_LAST     = [249,  249,  249,  249,  249,  249,  249,  249, 249]

#OVL_ID      = ['',   '',  '_532', '_532s', '_607', '_1064', '', '', '']
#CHAN_NC_POS = [0,1,2,3,4,5,6,7,2]

OVL_ID = [
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    '']
CHAN_NC_POS = [0, 1, 2, 3, 4, 5, 6, 7, 2]

#DOUBLE_CHAN = 2
NUM_DOUBLE_CHANNELS = 1

NUM_CAL_CHANNELS = 4
CAL_CHANNEL_SCC_ID =      [391, 392, 393, 394] #scc test version: 532s+45, 532s-45, 532+45, 532-45
CAL_CHANNEL_SCC_ID_STR =  ['oh004', 'oh005', 'oh006', 'oh007'] #scc test version: 532s+45, 532s-45, 532+45, 532-45
CAL_CHANNEL        =  [3,   3,   2,   2] #532s = channel 3, 532 = channel 2
CAL_IDX_RANGE      =  [0,   1,   0,   1] # 0 = first calibration
# position, 1 = second calibration position

CALIB_RANGE_MIN = 1000
CALIB_RANGE_MAX = 3000

# rounded value of the variable 'depol_cal_angle' in case of normal measurement
CAL_ANGLE_MEASUREMENT = 0

LIGHT_SPEED = 3E8

NB_OF_TIME_SCALES = 1
NB_OF_SCAN_ANGLES = 1


GROUND_PRES = 1000.  # hPa
GROUND_TEMP = 15.  # degC

FIRST_VALID_BIN = 251

SCC_RAW_FILENAME_BODY = 'oh_RALPH'

SONDE_HEADER_STR = 'hPa'
SONDE_BOTTOM_STR = 'Station'

NC_FILL_INT = -2147483647
NC_FILL_FOAT = 9.9692099683868690e+36
PLOT_WINDOW_SIZE = (1280, 1024)
PLOT_BORDER_COLOR = (50, 0, 0)
PLOT_CONTOUR_DATA_UPPER_PERCENTILE = 99
PLOT_ISO_SMOOTH_FILTER_RANGE = (4, 4)
PLOT_ISO_COLOR = 'g'
PLOT_PROFILE_COLOR = {'chan_0': (0, 0, 255, 255),
                      'chan_1': (255, 0, 255, 255),
                      'chan_2': (0, 255, 0, 255),
                      'chan_3': (170, 170, 0, 255),
                      'chan_4': (255, 255, 0, 255),
                      'chan_5': (255, 0, 0, 255),
                      'chan_6': (0, 128, 0, 255),
                      'chan_7': (155, 170, 0, 255),
                      'chan_8': (0, 255, 0, 255),
#                      'chan_9': (0, 255, 0, 255),
#                      'chan_10': (0, 255, 0, 255),
#                      'chan_11': (0, 255, 0, 255),
#                      'chan_12': (0, 0, 255, 255),
#                      'chan_13': (255, 255, 0, 255),
#                      'chan_14': (0, 255, 0, 255),
#                      'chan_15': (0, 255, 0, 255),
#                      'chan_16': (0, 0, 255, 255),
#                      'chan_17': (255, 255, 0, 255),

                      }
QUICKLOOK_CHANNEL = 'chan_5'
MAX_PLOT_ALTITUDE = 15000
REGION_INVALID_BRUSH = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))
REGION_NORMAL_BRUSH = QtGui.QBrush(QtGui.QColor(0, 0, 255, 50))
REGION_INITIAL_WIDTH_IN_BINS = 20
GRADIENT = {'ticks': [(0.0, (0, 0, 0, 255)), (1.0, (255, 255, 255, 255))],
            'mode': 'rgb',
            'edge_colors': [(255, 0, 0), (0, 0, 255)]}

STATION_ID = 'oh'

SONDE_STATIONS = {'10954': {'name': 'Altenstadt', 'lat': 47.50, 'lon': 10.52, 'alt': 756},
                  '10962': {'name': 'Hohenpeissenberg', 'lat': 47.8, 'lon': 11.01, 'alt': 977},
                  '11120': {'name': 'Innsbruck', 'lat': 47.16, 'lon': 11.21, 'alt': 593},
                  '10868': {'name': 'Oberschleissheim', 'lat': 48.25, 'lon': 11.55, 'alt': 492},
                  '12374': {'name': 'Legionowo', 'lat': 52.40, 'lon': 20.96, 'alt': 96}}
