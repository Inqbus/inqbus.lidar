import os
import traceback as tb
from datetime import datetime
from math import log

import numpy as np
import pyqtgraph as pg
from scipy.io import netcdf

from inqbus.lidar.scc_gui import util
from inqbus.lidar.scc_gui.axis import HeightAxis, DataAxis
from inqbus.lidar.scc_gui.configs import main_config as mc
from inqbus.lidar.scc_gui.log import logger
import zipfile



class ResultData(object):

    @classmethod
    def from_zip(cls, filepath):
        zfile = zipfile.ZipFile(filepath)
        zfile.extractall(mc.TEMP_PATH)
        file_name = os.path.split(filepath)[-1]
        file_name = file_name.split('.')[0]
        unziped_path = os.path.join(mc.TEMP_PATH, file_name)
        return ResultData.from_directory(unziped_path)

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

        obj.set_lr_type()

        obj.set_angestroem_profile()

        obj.set_zero_line_data()

        obj.set_title()

        obj.replace_masked_values()

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
                plot_min = -.001
                plot_max = .01

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

        if self.plot_depol:
            if self.pldr532_90:
                if (self.pldr532_90 / self.vldr532_90 < 5.0):
                    depol_scale = 1.0
                    self.scale_str = ''
                else:
                    depol_scale = 10.0
                    self.scale_str = '/10'

                self.axis_limits['Depol'] = (
                min(self.axis_limits['ParticleDepol'][0] / depol_scale, self.axis_limits['VolumeDepol'][0]),
                max(self.pldr532_90 / depol_scale, self.axis_limits['VolumeDepol'][1]))
                self.data['vldr532']['mean'] = self.data['b532']['VolumeDepol']['mean']
                self.data['vldr532']['exists'] = True
                self.data['pldr532']['mean'] = {}
                self.data['pldr532']['mean']['data'] = self.data['b532']['ParticleDepol']['mean']['data'] / depol_scale
                self.data['pldr532']['mean']['alt'] = self.data['b532']['ParticleDepol']['mean']['alt']
                self.data['pldr532']['exists'] = True

            if self.pldr355_90:
                if (self.pldr355_90 / self.vldr355_90 < 5.0):
                    depol_scale = 1.0
                    self.scale_str = ''
                else:
                    depol_scale = 10.0
                    self.scale_str = '/10'

                self.axis_limits['Depol'] = (
                min(self.axis_limits['ParticleDepol'][0] / depol_scale, self.axis_limits['VolumeDepol'][0]),
                max(self.pldr355_90 / depol_scale, self.axis_limits['VolumeDepol'][1]))
                self.data['vldr355']['mean'] = self.data['b355']['VolumeDepol']['mean']
                self.data['vldr355']['exists'] = True
                self.data['pldr355']['mean'] = {}
                self.data['pldr355']['mean']['data'] = self.data['b355']['ParticleDepol']['mean']['data'] / depol_scale
                self.data['pldr355']['mean']['alt'] = self.data['b355']['ParticleDepol']['mean']['alt']
                self.data['pldr355']['exists'] = True

            if self.pldr532_90 and self.pldr355_90:
                if (self.pldr532_90 / self.vldr532_90 < 5.0) and (self.pldr355_90 / self.vldr355_90 < 5.0):
                    depol_scale = 1.0
                    self.scale_str = ''
                else:
                    depol_scale = 10.0
                    self.scale_str = '/10'
                self.axis_limits['Depol'] = (
                min(self.axis_limits['ParticleDepol'][0] / depol_scale, self.axis_limits['VolumeDepol'][0]),
                max(self.pldr532_90 / depol_scale, self.pldr355_90 / depol_scale, self.axis_limits['VolumeDepol'][1]))

    def set_lr_type(self):
        for dtype in mc.RES_DTYPES_FOR_LR:
            self.get_lr(dtype)

    def set_angestroem_profile(self):
        if self.data['b532']['exists'] and self.data['b355']['exists']:
            self.get_angstroem_profile(self.data['aeb_uv_vis'], self.data['b532']['Backscatter']['mean'],
                                  self.data['b355']['Backscatter']['mean'], 532., 355.)
        if self.data['b532']['exists'] and self.data['b1064']['exists']:
            self.get_angstroem_profile(self.data['aeb_vis_ir'], self.data['b1064']['Backscatter']['mean'],
                                  self.data['b532']['Backscatter']['mean'], 1064., 532.)
        if self.data['e532']['exists'] and self.data['e355']['exists']:
            self.get_angstroem_profile(self.data['ae_ext'], self.data['e532']['Extinction']['mean'],
                                 self.data['e355']['Extinction']['mean'], 532., 355.)


    def get_lr(self, dtype):
        plot_min = -20.
        plot_max = 120.

        lr_type = dtype.replace('e', 'lr')

        if self.data[dtype]['exists']:
            self.data[lr_type]['data'] = self.data[dtype]['Extinction']['mean']['data'][:] / self.data[dtype]['Backscatter']['mean'][
                                                                                       'data'][:]
            self.data[lr_type]['alt'] = self.data[dtype]['Extinction']['mean']['alt']

            self.data[lr_type]['exists'] = True

            if 'lidar_ratio' in self.axis_limits.keys():
                plot_min = min(self.axis_limits['lidar_ratio'][0], plot_min)
                plot_max = max(self.axis_limits['lidar_ratio'][1], plot_max)

            self.axis_limits['lidar_ratio'] = (plot_min, plot_max)

    def get_angstroem_profile(self, target, source1, source2, wl1, wl2):
        plot_min  = -1.
        plot_max = 3.

        if source1['alt'][0] < source2['alt'][0]:
            f_source = source1 # first profile
            s_source = source2 # secons profile
            f_wl = wl1
            s_wl = wl2
        else:
            f_source = source2 # first profile
            s_source = source1 # secons profile
            f_wl = wl2
            s_wl = wl1

        if s_source['alt'][0] in f_source['alt']:
            idx_shift = int(np.where(f_source['alt'] == s_source['alt'][0])[0])
            max_bin = min( len(f_source['data']) - idx_shift, len(s_source['data']))
            f_profile = f_source['data'][idx_shift : max_bin+idx_shift]
            s_profile = s_source['data'][:max_bin]
            f_alt = f_source['alt'][idx_shift : max_bin +idx_shift]
            s_alt = s_source['alt'][:max_bin]
        else:
            s_profile = np.interp(f_source['alt'], s_source['alt'][~s_source['data'].mask] ,s_source['data'][~s_source['data'].mask], left = np.nan, right = np.nan) #interpolation of bsc2 profile to alt1 axis, missing values = nan
            f_profile = f_source['data']
            f_alt = f_source['alt']
            s_alt = f_alt


        factor = 1/( log(s_wl) - log(f_wl) )

        target['data'] = ( np.log(f_profile) - np.log(s_profile) ) *factor
        target['alt'] = np.ma.max([f_alt, s_alt ], axis = 0)
        target['exists'] = True

        plot_max = np.nanpercentile(target['data'][~target['data'].mask], 95)
        plot_min = np.nanpercentile(target['data'][~target['data'].mask], 5)
        if 'angstroem' in self.axis_limits.keys():
            plot_min = min(self.axis_limits['angstroem'][0], plot_min)
            plot_max = max(self.axis_limits['angstroem'][1], plot_max)

        self.axis_limits['angstroem'] = (plot_min, plot_max)

    def set_zero_line_data(self):
        self.zero_line_data = np.zeros((100))
        self.zero_line_alt = np.array(range(100)) * (self.data['max_alt'] / 99.)

    def set_title(self):
        self.title = self.meas_id + ': ' + self.data['start_time'].strftime('%Y-%m-%d %H:%M:%S - ') + self.data['end_time'].strftime('%H:%M:%S')

    def replace_masked_values(self):
        # important to view all plots and lines. Otherwise some lines behave strange on zooming.
        for dtype in mc.RES_CLEAR_DTYPES:
            if self.data[dtype]['exists']:
                self.data[dtype]['data'] = self.data[dtype]['data'].filled(fill_value=np.NaN)
                self.data[dtype]['alt'] = self.data[dtype]['alt'].filled(fill_value=np.NaN)



class ResultPlot(pg.GraphicsLayoutWidget):

    def setup(self, data):
        self.plots = []
        self.mes_data = data
        self.title = util.get_MDI_Win_title(self.mes_data.title)
        self.set_layout()
        self.define_axis()
        self.setup_plots()
        self.resize(mc.PLOT_WINDOW_SIZE[0]-30, mc.PLOT_WINDOW_SIZE[1]-30)
        self.setBackground('w')
        self.setDataRanges()
        self.setLegends()

    def setDataRanges(self):
        viewbox = self.bsc_plot.vb
        viewbox.enableAutoRange(viewbox.YAxis, False)
        min_heigth = mc.RES_MIN_ALT
        max_heigth = self.mes_data.data['max_alt']
        viewbox.setYRange(
            min_heigth,
            max_heigth)

        plots_limits = {
            self.bsc_plot : 'Backscatter',
            self.ext_plot: 'Extinction',
            self.lidar_plot: 'lidar_ratio',
            self.angstroem_plot: 'angstroem',
            self.depol_plot: 'Depol',
        }

        for plot in plots_limits.keys():
            viewbox = plot.vb
            min, max = self.mes_data.axis_limits[plots_limits[plot]]
            viewbox.enableAutoRange(viewbox.XAxis, False)
            viewbox.setXRange(
                min,
                max
            )

    def set_layout(self):
        self.plot_layout = self.addLayout(
            border=mc.PLOT_BORDER_COLOR,
        )
        self.addItem(self.plot_layout, 0, 0)
        self.plot_layout.layout.setRowStretchFactor(0, 13)

    def define_axis(self):
        # The height axis of the image
        self.height_axis = HeightAxis(orientation='left')
        # select the data to be displayed
        min_heigth = mc.RES_MIN_ALT
        max_heigth = self.mes_data.data['max_alt']

        self.height_axis.setRange(min_heigth, max_heigth)
        # Set Axis above other display elements
        self.height_axis.setZValue(130)

        self.plot_1_axis = DataAxis(orientation='bottom')
        self.plot_1_axis.setLabel(text='BSC.COEF.,\n 1/(Mm sr)')

        self.plot_2_axis = DataAxis(orientation='bottom')
        self.plot_2_axis.setLabel('EXT.COEF.,\n 1/Mm')

        self.plot_3_axis = DataAxis(orientation='bottom')
        self.plot_3_axis.setLabel(text='LIDAR RATIO,\n sr')

        self.plot_4_axis = DataAxis(orientation='bottom')
        self.plot_4_axis.setLabel(text='DEPOL. RATIO, \n %')

        self.plot_5_axis = DataAxis(orientation='bottom')
        self.plot_5_axis.setLabel('ANGSTR. EXP.')

    def setup_plots(self):
        self.setup_bsc_profile()
        self.setup_ext_profile()
        self.setup_lidar_ratio()
        self.setup_depol()
        self.setup_angstroem()

    def setup_bsc_profile(self):
        self.bsc_plot = self.plot_layout.addPlot(
            axisItems={'bottom': self.plot_1_axis, 'left': self.height_axis},
            viewBox=pg.ViewBox()
        )
        self.bsc_plot.plot(
            self.mes_data.zero_line_data, self.mes_data.zero_line_alt, pen='k', clear = True
        )

        for dtype in ['b355', 'b532', 'b1064']:
            if self.mes_data.data[dtype]['exists']:
                profile = self.mes_data.data[dtype]['Backscatter']['mean']
                try:
                    self.bsc_plot.plot(profile['data'][~profile['data'].mask], profile['alt'][~profile['data'].mask],
                                       pen=self.mes_data.data[dtype]['color'], name=dtype, clear=False)
                except ValueError:
                    logger.error('Could not plot %s.' % dtype)
                    logger.error("Traceback: %s" % tb.format_exc())

        for dtype in ['e355', 'e532']:
            if self.mes_data.data[dtype]['exists']:
                profile = self.mes_data.data[dtype]['Backscatter']['mean']
                try:
                    self.bsc_plot.plot(profile['data'][~profile['data'].mask], profile['alt'][~profile['data'].mask],
                                pen=self.mes_data.data[dtype + 'bsc']['color'], name=dtype, clear=False)
                except ValueError:
                    logger.error('Could not plot %s.' % dtype)
                    logger.error("Traceback: %s" % tb.format_exc())
        self.plots.append(self.bsc_plot)


    def setup_ext_profile(self):
        self.ext_plot = self.plot_layout.addPlot(
            axisItems={'bottom': self.plot_2_axis, 'left': self.height_axis},
            viewBox=pg.ViewBox()
        )
        self.ext_plot.hideAxis('left')


        self.ext_plot.plot(
            self.mes_data.zero_line_data, self.mes_data.zero_line_alt, pen='k', clear = True
        )

        for dtype in ['e355', 'e532']:
            if self.mes_data.data[dtype]['exists']:
                profile = self.mes_data.data[dtype]['Extinction']['mean']
                try:
                    self.ext_plot.plot(profile['data'], profile['alt'], pen=self.mes_data.data[dtype]['color'], name=dtype, clear=False)
                except ValueError:
                    logger.error('Could not plot %s.' % dtype)
                    logger.error("Traceback: %s" % tb.format_exc())

        self.ext_plot.setYLink(self.bsc_plot)
        self.plots.append(self.ext_plot)

    def setup_lidar_ratio(self):
        self.lidar_plot = self.plot_layout.addPlot(
            axisItems={'bottom': self.plot_3_axis, 'left': self.height_axis},
            viewBox=pg.ViewBox()
        )
        self.lidar_plot.hideAxis('left')

        self.lidar_plot.plot(self.mes_data.zero_line_data + 100., self.mes_data.zero_line_alt, pen=0.75)
        for dtype in ['lr355', 'lr532']:
            if self.mes_data.data[dtype]['exists']:
                self.lidar_plot.plot(self.mes_data.data[dtype]['data'], self.mes_data.data[dtype]['alt'], pen=self.mes_data.data[dtype]['color'], name=dtype)
                
        self.lidar_plot.setYLink(self.bsc_plot)
        self.plots.append(self.lidar_plot)
    
    def setup_depol(self):
        self.depol_plot = self.plot_layout.addPlot(
            axisItems={'bottom': self.plot_4_axis, 'left': self.height_axis},
            viewBox=pg.ViewBox()
        )
        self.depol_plot.hideAxis('left')

        if self.mes_data.data['vldr532']['exists']:
            self.depol_plot.plot(self.mes_data.data['vldr532']['mean']['data'], self.mes_data.data['vldr532']['mean']['alt'],
                         pen=self.mes_data.data['vldr532']['color'], name='vldr532')
        if self.mes_data.data['pldr532']['exists']:
            self.depol_plot.plot(self.mes_data.data['pldr532']['mean']['data'], self.mes_data.data['pldr532']['mean']['alt'],
                         pen=self.mes_data.data['pldr532']['color'], name='pldr532' + self.mes_data.scale_str)

        self.depol_plot.setYLink(self.bsc_plot)
        self.plots.append(self.depol_plot)
    
    def setup_angstroem(self):
        self.angstroem_plot = self.plot_layout.addPlot(
            axisItems={'bottom': self.plot_5_axis, 'left': self.height_axis},
            viewBox=pg.ViewBox()
        )
        self.angstroem_plot.hideAxis('left')

        self.angstroem_plot.plot(self.mes_data.zero_line_data, self.mes_data.zero_line_alt, pen='k')
        self.angstroem_plot.plot(self.mes_data.zero_line_data - 1., self.mes_data.zero_line_alt, pen=0.75)
        self.angstroem_plot.plot(self.mes_data.zero_line_data + 3., self.mes_data.zero_line_alt, pen=0.75)
        for dtype in ['aeb_uv_vis', 'aeb_vis_ir', 'ae_ext']:
            if self.mes_data.data[dtype]['exists']:
                self.angstroem_plot.plot(self.mes_data.data[dtype]['data'], self.mes_data.data[dtype]['alt'], pen=self.mes_data.data[dtype]['color'], name=dtype)

        self.angstroem_plot.setYLink(self.bsc_plot)
        self.plots.append(self.angstroem_plot)

    def setLegends(self):
        # TODO: Improve legend style and position
        for plot in self.plots:
            legend = pg.LegendItem()
            legend.setParentItem(plot)
            for item in plot.items:
                if item.name():
                    legend.addItem(item, item.name())

            plot.addLegend()