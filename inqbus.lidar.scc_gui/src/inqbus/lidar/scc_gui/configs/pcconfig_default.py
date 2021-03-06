import os
from logging import INFO

# this path can be your general base path. It is not mandatory.
# You may also provide the following paths directly,
# not in relation to this base path
BASE_PATH = 'C:\\inqbus.lidar\\test_data'

# This is the directory, where your raw lidar data are located
DATA_PATH = os.path.join(BASE_PATH, 'data')

# If your raw lidar data are zip files, the are temporarily unpacked into this directory.
TEMP_PATH = 'c:\\temp'

# the created scc raw data files and the corresponding ancillary files are written into this directory
OUT_PATH = os.path.join(BASE_PATH, 'scc_raw')
# This is the directory, where radio sonde files are located.
SONDE_PATH = os.path.join(BASE_PATH, 'sondes')
# this is the directory, where overlap files are located
# not yet implemented
OVL_PATH = os.path.join(BASE_PATH, 'overlaps')

# this is the directory where lidar-log-files are located
LIDAR_LOG_PATH = os.path.join(BASE_PATH, 'logs')

# This is the directory, where the original optical data (b and e files) are located
RESULT_DATA_PATH = os.path.join(BASE_PATH, 'res_data')

# the final, quality controlled optical data (b and e files) are written into this directory
RESULT_EXPORT_PATH = os.path.join(BASE_PATH, 'res_exported')

# this is the path where plots and ASCII files of telecover analysis are written to
TELECOVER_PATH = 'G:\\dokumentation\\RALPH_QAtests'

# log files are written into this directory
SYS_LOG_PATH = os.path.join(BASE_PATH, 'gui_log')
# log files are written into this file
SYS_LOG_FILE = os.path.join(SYS_LOG_PATH, 'scc-gui.log')
# log level
SYS_LOG_LEVEL = INFO
