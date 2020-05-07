# Constants do not change at all. They are consistent over runs of the
# application and the plattform and the environment.

from PyQt5 import QtGui

# -------------------------------------------------------------------
# configurations for normal measurements
# -------------------------------------------------------------------

# name or id of the lidar. used, e.g. for titel of telecover plots
LIDAR_NAME = 'RALPH'

#Number of channels that shall be exported under more than one label.
# Example: for some product configuration in SCC (e.g. backscatter retrievals with usecase 0)
# the toatal signal must be labelled as signal type 'elT'. For other products (e.g. depolarization)
# the same signal data must be labelled as 'elPR' or 'elPT'. Then, the two copies of corresponding signal can be
# written into the SCC raw data file. one of the copies refers to a channel of type 'elT', the other copy refers
# to a channel of type 'elPR' or 'elPT'

NUM_DOUBLE_CHANNELS = 1

# this is the total number of all channels that shall be analyzed or exported.
# This number is the sum of the number of physical channels (signals detected in your lidar)
# plus the number of duplications (NUM_DOUBLE_CHANNELS)
NUM_CHANNELS = 9

# create Channel names for internal use. This line shall not be modified!
CHANNEL_NAMES = {chan_id: "chan_%s" % chan_id for chan_id in range( NUM_CHANNELS )}

# Those channel IDs refer to the IDs of your channels in the SCC interface. If unknown, use 999.
# Alternatively, you can identify your signals within SCC also with the CHANNEL_ID_STR.
# In this case, the CHANNEL_ID are ignored by SCC.
# Note: In any case, you need to fill this array with the correct number of IDs.
# If they shall be ignored, use 999.
#
# If you want to analyze your data with the operational version of SCC AND with the test version,
# it is recommended to use CHANNEL_ID_STR instead of  CHANNEL_ID for the identification
# of your signals within the SCC raw data files.
CHANNEL_ID = [
    503,
    504,
    505,
    506,
    507,
    508,
    509,
    510,
    999]

# Those channel CHANNEL_ID_STR refer to the ID strings of your channels in the SCC interface.
# This parameter is mandatory.
CHANNEL_ID_STR = [
    'oh000',
    'oh001',
    'oh002',
    'oh003',
    'oh008',
    'oh011',
    'oh010',
    'oh009',
    'oh012']

# indicate here, which of the channels in your raw data file are far-range channels (1)
# or near-range channels (0).
# If there is no separation between near- range and far-range channels, use always 1.
# The order in this array refers to CHANNEL_ID_STR
RANGE_ID = [1,    1,    1,    1,    1,    1,     0,    0,  1]

# provide for each channel the first and last bin for the calculation of signal background bin
# The order in these arrays refers to CHANNEL_ID_STR
BG_FIRST = [0,    0,    0,    0,    0,    0,    0,    0,   0]
BG_LAST = [249,  249,  249,  249,  249,  249,  249,  249, 249]

# which altitude bin coresponds to 0m height above lidar?
FIRST_VALID_BIN = 251

# provide here, at which position in your raw data file the scc signals are located.
CHAN_NC_POS = [0, 1, 2, 3, 4, 5, 6, 7, 2]

# -------------------------------------------------------------------
# configurations for depolarization calibration measurements
# -------------------------------------------------------------------
# general assumption: first, several profiles are recorded with the first
# position of the polarization filter (e.g. +45°), next several profiles
# with the second position (-45°) are recorded.
# Note: this tool will not work if the the profiles with the two positions are recorded in alternation.

# number of channels for the depolarization calibration.
# in case of +/- 45° calibration of 1 wavelength, NUM_CAL_CHANNELS = 4
# in case of +/- 45° calibration of 2 wavelength, NUM_CAL_CHANNELS = 8
# in case of + 45° calibration of 1 wavelength, NUM_CAL_CHANNELS = 2
NUM_CAL_CHANNELS = 4

# channel IDs of calibration channels, see CHANNEL_ID
CAL_CHANNEL_SCC_ID =      [391, 392, 393, 394]

# channel string IDs of the calibration channels, see CHANNEL_ID_STR
# Example: '532s_p45', '532s_m45', '532total_p45', '532total_m45'
CAL_CHANNEL_SCC_ID_STR =  ['oh004', 'oh005', 'oh006', 'oh007']

# the relation between calibration channels and regular channels
# The order in this array refers to CAL_CHANNEL_SCC_ID_STR.
# the numbers refer to the order in CHANNEL_ID_STR
# Example: 532s = channel 3, 532total = channel 2
CAL_CHANNEL        =  [3,   3,   2,   2]

# Which calibration position (+ or - 45) is measured first, which is measured next?
# The order in this array refers to CAL_CHANNEL_SCC_ID_STR.
# Example: the output channels correspond to
# '532s_p45' = channel3, first (0) calibration position,
# '532s_m45' = channel3, second(1) calibration position,
# '532total_p45' = channel2, first (0) calibration position,
# '532total_m45' = channel2, second(1) calibration position,
CAL_IDX_RANGE      =  [0,   1,   0,   1] # 0 = first calibration

# which altitude range shall be used for the depolarization calibration?
CALIB_RANGE_MIN = 1000 #m
CALIB_RANGE_MAX = 3000 #m

# In order to automatically find calibration profiles: Which is the
# rounded value of the variable 'depol_cal_angle' in case of REGULAR (no calibration) measurement ?
CAL_ANGLE_MEASUREMENT = 0

# -------------------------------------------------------------------
# general station and lidar configurations
# -------------------------------------------------------------------

# number of time scales and scan angles in the raw data file
# Note: only files with NB_OF_TIME_SCALES = 1 and NB_OF_SCAN_ANGLES = 1
# can be handled correctly in the current version
NB_OF_TIME_SCALES = 1
NB_OF_SCAN_ANGLES = 1

# the output filenames are automatically generated from the measurementID,
# this SCC_RAW_FILENAME_BODY and the measurement times
SCC_RAW_FILENAME_BODY = 'oh_RALPH'

# SCC station ID
STATION_ID = 'hpb'

# -------------------------------------------------------------------
# plot configurations
# -------------------------------------------------------------------

# Which channel shall be used to prepare the quicklook?
# the channel name refers to CHANNEL_NAMES
QUICKLOOK_CHANNEL = 'chan_5'

# what is the (initial) maximum altitude of the plots?
MAX_PLOT_ALTITUDE = 15000 #m

# which colors shall be used to plot the signal profiles?
# there must be one entry for each of the CHANNEL_NAMES
PLOT_PROFILE_COLOR = {'chan_0': (0, 0, 255, 255),
                      'chan_1': (255, 0, 255, 255),
                      'chan_2': (0, 255, 0, 255),
                      'chan_3': (170, 170, 0, 255),
                      'chan_4': (255, 255, 0, 255),
                      'chan_5': (255, 0, 0, 255),
                      'chan_6': (0, 128, 0, 255),
                      'chan_7': (155, 170, 0, 255),
                      'chan_8': (0, 255, 0, 255),
                      }
PLOT_WINDOW_SIZE = (1280, 1024)
PLOT_BORDER_COLOR = (50, 0, 0)
PLOT_CONTOUR_DATA_UPPER_PERCENTILE = 99
PLOT_ISO_SMOOTH_FILTER_RANGE = (4, 4)
PLOT_ISO_COLOR = 'g'

REGION_INVALID_BRUSH = QtGui.QBrush(QtGui.QColor(255, 0, 0, 50))
REGION_NORMAL_BRUSH = QtGui.QBrush(QtGui.QColor(0, 0, 255, 50))
REGION_INITIAL_WIDTH_IN_BINS = 20
GRADIENT = {'ticks': [(0.0, (0, 0, 0, 255)), (1.0, (255, 255, 255, 255))],
            'mode': 'rgb',
            'edge_colors': [(255, 0, 0), (0, 0, 255)]}


# -------------------------------------------------------------------
# configurations for the calculation of the molecular profiles
# -------------------------------------------------------------------

# values of ground pressure and temperature that are provided in SCC raw data file for
# the calculation of standard atmosphere
# if a radio sonde is provided, these values are ignored.
GROUND_PRES = 900.  # hPa
GROUND_TEMP = 18.  # degC

# when reading Wyoming files, the following key words are used to find the beginning and end of the data section
# = end of header / begin of footer
SONDE_HEADER_STR = 'hPa'
SONDE_BOTTOM_STR = 'Station'

# if radio sonde data are from Ninjo system, no coordinates are provided within the csv files.
# In this case, the following coordinates are used.
SONDE_STATIONS = {'10954': {'name': 'Altenstadt', 'lat': 47.50, 'lon': 10.52, 'alt': 756},
                  '10962': {'name': 'Hohenpeissenberg', 'lat': 47.8, 'lon': 11.01, 'alt': 977},
                  '11120': {'name': 'Innsbruck', 'lat': 47.16, 'lon': 11.21, 'alt': 593},
                  '10868': {'name': 'Oberschleissheim', 'lat': 48.25, 'lon': 11.55, 'alt': 484},
                  '10739': {'name': 'Stuttgart', 'lat': 48.83, 'lon': 9.2, 'alt': 314},
                  }

# -------------------------------------------------------------------
# configurations for telecover measurements
# -------------------------------------------------------------------
#TC_NORMALIZATION_RANGE = (4000,5000) #[m]
TC_NORMALIZATION_RANGE = (2000,3000) #[m]
TC_MAX_PLOT_HEIGHT = [2000, 6000] #[m]
TC_MAX_OUTPUT_HEIGHT = 6000 #[m]
TC_RANGE_ID = ['nr', 'fr']

TC_SMOOTH_BINS = 4

TC_CHANNELS = ['chan_0', 'chan_1', 'chan_2', 'chan_3', 'chan_4', 'chan_5']
TC_CHANNEL_NAMES = {'chan_0': '355', 'chan_1':'387', 'chan_2':'532', 'chan_3':'532s', 'chan_4':'607', 'chan_5':'1064'}

TC_RATIOS = range(4)
TC_RATIO_NAMES = ['R355/387', 'R532/607', 'R532s/532', 'R1064/607']
TC_NOMINATORS = ['chan_0', 'chan_2', 'chan_3', 'chan_5']
TC_DENOMINATORS = ['chan_1', 'chan_4', 'chan_2', 'chan_4']

TC_COLORS = {'north':'blue', 'north2':'cyan', 'east':'r', 'south': 'orange', 'west':'lime', 'dark':'k'}
TC_STATION_NAME = 'OH (Hohenpeissenberg)'


# -------------------------------------------------------------------
# constants - do not change!
# -------------------------------------------------------------------

LIGHT_SPEED = 3E8

NC_FILL_INT = -2147483647
NC_FILL_FOAT = 9.9692099683868690e+36
