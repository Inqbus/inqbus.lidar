import datetime as dt
import os
import zipfile

import numpy as np
import pyqtgraph as pg
from scipy.io import netcdf
from datetime import datetime

from inqbus.lidar.components.error import PathDoesNotExist
from pyqtgraph.Qt import QtCore, QtGui

from inqbus.lidar.components.regions import Regions
from inqbus.lidar.scc_gui import util
from inqbus.lidar.scc_gui.log import logger
from inqbus.lidar.scc_gui.axis import DateAxis, HeightAxis
from inqbus.lidar.scc_gui.configs import main_config as mc
from inqbus.lidar.scc_gui.histo import Histo
from inqbus.lidar.scc_gui.image import Image
from inqbus.lidar.scc_gui.region import MenuLinearRegionItem
from inqbus.lidar.scc_gui.viewbox import FixedViewBox

class ResultData(object):

    @classmethod
    def from_directory(cls, filepath):
        obj = cls()
        obj.data = {}
        obj.data.update(mc.RES_DATA_SETTINGS)
        obj.axis_limits = {}
        obj.axis_limits.update(mc.RES_AXES_LIMITS)
        meas_id = os.path.split(filepath)[-1]
        obj.meas_id = meas_id

        for filename in os.listdir(filepath):
            obj.read_nc_file(os.path.join(filepath, filename))

        obj.get_mean_profile()

        obj.set_depol()

        return obj

    def read_nc_file(self, file_name):
        f = netcdf.netcdf_file(file_name, 'r', False, 1)

        file_start = datetime.strptime(str(f.StartDate) + str(f.StartTime_UT).zfill(6), '%Y%m%d%H%M%S')
        file_end = datetime.strptime(str(f.StartDate) + str(f.StopTime_UT).zfill(6), '%Y%m%d%H%M%S')
        self.data['start_time'] = min(self.data['start_time'], file_start)
        self.data['end_time'] = max(self.data['end_time'], file_end)

        alt = np.ma.masked_array(f.variables['Altitude'].data, f.variables['Altitude'].data > 1E30,
                                 fill_value=np.nan) - f.Altitude_meter_asl
        self.data['max_alt'] = max(self.data['max_alt'], max(alt))
        dtype = file_name.split('.')[-1]
        self.data[dtype]['exists'] = True

        for v in mc.RES_VAR_NAMES[dtype]:
            if v in f.variables.keys():
                if v in mc.RES_VAR_NAME_ALIAS.keys():
                    va = mc.RES_VAR_NAME_ALIAS[v]
                else:
                    va = v

                if not (va in self.data[dtype].keys()):
                    self.data[dtype][va] = {'single': []}

                if va in ['Backscatter', 'Extinction']:
                    vdata = np.ma.masked_array(f.variables[v].data / 1.0E-6, f.variables[v].data > 1E30,
                                               fill_value=np.nan)
                else:
                    vdata = np.ma.masked_array(f.variables[v].data * 100., f.variables[v].data > 1E30,
                                               fill_value=np.nan)

                self.data[dtype][va]['single'].append({'alt': alt, 'data': vdata})

        f.close()

    def get_mean_profile(self):
        for dtype in mc.RES_DTYPES_FOR_MEAN_PROFILE:
            for varname in mc.RES_VAR_NAMES[dtype]:
                plot_min = mc.RES_PLOT_DEFAULT_MIN
                plot_max = mc.RES_PLOT_DEFAULT_MAX

                if self.data[dtype]['exists'] and varname in self.data[dtype].keys():
                    single_profiles = self.data[dtype][varname]['single']
                    if len(single_profiles) == 1:
                        self.data[dtype][varname]['mean'] = {'alt': single_profiles[0]['alt'],
                                                        'data': single_profiles[0]['data']}
                    else:
                        min_start = 15000
                        min_start_idx = np.nan
                        max_len = 0
                        for p in range(len(single_profiles)):
                            if single_profiles[p]['alt'][0] < min_start:
                                min_start = single_profiles[p]['alt'][0]
                                min_start_idx = p
                            max_len = max(max_len, len(single_profiles[p]['alt']))

                        data_arr = []
                        alt_arr = []
                        for p in range(len(single_profiles)):

                            idx_shift = int(
                                np.where(single_profiles[min_start_idx]['alt'] == single_profiles[p]['alt'][0])[0])
                            fill_array = np.ma.masked_array(np.ones(idx_shift) * np.nan, mask=True, fill_value=np.nan)
                            d = np.ma.append(fill_array, single_profiles[p][
                                'data'])  # insert nans in the beginning of profile until beginning of its altitude axis fits to the one of max_start_idx
                            a = np.ma.append(fill_array, single_profiles[p]['alt'])

                            fill_length = max_len - len(d)  # len(single_profiles[p]['data'])
                            if fill_length < 0:
                                dd = d[:fill_length]
                                aa = a[:fill_length]
                            else:
                                fill_array = np.ma.masked_array(np.ones(fill_length) * np.nan, mask=True,
                                                                fill_value=np.nan)
                                dd = np.ma.append(d,
                                                  fill_array)  # fill the end of profile with nans until its length is equal max_len
                                aa = np.ma.append(a, fill_array)

                            dd.fill_value = np.nan
                            aa.fill_value = np.nan

                            data_arr.append(dd)
                            alt_arr.append(aa)

                        self.data[dtype][varname]['mean'] = {'data': np.ma.mean(data_arr, axis=0),
                                                        'alt': np.ma.max(alt_arr, axis=0)}

                    plot_max = np.ma.max(self.data[dtype][varname]['mean']['data'])
                    plot_min = np.ma.min(self.data[dtype][varname]['mean']['data'])

                    if varname in self.axis_limits.keys():
                        plot_min = min(self.axis_limits[varname][0], plot_min)
                        plot_max = max(self.axis_limits[varname][1], plot_max)

                self.axis_limits[varname] = (plot_min, plot_max)
                    
    def set_depol(self):
        self.plot_depol = False
        if self.data['b532']['exists'] and ('ParticleDepol' in self.data['b532'].keys()) and (
                    'VolumeDepol' in self.data['b532'].keys()):
            self.pldr532_90 = np.nanpercentile(
                self.data['b532']['ParticleDepol']['mean']['data'][
                    ~self.data['b532']['ParticleDepol']['mean']['data'].mask], 90)
            self.vldr532_90 = np.nanpercentile(
                self.data['b532']['VolumeDepol']['mean']['data'][~self.data['b532']['VolumeDepol']['mean']['data'].mask],
                90)
            self.plot_depol = True
        else:
            self.pldr532_90 = None
            self.vldr532_90 = None
        if self.data['b355']['exists'] and ('ParticleDepol' in self.data['b355'].keys()) and (
            'VolumeDepol' in self.data['b355'].keys()):
            self.pldr355_90 = np.nanpercentile(
                self.data['b355']['ParticleDepol']['mean']['data'][~self.data['b355']['ParticleDepol']['mean']['data'].mask], 90)
            self.vldr355_90 = np.nanpercentile(
                self.data['b355']['VolumeDepol']['mean']['data'][~self.data['b355']['VolumeDepol']['mean']['data'].mask], 90)
            self.plot_depol = True
        else:
            self.pldr355_90 = None
            self.vldr355_90 = None

class ResultPlot(pg.GraphicsLayoutWidget):

    def setup(self, data):
        pass