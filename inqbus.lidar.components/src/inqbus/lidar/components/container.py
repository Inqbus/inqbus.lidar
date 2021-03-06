import datetime
import os
import string
import zipfile
import sys
import traceback as tb
from collections import Counter

import numpy as np
import matplotlib.pyplot as plt
from inqbus.lidar.scc_gui.log import logger
from netCDF4 import Dataset
from scipy.io import netcdf

from inqbus.lidar.components import nameddict, error
from inqbus.lidar.components.error import NoCalIdxFound, PathDoesNotExist, FilesAreDifferent
from inqbus.lidar.components.constants import NO_CLOUD, UNKNOWN_CLOUD, CIRRUS, WATER_CLOUD, NO_CLOUD_MASK, MANUAL_CLOUD_MASK
from inqbus.lidar.components.util import get_file_from_path
from inqbus.lidar.scc_gui.configs import main_config as mc


class BaseContainer(object):
    """
    container of time axis data (start and stop)
    """

    def __init__(self):
        self.header = nameddict.NamedDict()
        self._data = None

    @classmethod
    def create_with_data(cls, in_data, header_info):
        result = cls()

        result._data = in_data
        try:
            result.header.attrs = header_info.attrs.copy()
        except BaseException:
            result.header.attrs = header_info.copy()

        return result

    def append_data(self, new_data, orient='h'):
        """
        append data of another BaseContainer object
        :param new_data:
        :return:
        """
        if orient == 'h':
            self._data = np.hstack((self.data, new_data))
        elif orient == 'v':
            self._data = np.vstack((self.data, new_data))
        else:
            logger.error('incorrect orientation parameter for BaseContainer.append_data')

    @property
    def data(self):
        return self._data


class TimeAxis(BaseContainer):
    """
    container of time axis data as datetetime.datetime s (start and stop)

    >>> a=[[20150501, 60],[20150501, 90], [20150501, 120]]
    >>> stop_times = np.array( a )
    >>> ta = TimeAxis.from_polly_file(stop_times)
    >>> np.array_equal(ta.data,np.array([[datetime.datetime(2015, 5, 1, 0, 0, 30), datetime.datetime(2015, 5, 1, 0, 1), datetime.datetime(2015, 5, 1, 0, 1, 30)], \
                        [datetime.datetime(2015, 5, 1, 0, 1), datetime.datetime(2015, 5, 1, 0, 1, 30), datetime.datetime(2015, 5, 1, 0, 2)]]) )
    True

    """

    def __str__(self):
        return str(self.data)

    @classmethod
    # stop times in polly format (tuple (int: date, int: seconds of day) )
    def from_polly_file(cls, stop_times):
        result = cls()

        stop = []
        for t in stop_times:
            date = datetime.datetime.strptime(str(t[0]), '%Y%m%d')
            stop.append(date + datetime.timedelta(seconds=int(t[1])))

        stop_array = np.array(stop)
        # todo calc mean of time diffs
        start_array = np.ndarray(
            shape=stop_array.shape,
            dtype=stop_array.dtype)
        start_array[1:] = stop_array[:-1]
        # todo stop_array[0] -duration
        start_array[0] = stop_array[0] - (stop_array[1] - stop_array[0])

        result._data = np.vstack((start_array, stop_array))

        return result

    @property
    def start(self):
        """
        >>> a=[[20150501, 60],[20150501, 90], [20150501, 120]]
        >>> stop_times = np.array( a )
        >>> ta = TimeAxis.from_polly_file(stop_times)
        >>> np.array_equal(ta.start,np.array([datetime.datetime(2015, 5, 1, 0, 0, 30), datetime.datetime(2015, 5, 1, 0, 1), datetime.datetime(2015, 5, 1, 0, 1, 30)]) )
        True
        """
        return self.data[0, :]

    @property
    def stop(self):
        """
        >>> a=[[20150501, 60],[20150501, 90], [20150501, 120]]
        >>> stop_times = np.array( a )
        >>> ta = TimeAxis.from_polly_file(stop_times)
        >>> np.array_equal(ta.stop,np.array([datetime.datetime(2015, 5, 1, 0, 1), datetime.datetime(2015, 5, 1, 0, 1, 30), datetime.datetime(2015, 5, 1, 0, 2)]) )
        True
        """
        return self.data[1, :]

    @property
    def time(self):
        """
        >>> a=[[20150501, 60],[20150501, 90], [20150501, 120]]
        >>> stop_times = np.array( a )
        >>> ta = TimeAxis.from_polly_file(stop_times)
        >>> np.array_equal(ta.time, np.array([[datetime.datetime(2015, 5, 1, 0, 0, 30), datetime.datetime(2015, 5, 1, 0, 1)], \
                                              [datetime.datetime(2015, 5, 1, 0, 1),     datetime.datetime(2015, 5, 1, 0, 1, 30)],\
                                              [datetime.datetime(2015, 5, 1, 0, 1, 30), datetime.datetime(2015, 5, 1, 0, 2)]]) )
        True
        """
        return self.data.transpose()

    @property
    def secs_of_meas_start(self):
        # start time in seconds since start of measurement
        return self.start - self.start[0]

    @property
    def secs_of_meas_stop(self):
        # stop time in seconds since start of measurement
        return self.stop - self.start[0]


class Signal(BaseContainer):
    """
    container for a 2-dim (time, height) signal (1 channel only)
    >>> in_data = np.array([[1,2,3,4],[11,22,33,44],[111,222,333,444]])
    >>> in_header ={'wl':355, 'bg':[0,250]}
    >>> s = Signal.from_polly_file(in_data, in_header)
    >>> (s.header == in_header) and np.array_equal(in_data, s.data)
    True
    """

    def __str__(self):
        return str(self.header) + str(self.data)

    @classmethod
    # raw data from nc file and header info
    def from_polly_file(cls, raw_data, header_info):
        result = cls()

        result.header.attrs = header_info.copy()
        result._data = raw_data

        return result


class PreProcessedSignal(BaseContainer):
    """
    container for a 2-dim (time, height) signal (1 channel only)
    >>> in_data = np.array([[1,2,3,4],[11,22,33,44],[111,222,333,444]])
    >>> in_header ={'wl':355, 'bg':[0,250]}
    """

    def __init__(self):
        super(PreProcessedSignal, self).__init__()
        self.bg = None

    def __str__(self):
        return str(self.header) + str(self.data)

    @classmethod
    def from_rawsig(cls, raw_sig, range_axis):
        """
        raw data from nc file and header info
        """
        result = cls()

        result.header.attrs = raw_sig.header.attrs.copy()

        result.bg = TimeSeries.with_data(np.average(
            raw_sig.data[:, result.header.bg_first: result.header.bg_last], axis=1), {'dummy': 0})

        bg_cor_data = np.subtract(
            raw_sig.data, result.bg.data.reshape(len(result.bg.data), 1))
        range_square = (
            np.square(
                range_axis.data).reshape(
                1, len(
                    range_axis.data)))

        result._data = np.multiply(bg_cor_data, range_square)

        return result


class TimeSeries(BaseContainer):
    """
    container for a 1-dim variable (along time axis)
    """

    def __str__(self):
        return str(self.header) + str(self.data)

    @classmethod
    def with_data(cls, data, header_info):
        """raw data from nc file and header info"""
        result = cls()

        result.header.attrs = header_info.copy()
        result._data = data

        return result


class Sonde(object):
    def __init__(self):
        self.header = nameddict.NamedDict()
        self._data = nameddict.NamedDict()

    @classmethod
    def from_file(cls, sonde_filename, measurementID):
        result = cls()

        dummy = {
            'alt': [],
            'pp': [],
            'tt': [],
            'td': [],
            'rh': []}

        sf = open(sonde_filename, 'r')
        lines = sf.readlines()
        l = 0
        while len(str.split(lines[l])) == 0:
            l = + 1
        header_data = str.split(lines[l])
        result.header.location = header_data[1]
        result.header.WMO_id = header_data[0]
        result.header.time = datetime.datetime.strptime(
            ' '.join(header_data[-4:]), '%HZ %d %b %Y')
        result.header.filename = 'rs_' + measurementID + '.nc'

        first_l = 0
        last_l = 0
        for l in range(len(lines)):
            if lines[l].count(mc.SONDE_HEADER_STR) and first_l == 0:
                first_l = l + 2
            if lines[l].count(mc.SONDE_BOTTOM_STR) and last_l == 0:
                last_l = l - 1
            if lines[l].count('latitude'):
                result.header.latitude = float(
                    str.split(lines[l], ':')[1])
            if lines[l].count('longitude'):
                result.header.longitude = float(
                    str.split(lines[l], ':')[1])
            if lines[l].count('elevation'):
                result.header.altitude = float(
                    str.split(lines[l], ':')[1])

        for line in lines[first_l: last_l]:
            try:
                pp = float(line[0:7])
                alt = float(line[7:14])
                tt = float(line[14:21])
                rh = float(line[28:35])
                dummy['pp'].append(pp)
                dummy['alt'].append(alt)
                dummy['tt'].append(tt)
                dummy['rh'].append(rh)
            except BaseException:
                Error = 1
        sf.close()

        for k in dummy.keys():
            result._data.attrs[k] = np.array(dummy[k])

        return result

    @classmethod
    def from_gdas_file(cls, sonde_filename, measurementID):
        result = cls()

        dummy = {'alt': [], 'pp': [], 'tt': [], 'td': []}  # , 'rh':[]}

        sf = open(sonde_filename, 'r')
        lines = sf.readlines()
        sf.close()

        result.header.WMO_id = '_____'

        y = int(lines[0].split()[1])
        m = int(lines[0].split()[3])
        d = int(lines[0].split()[5])
        h = int(lines[0].split()[7])
        result.header.time = datetime.datetime(y, m, d, h)
        result.header.location = 'GDAS_interpolated_to_lidar_site'
        result.header.filename = 'rs_' + measurementID + '.nc'

        result.header.latitude = float(lines[0].split()[-3])
        result.header.longitude = float(lines[0].split()[-1])
        result.header.altitude = mc.NC_FILL_FOAT

        # search for first empty line
        first_line = 0
        while len(lines[first_line].split()) > 0:
            first_line = first_line + 1
        # first data line is 5 lines below
        first_line = first_line + 5

        result.header.altitude = float(
            lines[first_line].split()[1].split('.')[0])
        for l in lines[first_line:]:
            line_data = l.split()
            if len(line_data) >= 4:
                dummy['pp'].append(float(line_data[0]))
                dummy['alt'].append(float(line_data[1].split('.')[0]))
                dummy['tt'].append(float(line_data[2]))
                dummy['td'].append(float(line_data[3]))

        for k in dummy.keys():
            result._data.attrs[k] = np.array(dummy[k])

        return result

    @classmethod
    def from_csv_file(cls, sonde_filename, measurementID):
        result = cls()

        dummy = {'alt': [], 'pp': [], 'tt': [], 'td': [], 'rh': []}

        sf = open(sonde_filename, 'r')
        lines = sf.readlines()

        result.header.WMO_id = os.path.split(sonde_filename)[1].split('_')[1]
        date_str = os.path.split(sonde_filename)[1].split('_')[0]
        time_str = os.path.split(sonde_filename)[1].split('_')[2].split('z')[0]
        result.header.time = datetime.datetime.strptime(
            date_str + time_str, '%y%m%d%H')
        result.header.location = mc.SONDE_STATIONS[result.header.WMO_id]['name']
        result.header.filename = 'rs_' + measurementID + '.nc'

        result.header.latitude = mc.SONDE_STATIONS[result.header.WMO_id]['lat']
        result.header.longitude = mc.SONDE_STATIONS[result.header.WMO_id]['lon']
        result.header.altitude = mc.SONDE_STATIONS[result.header.WMO_id]['alt']

        for l in range(len(lines) - 1, 0, -1):
            line_data = lines[l].split(';')
            try:
                pp = float(line_data[0])
                alt = float(
                    line_data[1].ljust(
                        line_data[1].rfind('.') + 4,
                        '0').replace(
                        '.',
                        ''))
                tt = float(line_data[2].replace(',', '.'))
                rh = float(line_data[4])

                if len(dummy['pp']) == 0:
                    dummy['pp'].append(pp)
                    dummy['alt'].append(alt)
                    dummy['tt'].append(tt)
                    dummy['rh'].append(rh)
                else:
                    if (pp != dummy['pp'][-1]) and (alt != dummy['alt'][-1]):
                        dummy['pp'].append(pp)
                        dummy['alt'].append(alt)
                        dummy['tt'].append(tt)
                        dummy['rh'].append(rh)

            except BaseException:
                Error = 1
        sf.close()

        for k in dummy.keys():
            result._data.attrs[k] = np.array(dummy[k])

        return result

    def write_scc_sonde_file(self):
        dt = datetime.timedelta(hours=2)

        outfile = netcdf.netcdf_file(
            os.path.join(
                mc.OUT_PATH,
                self.header.filename),
            'w',
            False,
            1)

        outfile.Sounding_Start_Date = (
            self.header.time - dt).strftime('%Y%m%d')
        outfile.Sounding_Date_Format = "YYYYMMDD"

        outfile.Sounding_Start_Time_UT = (
            self.header.time - dt).strftime('%H%M%S')
        outfile.Sounding_Stop_Time_UT = self.header.time.strftime('%H%M%S')
        outfile.Sounding_Time_Format = "HHMMSS"

        outfile.Latitude_degrees_north = np.float64(self.header.latitude)
        outfile.Longitude_degrees_east = np.float64(self.header.longitude)
        outfile.Altitude_meter_asl = np.float64(self.header.altitude)
        outfile.Location = self.header.location

        dim = outfile.createDimension('points', len(self.data['pp']))

        pres_var = outfile.createVariable('Pressure', np.float64, ('points',))
        pres_var.Units = 'hPa'
        temp_var = outfile.createVariable(
            'Temperature', np.float64, ('points',))
        temp_var.Units = 'C'
        alt_var = outfile.createVariable('Altitude', np.float64, ('points',))
#        alt_var.Comments = 'Height above lidar station'
        alt_var.Units = 'm'

        pres_var[:] = self.data['pp'][:]
        temp_var[:] = self.data['tt'][:]
        alt_var[:] = self.data['alt'][:] - outfile.Altitude_meter_asl

        if 'mr' in self.data.keys():
            mr_var = outfile.createVariable(
                'MixingRatio', np.float64, ('points',))
            mr_var.Units = 'g/kg'
            mr_var[:] = self.data['mr'][:]

        outfile.close()

    @property
    def data(self):
        return self._data


class ZAxis(object):
    """
    variable container for z values with
    * property range_axis # pointing along the beam
    * property height_axis # height above lidar, vertically pointing
    * property alt_axis # height above sea level, vertically pointing
    """

    def __init__(self):
        self.header = nameddict.NamedDict()
        self._range_axis = None
        self._height_axis = None
        self._altitude_axis = None

    def __str__(self):
        return str(self.header) + str(self.data)

    @classmethod
    def from_polly_file(cls, header_info):
        """
        raw data from nc file and header info
        """
        result = cls()

        result.header.attrs = header_info.copy()
        result.header.range_res = result.header.bin_res * \
            1E-9 * mc.LIGHT_SPEED / 2  # bin resolution in ns
        result.header.vert_res = result.header.range_res * \
            np.cos(np.deg2rad(result.header.zenith_angle))
        # todo: maybe this parameter can later be modified by GUI
        result.header.first_valid_bin = mc.FIRST_VALID_BIN

        return result

    @property
    def range_axis(self):
        if not self._range_axis:
            axis_data = (np.array(range(self.header.points)) + 0.5 -
                         self.header.first_valid_bin) * self.header.range_res
            self._range_axis = BaseContainer.create_with_data(
                axis_data, self.header)
        return self._range_axis

    @property
    def height_axis(self):
        """height above lidar, vertically pointing"""
        if not self._height_axis:
            axis_data = (np.array(range(self.header.points)) + 0.5 -
                         self.header.first_valid_bin) * self.header.vert_res
            self._height_axis = BaseContainer.create_with_data(
                axis_data, self.header)
        return self._height_axis

    @property
    def alt_axis(self):
        """height above sea level, vertically pointing"""
        if not self._altitude_axis:
            axis_data = (np.array(range(self.header.points)) + 0.5 - \
                         self.header.first_valid_bin) * self.header.vert_res + self.header.altitude
            self._altitude_axis = BaseContainer.create_with_data(
                axis_data, self.header)
        return self._altitude_axis

    def m_2_bin(self, altitude_m):
        """height above lidar to bin"""
        res =  np.where(self._height_axis.data > altitude_m)
        res = res[0][0]
        return res

    def bin_2_height(self, bin):
        """bin to height above lidar"""
        res = self.height_axis[bin - self.header.first_valid_bin]
        return res


class Measurement(object):
    """
    container for a whole measurement
    """

    def __init__(self):
        self.header = nameddict.NamedDict()
        self.time_axis = None

        self.z_axis = None
        self.signals = nameddict.NamedDict()
        self.pre_processed_signals = nameddict.NamedDict()
        self.sounding = None
        self.shots = None
        self.depol_cal_angle = None
        self.shutter = None
        self.mask = None
        # will be set by read_signal
        self.cloud_mask = None
        # will be set by read_signal
        self.header.cloud_mask_type = NO_CLOUD_MASK
        self.title = None
        self.telecover_data = {'profiles':{},
                               'used_sectors':[],
                               'used_tc_sectors': [],
                               'sectors_for_avrg':[]}


    def set_cloud_region(self, bin_region, cloud_type):
        """bin_region = selected altitude region in bins (incl. pre-trigger bins). """
        self.cloud_mask[:, bin_region[0]: bin_region[1]] = cloud_type
        self.header.cloud_mask_type = MANUAL_CLOUD_MASK

    def remove_cloud_mask(self):
        """remove complete cloud_mask """
        self.cloud_mask[:, :] = NO_CLOUD
        self.header.cloud_mask_type = NO_CLOUD_MASK

    def set_telecover_region(self, a_region, sector_name):
        if not sector_name in self.telecover_data['used_sectors']:
            self.telecover_data['used_sectors'].append(sector_name)

            if sector_name in mc.TC_SECTORS:
                self.telecover_data['used_tc_sectors'].append(sector_name)

            if sector_name in mc. SECTORS_FOR_AVRG:
                self.telecover_data['sectors_for_avrg'].append(sector_name)

        self.telecover_data['profiles'][sector_name] = {'start_idx': a_region[0], 'stop_idx': a_region[1]}

# for testing with file 2018_03_24_Sat_DW_12_00_01.nc.zip
#        self.telecover_data['profiles']['north'] = {'start_idx': 150, 'stop_idx': 162}
#        self.telecover_data['profiles']['west'] = {'start_idx': 165, 'stop_idx': 177}
#        self.telecover_data['profiles']['south'] = {'start_idx': 179, 'stop_idx': 190}
#        self.telecover_data['profiles']['east'] ={'start_idx': 193, 'stop_idx': 203}
#        self.telecover_data['profiles']['north2'] = {'start_idx': 206, 'stop_idx': 216}
#        self.telecover_data['used_sectors'] = ['north', 'west', 'east', 'south', 'north2']
#        self.telecover_data['sectors_for_avrg'] = ['north', 'west', 'east', 'south']

    def plot_tc_output_per_ratio(self):
        # plot data in near range (r=0) and far range(r=1)

        ratio_data = self.telecover_data['ratios']

        out_dir = os.path.join(mc.TELECOVER_PATH, '{}_telecover'.format(self.telecover_data['tc_date'].strftime('%Y%m%d')))
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        for r in range(len(mc.TC_RANGE_ID)):
            max_plot_bin = np.where(self.telecover_data['range_smooth'] > mc.TC_MAX_PLOT_HEIGHT[r])[0][0]
            min_plot_bin = np.where(self.telecover_data['range_smooth'] > 0)[0][0]

            fig, axes = plt.subplots(nrows=len(mc.TC_RATIOS), ncols=2, sharex=True, figsize=(8.2, 11.6))
#            fig, axes = plt.subplots(nrows=4, ncols=2, sharex=True, figsize=(8.2, 11.6))


            for ratio in mc.TC_RATIOS:
                r_name = mc.TC_RATIO_NAMES[ratio]
                prow = ratio

                pcol = 0

                ymax = 0
                ymin = 1e6

                for sector in self.telecover_data['used_tc_sectors']:
                    axes[prow, pcol].plot(self.telecover_data['range_smooth'][0: max_plot_bin],
                                          ratio_data[sector][r_name][0: max_plot_bin],
                                          color=mc.TC_COLORS[sector], label=sector)
                    ymax = max(ymax, np.nanpercentile(ratio_data[sector][r_name][min_plot_bin : max_plot_bin], 97))
                    ymin = min(ymin, np.nanpercentile(ratio_data[sector][r_name][min_plot_bin : max_plot_bin], 7))

                axes[prow, pcol].plot(self.telecover_data['range_smooth'][0: max_plot_bin],
                                      self.telecover_data['mean'][r_name][0: max_plot_bin],
                                      color='grey', linestyle='--', label='mean')

                axes[prow, pcol].set_ylim((0, ymax))
                axes[prow, pcol].set_title('normalized ' + r_name, fontsize=10, verticalalignment='bottom')
                axes[prow, pcol].grid()

                pcol = 1
                for sector in self.telecover_data['used_tc_sectors']:
                    axes[prow, pcol].plot(self.telecover_data['range_smooth'][0: max_plot_bin],
                                          ratio_data[sector][r_name+'_dev'][0: max_plot_bin],
                                          color=mc.TC_COLORS[sector], label=sector)
                axes[prow, pcol].set_title('deviation ' + r_name, fontsize=10, verticalalignment='bottom')
                axes[prow, pcol].grid()

            for prow in range(len(mc.TC_RATIOS)):
                axes[prow, 0].set_ylabel('signal ratio')
                #axes[prow, 0].set_ylim((ymin, ymax))
                axes[prow, 1].set_ylim((-.3, .3))
                for pcol in [0, 1]:
                    axes[prow, pcol].set_xlim((0, mc.TC_MAX_PLOT_HEIGHT[r]))

            for pcol in [0, 1]:
                axes[len(mc.TC_RATIOS)-1, pcol].set_xlabel('height, m')

            plt.subplots_adjust(wspace=0.15, hspace=0.15)  # right = 0.83
            plt.figtext(0.1, 0.96,
                        mc.LIDAR_NAME + ' telecover ratios ' +
                        self.telecover_data['tc_date'].strftime('%d.%m.%Y') +
                        ' normalized: ' + str(mc.TC_NORMALIZATION_RANGE) + 'm',
                        fontsize=14)
            axes[0, 0].legend(bbox_to_anchor=(0., 1.12, 2.05, .102), loc=3, ncol=6, mode="expand", borderaxespad=0.)

            plt.savefig(
                os.path.join(out_dir, 'telecover_ratios_' + mc.TC_RANGE_ID[r] + '_' + self.telecover_data['tc_date'].strftime('%Y%m%d') + '.png'))
            plt.close()

    def plot_tc_output_per_channel(self, data, ref_data_name, percentile_range, fixed_axis_range, plot_label, title_str):
        min_percentile = percentile_range[0]
        max_percentile = percentile_range[1]

        out_dir = os.path.join(mc.TELECOVER_PATH, '{}_telecover'.format(self.telecover_data['tc_date'].strftime('%Y%m%d')))
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        # plot data in near range (r=0) and far range(r=1)
        for r in range(len(mc.TC_RANGE_ID)):
            max_plot_bin = np.where(self.telecover_data['range_smooth'] > mc.TC_MAX_PLOT_HEIGHT[r])[0][0]
            min_plot_bin = np.where(self.telecover_data['range_smooth'] > 0)[0][0]

            fig, axes = plt.subplots(nrows=3, ncols=2, sharex=True, sharey=True, figsize=(8.2, 11.6))

            ymax = 0
            ymin = 1e6
            for ch in mc.TC_CHANNELS:
                for sector in self.telecover_data['used_tc_sectors']:
                    ymax = max(ymax, np.nanpercentile(data[sector][ch][min_plot_bin+1: max_plot_bin], max_percentile) )
                    ymin = min(ymin, np.nanpercentile(data[sector][ch][min_plot_bin+1: max_plot_bin], min_percentile))

            if ~np.isnan(fixed_axis_range[0]):
                ymin = fixed_axis_range[0]
            if ~np.isnan(fixed_axis_range[1]):
                ymax = fixed_axis_range[1]

            for ch in mc.TC_CHANNELS:
                ch_idx = mc.TC_CHANNELS.index(ch)
                prow = int(ch_idx / 2)
                pcol = ch_idx % 2

                for sector in self.telecover_data['used_tc_sectors']:
                    axes[prow, pcol].plot(self.telecover_data['range_smooth'][0: max_plot_bin],
                                          data[sector][ch][0: max_plot_bin],
                                          color=mc.TC_COLORS[sector], label=sector)

                if ref_data_name != '':
                    axes[prow, pcol].plot(self.telecover_data['range_smooth'][0: max_plot_bin],
                                      self.telecover_data[ref_data_name][ch][0: max_plot_bin],
                                      color = 'grey', linestyle = '--', label = ref_data_name)

                axes[prow, pcol].set_title(mc.TC_CHANNEL_NAMES[ch], fontsize=10, verticalalignment='bottom')
                axes[prow, pcol].grid()

            for prow in range(3):
                axes[prow, 0].set_ylabel(plot_label)
                for pcol in [0, 1]:
                    axes[prow, pcol].set_xlim((0, mc.TC_MAX_PLOT_HEIGHT[r]))
                    axes[prow, pcol].set_ylim((ymin, ymax))

            for pcol in [0, 1]:
                axes[2, pcol].set_xlabel('height, m')

            plt.subplots_adjust(wspace=0.05, hspace=0.15)  # right = 0.83
            plt.figtext(0.2, 0.96, mc.LIDAR_NAME + ' telecover ' + self.telecover_data['tc_date'].strftime('%d.%m.%Y') + title_str, fontsize=14)
            axes[0, 0].legend(bbox_to_anchor=(0., 1.1, 2.05, .102), loc=3, ncol=6, mode="expand", borderaxespad=0.)

            plt.savefig(
                os.path.join(out_dir,
                             'telecover_{}_'.format(plot_label) + mc.TC_RANGE_ID[r] + '_' + self.telecover_data['tc_date'].strftime('%Y%m%d') + '.png'))
            plt.close()

    def export_telecover_to_ASCII(self):
        r_axis = self.z_axis.range_axis.data
        max_output_bin = np.where(r_axis > mc.TC_MAX_OUTPUT_HEIGHT)[0][0]
        first_output_bin = np.where(r_axis > 0)[0][0]

        out_dir = os.path.join(mc.TELECOVER_PATH, '{}_telecover'.format(self.telecover_data['tc_date'].strftime('%Y%m%d')))
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        for ch in mc.TC_CHANNELS:
            channel_name = mc.TC_CHANNEL_NAMES[ch].replace( ' ', '_')
            outfilename = 'telecover_' + channel_name + '_' + self.telecover_data['tc_date'].strftime('%Y%m%d') + '.txt'
            #print(outfilename)
            outfile = open(os.path.join(out_dir, outfilename), 'w')

            outfile.write(mc.TC_STATION_NAME + '\n')
            outfile.write(mc.LIDAR_NAME + ' \n')
            outfile.write(mc.TC_CHANNEL_NAMES[ch] + ', photon counting \n')
            outfile.write(self.telecover_data['tc_date'].strftime('%d.%m.%Y') + '\n')
            outfile.write('range')
            for sector in self.telecover_data['used_sectors']:
                outfile.write(', ' + sector)
            outfile.write('\n')

            for r in range(first_output_bin, max_output_bin):
                outfile.write( str(r_axis[r]) )
                for sector in self.telecover_data['used_sectors']:
                    outfile.write(', ' + str(self.telecover_data['rc_signals'][sector][ch][r]) )
                outfile.write('\n')

            outfile.close()

    def analyse_telecover(self):
        norm_bin_first = np.where(self.z_axis.height_axis.data > mc.TC_NORMALIZATION_RANGE[0])[0][0]
        norm_bin_last  = np.where(self.z_axis.height_axis.data > mc.TC_NORMALIZATION_RANGE[1])[0][0]
        points_smooth = int(self.z_axis.height_axis.data.size / mc.TC_SMOOTH_BINS)
        self.telecover_data['range_smooth'] = np.average(self.z_axis.range_axis.data.reshape((points_smooth, mc.TC_SMOOTH_BINS)), axis=1)
        self.telecover_data['tc_date'] = self.time_axis.start[0]

        # for each channel and each sector: calculate range-corrected signals
        # for each channel and each sector: calculate normalized signals
        # smooth
        self.telecover_data['rc_signals'] = {}
        self.telecover_data['sm_rc_signals'] = {}
        self.telecover_data['sm_norm_signals'] = {}

        for sector in self.telecover_data['used_sectors']:
            self.telecover_data['rc_signals'][sector] = {}
            self.telecover_data['sm_rc_signals'][sector] = {}
            self.telecover_data['sm_norm_signals'][sector] = {}

            first = self.telecover_data['profiles'][sector]['start_idx']
            last  = self.telecover_data['profiles'][sector]['stop_idx']
            if self.time_axis.start[first] > self.telecover_data['tc_date']:
                self.telecover_data['tc_date'] = self.time_axis.start[first]

            for ch in mc.TC_CHANNELS:
                rc_signal = np.average(self.pre_processed_signals[ch].data[first:last], axis = 0)
                self.telecover_data['rc_signals'][sector][ch] = rc_signal
                self.telecover_data['sm_rc_signals'][sector][ch] = np.average(rc_signal.reshape((points_smooth, mc.TC_SMOOTH_BINS)), axis=1)

                norm = np.average(self.telecover_data['rc_signals'][sector][ch][norm_bin_first: norm_bin_last])
                norm_signal = self.telecover_data['rc_signals'][sector][ch] / norm
                self.telecover_data['sm_norm_signals'][sector][ch] = np.average(norm_signal.reshape((points_smooth, mc.TC_SMOOTH_BINS)), axis=1)

        # for each channel: calculate mean of all sectors
        self.telecover_data['mean'] = {}
        for ch in mc.TC_CHANNELS:
            data = np.array([])
            for sector in self.telecover_data['sectors_for_avrg']:
                data = np.append(data, self.telecover_data['sm_norm_signals'][sector][ch])
            data = data.reshape(len(self.telecover_data['sectors_for_avrg']), points_smooth)
            self.telecover_data['mean'][ch] = np.average(data, axis = 0)

        # for each channel and each sector: calculate deviation from mean
        self.telecover_data['dev'] = {}
        for sector in self.telecover_data['used_tc_sectors']:
            self.telecover_data['dev'][sector] = {}
            for ch in mc.TC_CHANNELS:
                sector_data = self.telecover_data['sm_norm_signals'][sector][ch]
                mean = self.telecover_data['mean'][ch]
                data = ( sector_data - mean) / mean
                data[np.where(np.isinf(data))[0]] = np.nan
                self.telecover_data['dev'][sector][ch] = data

        # for each channel and each sector: calculate ratio to mean
        self.telecover_data['ratio'] = {}
        for sector in self.telecover_data['used_tc_sectors']:
            self.telecover_data['ratio'][sector] = {}
            for ch in mc.TC_CHANNELS:
                sector_data = self.telecover_data['sm_norm_signals'][sector][ch]
                mean = self.telecover_data['mean'][ch]
                data = sector_data / mean
                data[np.where(np.isinf(data))[0]] = np.nan
                self.telecover_data['ratio'][sector][ch] = data

        # for each channel: calculate RMSD
        self.telecover_data['RMSD'] = {}
        for ch in mc.TC_CHANNELS:
            data = np.zeros(points_smooth)
            for sector in self.telecover_data['sectors_for_avrg']:
                data = data + np.square(self.telecover_data['dev'][sector][ch])
            self.telecover_data['RMSD'][ch] = np.sqrt( data / len(self.telecover_data['sectors_for_avrg']) )

        # for each sector: calculate signal ratios
        self.telecover_data['ratios'] = {}
        for sector in self.telecover_data['used_tc_sectors']:
            self.telecover_data['ratios'][sector] = {}
            for r in mc.TC_RATIOS:
                # calc ratio for each sector
                nom_data   = self.telecover_data['sm_norm_signals'][sector][mc.TC_NOMINATORS[r]]
                denom_data = self.telecover_data['sm_norm_signals'][sector][mc.TC_DENOMINATORS[r]]
                ratio = nom_data/ denom_data
                ratio[np.where(np.isinf(ratio))[0]] = np.nan
                self.telecover_data['ratios'][sector][mc.TC_RATIO_NAMES[r]] = ratio

        for r in mc.TC_RATIOS:
            # calc average of all sectors
            data = np.array([])
            for sector in self.telecover_data['sectors_for_avrg']:
                data = np.append(data, self.telecover_data['ratios'][sector][mc.TC_RATIO_NAMES[r]])
            data = data.reshape(len(self.telecover_data['sectors_for_avrg']), points_smooth)
            self.telecover_data['mean'][mc.TC_RATIO_NAMES[r]] = np.average(data, axis = 0)

            # calc deviation of signal ratios from their mean
            mean = self.telecover_data['mean'][mc.TC_RATIO_NAMES[r]]
            for sector in self.telecover_data['used_tc_sectors']:
                sector_data = self.telecover_data['ratios'][sector][mc.TC_RATIO_NAMES[r]]
                dev = (sector_data - mean) / mean
                dev[np.where(np.isinf(dev))[0]] = np.nan
                self.telecover_data['ratios'][sector][mc.TC_RATIO_NAMES[r] + '_dev'] = dev

        self.plot_tc_output_per_channel(self.telecover_data['sm_rc_signals'], '', (0, 100), (0, np.nan), 'rc_signal', '')
        self.plot_tc_output_per_channel(self.telecover_data['sm_norm_signals'], 'mean',
                                        (0, 100), (0, np.nan), 'norm_signal',  ' normalized: ' + str(mc.TC_NORMALIZATION_RANGE) + 'm')
        self.plot_tc_output_per_channel(self.telecover_data['dev'], 'RMSD', (10, 90), (-0.3, 0.3), 'deviations', ' normalized: ' + str(mc.TC_NORMALIZATION_RANGE) + 'm')
        self.plot_tc_output_per_channel(self.telecover_data['ratio'], '', (10, 90), (0, np.nan), 'ratio_to_mean', ' normalized: ' + str(mc.TC_NORMALIZATION_RANGE) + 'm')
        self.plot_tc_output_per_ratio()
        self.export_telecover_to_ASCII()

    def read_signal(self, sig_filename):
        if sig_filename.endswith('.zip'):
            if os.path.exists(mc.TEMP_PATH):
                zfile = zipfile.ZipFile(sig_filename)
                nc_filename = zfile.extract(zfile.namelist()[0], mc.TEMP_PATH)
                zfile.close()
            else:
                logger.error('%s does not exist' % mc.TEMP_PATH)
                raise PathDoesNotExist
        elif sig_filename.endswith('.nc'):
            nc_filename = sig_filename

        nc_file = netcdf.netcdf_file(nc_filename, 'r', False, 1)

        self.title = get_file_from_path(sig_filename)

        self.header.latitude = nc_file.variables['location_coordinates'].data[0]
        self.header.longitude = nc_file.variables['location_coordinates'].data[1]
        self.header.altitude = nc_file.variables['location_height'].getValue()
        self.header.points = nc_file.dimensions['height']
        self.header.time_len = len(nc_file.variables['measurement_time'].data)
        self.header.nb_of_time_scales = mc.NB_OF_TIME_SCALES
        self.header.nb_of_scan_angles = mc.NB_OF_SCAN_ANGLES
        self.header.num_channels = nc_file.dimensions['channel'] + \
            mc.NUM_DOUBLE_CHANNELS
        # in ns
        self.header.bin_res = nc_file.variables['measurement_height_resolution'].getValue(
        )
        self.header.zenith_angle = nc_file.variables['zenithangle'].getValue()

        self.header.measurement_id = None
        self.header.comment = None
        self.header.pressure = mc.GROUND_PRES
        self.header.temperature = mc.GROUND_TEMP

        self.time_axis = TimeAxis.from_polly_file(
            nc_file.variables['measurement_time'].data)
        self.z_axis = ZAxis.from_polly_file(
            {
                'points': self.header.points,
                'bin_res': self.header.bin_res,
                'zenith_angle': self.header.zenith_angle,
                'altitude': self.header.altitude})
        self.shots = TimeSeries.with_data(
            nc_file.variables['measurement_shots'].data[:, 0], {'dummy': 0})
        self.depol_cal_angle = TimeSeries.with_data(
            nc_file.variables['depol_cal_angle'].data, {'dummy': 0})
        self.mask = np.ones((self.header.time_len,), dtype=bool)
        self.cloud_mask = np.ones((self.header.time_len, self.header.points), dtype=int) * NO_CLOUD

        for ch in range(
                nc_file.dimensions['channel'] +
                mc.NUM_DOUBLE_CHANNELS):
            channel_info = {}
            # todo: user defined parameter  via GUI?
            channel_info['bg_first'] = mc.BG_FIRST[ch]
            channel_info['bg_last'] = mc.BG_LAST[ch]
            channel_info['channel_id'] = mc.CHANNEL_ID[ch]
            channel_info['channel_name'] = mc.CHANNEL_ID_STR[ch]
            channel_info['range_id'] = mc.RANGE_ID[ch]
            channel_info['first_valid_bin'] = self.z_axis.header.first_valid_bin
            self.signals[mc.CHANNEL_NAMES[ch]] = Signal.from_polly_file(
                nc_file.variables['raw_signal'].data[:, :, mc.CHAN_NC_POS[ch]], channel_info)
            self.pre_processed_signals[mc.CHANNEL_NAMES[ch]] = PreProcessedSignal.from_rawsig(
                self.signals[mc.CHANNEL_NAMES[ch]], self.z_axis.range_axis)

        nc_file.close()


    def append_nc_file(self, sig_filename):
        if sig_filename.endswith('.zip'):
            if os.path.exists(mc.TEMP_PATH):
                zfile = zipfile.ZipFile(sig_filename)
                nc_filename = zfile.extract(zfile.namelist()[0], mc.TEMP_PATH)
                zfile.close()
            else:
                logger.error('%s does not exist' % mc.TEMP_PATH)
                raise PathDoesNotExist
        elif sig_filename.endswith('.nc'):
            nc_filename = sig_filename

        nc_file = netcdf.netcdf_file(nc_filename, 'r', False, 1)
        new_time_len = len(nc_file.variables['measurement_time'].data)
        self.header.time_len = self.header.time_len + new_time_len

        if self.header.latitude != nc_file.variables['location_coordinates'].data[0] or \
            self.header.longitude != nc_file.variables['location_coordinates'].data[1] or \
            self.header.altitude != nc_file.variables['location_height'].getValue() or \
            self.header.points != nc_file.dimensions['height'] or \
            self.header.num_channels != nc_file.dimensions['channel'] + mc.NUM_DOUBLE_CHANNELS or \
            self.header.bin_res != nc_file.variables['measurement_height_resolution'].getValue() or \
            self.header.zenith_angle != nc_file.variables['zenithangle'].getValue():
            raise FilesAreDifferent

        new_time_axis = TimeAxis.from_polly_file(nc_file.variables['measurement_time'].data)
        self.time_axis.append_data(new_time_axis.data)
        new_shots = TimeSeries.with_data(nc_file.variables['measurement_shots'].data[:, 0], {'dummy': 0})
        self.shots.append_data(new_shots.data)
        new_depol_cal_angle = TimeSeries.with_data(nc_file.variables['depol_cal_angle'].data, {'dummy': 0})
        self.depol_cal_angle.append_data(new_depol_cal_angle.data)

        self.mask = np.hstack((self.mask, np.ones((new_time_len,), dtype=bool)))
        self.cloud_mask = np.vstack((self.cloud_mask, np.ones((new_time_len, self.header.points), dtype=int) * NO_CLOUD))

        for ch in range(self.header.num_channels):
            old_sig = self.signals[mc.CHANNEL_NAMES[ch]]
            new_signal = Signal.from_polly_file(
                 nc_file.variables['raw_signal'].data[:, :, mc.CHAN_NC_POS[ch]], old_sig.header.attrs)
            old_sig.append_data(new_signal.data, orient='v')

            old_pp_sig = self.pre_processed_signals[mc.CHANNEL_NAMES[ch]]
            new_pp_sig = PreProcessedSignal.from_rawsig(new_signal, self.z_axis.range_axis)
            old_pp_sig.append_data(new_pp_sig.data, orient='v')

        nc_file.close()

    def read_log(self, lidarlog_filename):
        if lidarlog_filename:
            try:
                log_file = open(lidarlog_filename, 'r')
            except IOError:
                logger.warning("Lidar Log %s does not exist." % lidarlog_filename)
                raise error.LidarFileNotFound

            data = {
                'time': [],
                'T1064': [],
                'T1': [],
                'T2': [],
                'pyro': [],
                'Tout': [],
                'RHout': [],
                'status': [],
                'roof_closed': [],
                'rain': [],
                'radar_shutter_close': []}

            lines = log_file.readlines()
            for l in lines[3:]:
                line_data = l.split()
                data_ok = True
                for ld in line_data[2:]:
                    if float(ld) < -100:
                        data_ok = False
                if data_ok:
                    time = datetime.datetime.strptime(
                        line_data[0] + line_data[1], '%d.%m.%Y%H:%M:%S')
                    status = int(line_data[8])
                    roof_closed = status & 1 == 1
                    rain = not(status & 2 == 2)
                    radar_shutter_closed = status & 4 == 4
                    data['time'].append(time)
                    data['T1064'].append(line_data[2])
                    data['T1'].append(line_data[3])
                    data['T2'].append(line_data[4])
                    data['pyro'].append(line_data[5])
                    data['Tout'].append(line_data[6])
                    data['RHout'].append(line_data[7])
                    data['status'].append(line_data[8])
                    data['roof_closed'].append(roof_closed)
                    data['rain'].append(rain)
                    data['radar_shutter_close'].append(radar_shutter_closed)
            log_file.close()

            time_array = np.array(data['time'])
            shutter_array = np.array(data['radar_shutter_close'])
            sum_shutter = []
            for t in range(self.header.time_len):
                f_idx = np.where(time_array >= self.time_axis.start[t])[0]
                l_idx = np.where(time_array < self.time_axis.stop[t])[0]
                if (len(f_idx) > 0) and (len(l_idx) > 0):
                    sum_shutter.append(np.count_nonzero(
                        shutter_array[f_idx[0]: l_idx[-1] + 1]))
                else:
                    sum_shutter.append(np.nan)

            self.shutter = TimeAxis.create_with_data(
                np.array(sum_shutter), {'dummy': 0})

    def read_sonde(self, sonde_name):
        if sonde_name == '':
            self.sounding = None
        else:
            if sonde_name.count('gdas'):
                self.sounding = Sonde.from_gdas_file(os.path.join(
                    mc.SONDE_PATH, sonde_name), self.header.measurement_id)
            else:
                if sonde_name.endswith('.txt'):
                    self.sounding = Sonde.from_file(
                        os.path.join(
                            mc.SONDE_PATH,
                            sonde_name),
                        self.header.measurement_id)
                elif sonde_name.endswith('.csv'):
                    self.sounding = Sonde.from_csv_file(os.path.join(
                        mc.SONDE_PATH, sonde_name), self.header.measurement_id)
                else:
                    raise error.WrongFileFormat

    def write_scc_raw_signal(self, filename):

        nc_file = Dataset(filename, "w", format="NETCDF4")
        self.mask[np.where(self.shots.data <= 0)] = 0
        self.mask[np.where(self.depol_cal_angle.data.round()
                           != mc.CAL_ANGLE_MEASUREMENT)] = 0

        # create dimensions
        dim = nc_file.createDimension('points', self.header.points)
        dim = nc_file.createDimension('channels', self.header.num_channels)
        dim = nc_file.createDimension('time', self.mask.sum())
        dim = nc_file.createDimension(
            'nb_of_time_scales',
            self.header.nb_of_time_scales)
        dim = nc_file.createDimension(
            'scan_angles', self.header.nb_of_scan_angles)

        # 'write_attributes'
        nc_file.Measurement_ID = self.header.measurement_id
        nc_file.RawData_Start_Date = self.time_axis.start[self.mask][0].strftime(
            '%Y%m%d')
        nc_file.RawData_Start_Time_UT = self.time_axis.start[self.mask][0].strftime(
            '%H%M%S')
        nc_file.RawData_Stop_Time_UT = self.time_axis.stop[self.mask][-1].strftime(
            '%H%M%S')
        if self.sounding:
            nc_file.Sounding_File_Name = self.sounding.header.filename
            self.sounding.write_scc_sonde_file()
        if 'comment' in self.header.attrs:
            nc_file.Comment = self.header.comment

        # 'create variables'

        bg_height_last_var = nc_file.createVariable(
            'Background_High', 'f8', ('channels',))  # 'f8' = np.float64
        bg_height_first_var = nc_file.createVariable('Background_Low',
                                                     'f8', ('channels',))
        bg_mode_var = nc_file.createVariable(
            'Background_Mode', 'i4', ('channels',))  # 'i4' = np.int32
        lr_input_var = nc_file.createVariable('LR_Input',
                                              'i4', ('channels',))
        angle_var = nc_file.createVariable('Laser_Pointing_Angle',
                                           'f8', ('scan_angles',))
        angle_id_var = nc_file.createVariable(
            'Laser_Pointing_Angle_of_Profiles', 'i4', ('time', 'nb_of_time_scales'))
        shots_var = nc_file.createVariable('Laser_Shots',
                                           'i4', ('time', 'channels'))
        mol_calc_var = nc_file.createVariable('Molecular_Calc',
                                              'i4', ())
        pres_var = nc_file.createVariable('Pressure_at_Lidar_Station',
                                          'f8', ())
        temp_var = nc_file.createVariable('Temperature_at_Lidar_Station',
                                          'f8', ())
        range_res_var = nc_file.createVariable('Raw_Data_Range_Resolution',
                                               'f8', ('channels',))
        start_var = nc_file.createVariable('Raw_Data_Start_Time',
                                           'i4', ('time', 'nb_of_time_scales'))
        stop_var = nc_file.createVariable('Raw_Data_Stop_Time',
                                          'i4', ('time', 'nb_of_time_scales'))
        data_var = nc_file.createVariable('Raw_Lidar_Data',
                                          'f8', ('time', 'channels', 'points'))
        range_id_var = nc_file.createVariable('ID_Range',
                                              'i4', ('channels',))
        ch_id_var = nc_file.createVariable('channel_ID',
                                           'i4', ('channels',))
        ch_name_var = nc_file.createVariable('channel_string_ID',
                                             str, ('channels',))
        time_scale_id_var = nc_file.createVariable('id_timescale',
                                                   'i4', ('channels',))

        if self.header.cloud_mask_type == MANUAL_CLOUD_MASK:
            cloud_mask_var = nc_file.createVariable('cloud_mask',
                                                    'i4', ('time', 'points'))
            cloud_mask_channel_var = nc_file.createVariable('cloud_mask_channel_idx',
                                                    'i4', ())

        # write data
        for ch in range(self.header.num_channels):
            range_res_var[ch] = self.z_axis.header.range_res
            bg_height_first_var[ch] = self.signals[mc.CHANNEL_NAMES[ch]
                                                   ].header.bg_first
            bg_height_last_var[ch] = self.signals[mc.CHANNEL_NAMES[ch]
                                                  ].header.bg_last
            time_scale_id_var[ch] = 0
            ch_id_var[ch] = mc.NC_FILL_INT
            ch_name_var[ch] = self.signals[mc.CHANNEL_NAMES[ch]
                                           ].header.channel_name
            lr_input_var[ch] = 1
            bg_mode_var[ch] = 0
            range_id_var[ch] = self.signals[mc.CHANNEL_NAMES[ch]
                                            ].header.range_id

            # todo: check what is really written into the ncfile
            shots_var[:, ch] = self.shots.data[self.mask][:]
            data_var[:, ch, :] = self.signals[mc.CHANNEL_NAMES[ch]
                                              ].data[self.mask][:, :]

        angle_var[0] = self.z_axis.header.zenith_angle

        if self.header.cloud_mask_type == MANUAL_CLOUD_MASK:
            cloud_mask_var[:, :] = self.cloud_mask[self.mask][:, :]
            cloud_mask_channel_var.assignValue(mc.CLOUD_MASK_CHANNEL_IDX)


        #value = 0 -> automatic (try model - if available, next use standard atmosphere), 1 -> sounding, 2 -> temp from model (by SCC)
        if self.sounding:
            mol_calc_var.assignValue(1)
        else:
            mol_calc_var.assignValue(0)

        pres_var.assignValue(self.header.pressure)
        temp_var.assignValue(self.header.temperature)

        for t in range(self.mask.sum()):
            angle_id_var[t, 0] = 0
            start_var[t, 0] = self.time_axis.secs_of_meas_start[self.mask][t].seconds - \
                self.time_axis.secs_of_meas_start[self.mask][0].seconds
            stop_var[t, 0] = self.time_axis.secs_of_meas_stop[self.mask][t].seconds - \
                self.time_axis.secs_of_meas_start[self.mask][0].seconds

        nc_file.close()

    @classmethod
    def from_nc_file(cls, sig_filename, syslog_filename):
        result = cls()
        try:
            Measurement.read_signal(result, sig_filename)
        except error.LidarError:
            logger.error("Exception: %s" % sys.exc_info()[0])
            logger.error("Traceback: %s" % tb.format_exc())

        try:
            Measurement.read_log(result, syslog_filename)
        except error.LidarFileNotFound:
            pass
        except error.LidarError:
            logger.error("Exception: %s" % sys.exc_info()[0])
            logger.error("Traceback: %s" % tb.format_exc())

        return result

    def find_depol_cal_idxs(self):
        non_0_idx = np.where(self.depol_cal_angle.data.round()
                             != mc.CAL_ANGLE_MEASUREMENT)[0]
        cal_angles = Counter(
            self.depol_cal_angle.data[non_0_idx]).most_common(2)
        idxs = []
        for ca in cal_angles:
            idxs.append(np.where(self.depol_cal_angle.data == ca[0])[0][1:])
        return idxs

    def write_scc_depolcal_signal(self):
        cal_idxs = self.find_depol_cal_idxs()
        if not cal_idxs:
            raise NoCalIdxFound()
        else:
            length = min(cal_idxs[0].size, cal_idxs[1].size)

            filename = os.path.join(
                mc.OUT_PATH, self.scc_depolcal_filename(cal_idxs))

            nc_file = Dataset(filename, "w", format="NETCDF4")

            self.mask[np.where(self.shots.data <= 0)] = 0

            # create dimensions
            dim = nc_file.createDimension('points', self.header.points)
            dim = nc_file.createDimension('channels', mc.NUM_CAL_CHANNELS)
            dim = nc_file.createDimension('time', length)
            dim = nc_file.createDimension(
                'nb_of_time_scales', self.header.nb_of_time_scales)
            dim = nc_file.createDimension(
                'scan_angles', self.header.nb_of_scan_angles)

            # 'write_attributes'
            nc_file.Measurement_ID = self.header.measurement_id
            nc_file.RawData_Start_Date = self.time_axis.start[cal_idxs[0][0]].strftime(
                '%Y%m%d')
            nc_file.RawData_Start_Time_UT = self.time_axis.start[cal_idxs[0][0]].strftime(
                '%H%M%S')
            nc_file.RawData_Stop_Time_UT = self.time_axis.stop[cal_idxs[1][-1]].strftime(
                '%H%M%S')
            if self.sounding:
                nc_file.Sounding_File_Name = self.sounding.header.filename
                self.sounding.write_scc_sonde_file()
            if 'comment' in self.header.attrs:
                nc_file.Comment = self.header.comment

            # 'create variables'

            bg_height_last_var = nc_file.createVariable('Background_High',
                                                        'f8', ('channels',))

            bg_height_first_var = nc_file.createVariable('Background_Low',
                                                         'f8', ('channels',))

            bg_mode_var = nc_file.createVariable('Background_Mode',
                                                 'i4', ('channels',))

            lr_input_var = nc_file.createVariable('LR_Input',
                                                  'i4', ('channels',))

            angle_var = nc_file.createVariable('Laser_Pointing_Angle',
                                               'f8', ('scan_angles',))

            angle_id_var = nc_file.createVariable(
                'Laser_Pointing_Angle_of_Profiles', 'i4', ('time', 'nb_of_time_scales'))

            shots_var = nc_file.createVariable('Laser_Shots',
                                               'i4', ('time', 'channels'))

            mol_calc_var = nc_file.createVariable('Molecular_Calc',
                                                  'i4', ())

            pres_var = nc_file.createVariable('Pressure_at_Lidar_Station',
                                              'f8', ())
            temp_var = nc_file.createVariable('Temperature_at_Lidar_Station',
                                              'f8', ())

            range_res_var = nc_file.createVariable('Raw_Data_Range_Resolution',
                                                   'f8', ('channels',))

            start_var = nc_file.createVariable(
                'Raw_Data_Start_Time', 'i4', ('time', 'nb_of_time_scales'))

            stop_var = nc_file.createVariable(
                'Raw_Data_Stop_Time', 'i4', ('time', 'nb_of_time_scales'))

            data_var = nc_file.createVariable(
                'Raw_Lidar_Data', 'f8', ('time', 'channels', 'points'))

            range_id_var = nc_file.createVariable('ID_Range',
                                                  'i4', ('channels',))

            ch_id_var = nc_file.createVariable('channel_ID',
                                               'i4', ('channels',))

            ch_name_var = nc_file.createVariable('channel_string_ID',
                                                 str, ('channels',))

            time_scale_id_var = nc_file.createVariable('id_timescale',
                                                       'i4', ('channels',))

            calib_range_min_var = nc_file.createVariable('Pol_Calib_Range_Min',
                                                         'f8', ('channels',))
            calib_range_max_var = nc_file.createVariable('Pol_Calib_Range_Max',
                                                         'f8', ('channels',))
            # write data

            angle_var[0] = self.z_axis.header.zenith_angle

            if self.sounding:
                mol_calc_var.assignValue(1)
            else:
                mol_calc_var.assignValue(0)

            pres_var.assignValue(self.header.pressure)
            temp_var.assignValue(self.header.temperature)

            for ch in range(mc.NUM_CAL_CHANNELS):
                range_res_var[ch] = self.z_axis.header.range_res
                bg_height_first_var[ch] = self.signals[mc.CHANNEL_NAMES[mc.CAL_CHANNEL[ch]]].header.bg_first
                bg_height_last_var[ch] = self.signals[mc.CHANNEL_NAMES[mc.CAL_CHANNEL[ch]]].header.bg_last
                time_scale_id_var[ch] = 0
                ch_id_var[ch] = mc.NC_FILL_INT
                ch_name_var[ch] = mc.CAL_CHANNEL_SCC_ID_STR[ch]
                lr_input_var[ch] = 1
                bg_mode_var[ch] = 0
                range_id_var[ch] = self.signals[mc.CHANNEL_NAMES[mc.CAL_CHANNEL[ch]]
                                                ].header.range_id
                calib_range_min_var[ch] = mc.CALIB_RANGE_MIN
                calib_range_max_var[ch] = mc.CALIB_RANGE_MAX

            for t in range(length):
                angle_id_var[t, 0] = 0
                start_var[t, 0] = self.time_axis.secs_of_meas_start[cal_idxs[0]
                                                                    ][t].seconds - self.time_axis.secs_of_meas_start[cal_idxs[0]][0].seconds
                stop_var[t, 0] = self.time_axis.secs_of_meas_stop[cal_idxs[1]
                                                                  ][t].seconds - self.time_axis.secs_of_meas_start[cal_idxs[0]][0].seconds
                for ch in range(mc.NUM_CAL_CHANNELS):
                    t_idx = cal_idxs[mc.CAL_IDX_RANGE[ch]][t]
                    ch_idx = mc.CAL_CHANNEL[ch]
                    shots_var[t, ch] = self.shots.data[t_idx]
                    data_var[t, ch, :] = self.signals[mc.CHANNEL_NAMES[ch_idx]
                                                      ].data[t_idx][:]

            nc_file.close()

    def scc_raw_filename(self):
        datestr = self.time_axis.start[self.mask][0].strftime('%Y%m%d')
        startstr = self.time_axis.start[self.mask][0].strftime('%H%M%S')
        stopstr = self.time_axis.stop[self.mask][-1].strftime('%H%M%S')

        filename = self.header.measurement_id  # + '_'
        filename = '_'.join([filename, startstr])
        filename = '_'.join([filename, stopstr])
        filename = '.'.join([filename, 'nc'])
        return filename

    def scc_depolcal_filename(self, cal_idxs):
        datestr = self.time_axis.start[cal_idxs[0][0]].strftime('%Y%m%d')
        startstr = self.time_axis.start[cal_idxs[0][0]].strftime('%H%M%S')
        stopstr = self.time_axis.stop[cal_idxs[1][-1]].strftime('%H%M%S')

        filename = mc.SCC_RAW_FILENAME_BODY + '_depolcal_'
        filename = '_'.join([filename, datestr])
        filename = '_'.join([filename, startstr])
        filename = '_'.join([filename, stopstr])
        filename = '.'.join([filename, 'nc'])
        return filename


if __name__ == "__main__":
    import doctest
    doctest.testmod()
