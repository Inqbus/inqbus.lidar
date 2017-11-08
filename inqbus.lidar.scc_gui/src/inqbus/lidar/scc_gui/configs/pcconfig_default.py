import os
from logging import INFO

BASE_PATH = 'C:\\inqbus.lidar\\test_data'

DATA_PATH = os.path.join(BASE_PATH, 'data')
TEMP_PATH = 'c:\\temp'

OUT_PATH = os.path.join(BASE_PATH, 'scc_raw')
SONDE_PATH = os.path.join(BASE_PATH, 'sondes')
OVL_PATH = os.path.join(BASE_PATH, 'overlaps')

IN_PATH = os.path.join(BASE_PATH, 'raw_nc')
LIDAR_LOG_PATH = os.path.join(BASE_PATH, 'logs')

SYS_LOG_PATH = os.path.join(BASE_PATH, 'gui_log')

SYS_LOG_FILE = os.path.join(SYS_LOG_PATH, 'scc-gui.log')
SYS_LOG_LEVEL = INFO
