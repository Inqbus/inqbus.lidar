# Config Items are persistent over many runs of the Application, but may change according to the plattform
# and the environment the application is run in
# load default configs or configs given by parameter

from importlib._bootstrap_external import SourceFileLoader
from optparse import OptionParser

import sys

parser = OptionParser()
parser.add_option("-p", "--pcconfig", dest='pcconfig')
parser.add_option("-l", "--lidarconfig", dest='lidarconfig')
parser.add_option("-r", "--resultconfig", dest='resultconfig')
(option, args) = parser.parse_args()

if option.pcconfig is None:
    from inqbus.lidar.scc_gui.configs.pcconfig_default import *
else:
    # same as: from LOCAL_CONFIG import *
    try:
        local_config = SourceFileLoader(
            "inqbus.lidar.scc_gui.configs.main_config",
            option.pcconfig).load_module()
    except IsADirectoryError:
        print("Wrong config. Please provide a python-file.")
        sys.exit()
    except ValueError:
        print("Wrong config. Please provide a python-file.")
        sys.exit()

if option.lidarconfig is None:
    from inqbus.lidar.scc_gui.configs.lidarconfig_default import *
else:
    # same as: from LOCAL_CONFIG import *
    try:
        local_config = SourceFileLoader(
            "inqbus.lidar.scc_gui.configs.main_config",
            option.lidarconfig).load_module()
    except IsADirectoryError:
        print("Wrong config. Please provide a python-file.")
        sys.exit()
    except ValueError:
        print("Wrong config. Please provide a python-file.")
        sys.exit()

if option.resultconfig is None:
    from inqbus.lidar.scc_gui.configs.result_config_default import *
else:
    try:
        local_config = SourceFileLoader(
            "inqbus.lidar.scc_gui.configs.main_config",
            option.resultconfig).load_module()
    except IsADirectoryError:
        print("Wrong config. Please provide a python-file.")
        sys.exit()
    except ValueError:
        print("Wrong config. Please provide a python-file.")
        sys.exit()