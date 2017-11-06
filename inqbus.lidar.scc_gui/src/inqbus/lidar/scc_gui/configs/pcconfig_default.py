import os

# this path can be your general base path. It is not mandatory.
# You may also provide the following paths directly,
# not in relation to this base path
BASE_PATH = '/'

# This is the directory, where your raw lidar data are located
DATA_PATH = os.path.join(BASE_PATH, 'data')

# If your raw lidar data are zip files, the are temporarily unpacked into this directory.
TEMP_PATH = os.path.join(BASE_PATH, 'temp')

# the created scc raw data files and the corresponding ancillary files are written into this directory
OUT_PATH = os.path.join(DATA_PATH, 'scc_raw')

# This is the directory, where radio sonde files are located.
SONDE_PATH = os.path.join(DATA_PATH, 'sondes')

# this is the directory, where overlap files are located
# not yet implemented
#OVL_PATH = os.path.join(DATA_PATH, 'overlaps')

# log files are written into this directory
LOG_PATH = os.path.join(BASE_PATH, 'logs')
