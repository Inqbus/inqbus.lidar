import copy
import functools
import os
import sys
import traceback as tb
import zipfile
from datetime import datetime, timedelta
from math import log
from collections import OrderedDict

import numpy as np
import pyqtgraph as pg
from PyQt5 import uic
from PyQt5.QtWidgets import QAction, QMenu, QWidgetAction
from inqbus.lidar.components.constants import NC_FILL_BYTE, CIRRUS, NO_CLOUD
from pyqtgraph.graphicsItems.LegendItem import ItemSample
from qtpy import QtGui
from pyqtgraph.Qt import QtCore
from scipy.io import netcdf
from netCDF4 import Dataset

from inqbus.lidar.scc_gui import util, PROJECT_PATH
from inqbus.lidar.scc_gui.axis import HeightAxis, DataAxis
from inqbus.lidar.scc_gui.configs import main_config as mc
from inqbus.lidar.scc_gui.configs.base_config import resource_path
from inqbus.lidar.scc_gui.log import logger
#from inqbus.lidar.scc_gui.app import app


class DataExport(object):

    def __init__(self, data):
        self.data = data
        self.export_dir = os.path.join(mc.RESULT_EXPORT_PATH, self.data.meas_id)
        self.overwrite_all = False
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

        self.export_all()

    def export_all(self):
        if self.data.data['version'] == 'nc4-cf':
#            self.export_mwl()
            for dtype in mc.RES_VAR_NAMES.keys():
                self.export_dtype_cf(dtype)
        else:
            for dtype in mc.RES_VAR_NAMES.keys():
                self.export_dtype(dtype)

    def export_general_cf(self, file, dtype):
        self.write_header_cf(file, dtype)
        #file.flush()
        logger.info("Finished Header ")

        self.write_global_variables_cf(file)
        #file.flush()
        logger.info("Finished writing global variables ")

    def export_mwl(self):
        filename = self.data.station_id + self.data.data['start_time'].strftime('%y%m%d%H%M') + '.mwl.nc'
        logger.info("export mwl file %s" %filename)

        file = self.create_file_cf(filename)
        self.export_general_cf(file)
        file.close()

    def export_dtype_cf(self, dtype):
        if self.data.data[dtype]['exists']:
            has_data = False
            for var in mc.RES_VAR_NAMES_CF[dtype]:
                var_dtype = mc.RES_VAR_NAMES_CF[dtype][var]
                if 'mean' in self.data.data[var_dtype]:
                    if not np.all(np.isnan(self.data.data[var_dtype]['mean']['data'])):
                        has_data = True

            if not has_data:
                return
            filename = self.data.data[dtype]['mean']['file_name'].split('_')[1]
        else:
            return

        file = self.create_file_cf(filename)

        self.write_data_variables_cf(file, dtype)

        for var in mc.RES_VAR_NAMES_CF[dtype]:
            var_data = self.data.data[mc.RES_VAR_NAMES_CF[dtype][var]]
            if var_data['exists']:
                if not np.all(np.isnan(var_data['mean']['data'])):
                    self.write_variables_cf(file, var_data['anc_vars'])

        self.export_general_cf(file, dtype)

        file.close()

    def export_dtype(self, dtype):
        if self.data.data[dtype]['exists']:
#            filename = self.data.meas_id + '.' + dtype
            filename = self.data.station_id + self.data.data['start_time'].strftime('%y%m%d%H%M') + '.' + dtype
        else:
            return

        file = self.create_file(filename)
        self.write_header(file, dtype)
        logger.info("Finished Header %s" % dtype)
        file.flush()
        self.write_data_variables(file, dtype)
        file.flush()
        logger.info("Finished data %s" % dtype)
        file.close()

    def create_file_cf(self, filename):
        full_filename = os.path.join(self.export_dir, filename)

        outfile = Dataset(full_filename, 'w', format="NETCDF4")
        return outfile

    def create_file(self, filename):
        full_filename = os.path.join(self.export_dir, filename)
        #if os.path.exists(full_filename) and ~self.overwrite_all:
            #QtGui.QMessageBox.about(app.main_window, "The file already exists.", "Do you want to overwrite?")
            #                msgBox.setText("The file already exists.");
            #                msgBox.setInformativeText("Do you want to overwrite?");
            #                msgBox.setStandardButtons(QMessageBox::Overwrite | QMessageBox::Discard | QMessageBox::Cancel);
            #                msgBox.setDefaultButton(QMessageBox::Cancel);
            #                ret = msgBox.exec();

        outfile = netcdf.netcdf_file(full_filename, 'w', False, 1)
        return outfile

#    def create_dimensions_cf(self, file):
#        self.alt_dim = file.createDimension('altitude', points)
#        self.time_dim = file.createDimension('time', 1)
#        self.wl_dim = file.createDimension('wavelength', 1)
#        self.nv_dim = file.createDimension('nv', 2)

    def write_header_cf(self, file, dtype):
        data = self.data.data
        for attr in data['global_attributes']:
            attr_value = data['global_attributes'][attr]
            if isinstance(attr_value, OrderedDict):
                continue
            file.setncattr(attr, data['global_attributes'][attr])
#            file.flush()

        for attr in data[dtype]['attrs']:
            attr_value = data[dtype]['attrs'][attr]
            if isinstance(attr_value, OrderedDict):
                continue
            file.setncattr(attr, data[dtype]['attrs'][attr])


        file.comment = data['Comments']
        file.measurement_start_datetime = data['start_time'].strftime('%Y-%m-%dT%H:%M:%SZ')
        file.measurement_stop_datetime = data['end_time'].strftime('%Y-%m-%dT%H:%M:%SZ')


    def write_header(self, file, dtype):
        data = self.data.data
        for attr in data[dtype]['attributes']:
            attr_value = data[dtype]['attributes'][attr]
            if isinstance(attr_value, OrderedDict):
                continue
            setattr(file, attr, data[dtype]['attributes'][attr])
            file.flush()

        file.Comments = data['Comments']
        file.StartDate = int(data['start_time'].strftime(
            '%Y%m%d'))
        file.StartTime_UT = int(data['start_time'].strftime(
            '%H%M%S'))
        file.StopTime_UT = int(data['end_time'].strftime(
            '%H%M%S'))

    def write_global_variables_cf(self, nc_file):
        self.write_variables_cf(nc_file, self.data.data['global_vars'])

    def write_variables_cf(self, nc_file, vars):
        for v in vars:
            if not v in nc_file.variables:
                orig_v = vars[v]

                #create variable
                if '_FillValue' in orig_v['attrs']:
                    var = nc_file.createVariable(v, orig_v['dtype'], orig_v['dims'], fill_value=orig_v['attrs']['_FillValue'])
                else:
                    var = nc_file.createVariable(v, orig_v['dtype'], orig_v['dims'])

                #create variable attributes
                for v_att in orig_v['attrs']:
                    if v_att != '_FillValue':
                        setattr(var, v_att, orig_v['attrs'][v_att])

                #set variable value
                var[:] = orig_v['values'][:]

    def write_data_variables(self, file, dtype):
        export_data = {}
        points = 0

        for col in mc.RES_VAR_NAMES[dtype]:
            if not (col in mc.RES_VAR_NAME_ALIAS):
                data = self.data.data[ mc.RES_VAR_NAMES[dtype][col] ]
                if data['exists']:
                    if 'mean' in data:
                        export_data[col] = data['mean']['data']

                        export_data['Error'+col] = data['mean']['error']

                        if not ('Altitude' in export_data):
                            export_data['Altitude'] = data['mean']['alt'] + self.data.data['station_altitude']
                        else:
                            if not np.array_equal( export_data['Altitude'], (data['mean']['alt'] + self.data.data['station_altitude']) ):
                                logger.info('altitude axes for export are different in %s' % (dtype))

                        if not ('VerticalResolution' in export_data):
                            export_data['VerticalResolution'] = data['mean']['vert_res']
                        else:
                            if not np.array_equal(export_data['VerticalResolution'], data['mean']['vert_res']):
                                logger.info('vertical resolution profiles for export are different in %s' % (dtype))

                        if 'cloud' in data['mean']:
                            if not ('__CloudFlag' in export_data):
                                export_data['__CloudFlag'] = data['mean']['cloud']
                            else:
                                if not np.array_equal(export_data['__CloudFlag'], data['mean']['cloud']):
                                    logger.info('cloud profiles for export are different in %s' % (dtype))

                        points = max(points, export_data[col].size)

                    else:
                        logger.info('No mean found for col %s in dtype %s' % (col, dtype))
                else:
                    logger.info('No %s data found for %s' % (col, dtype))

        col_dim = file.createDimension('Length', None) # Length is unlimited dimension, initialized with size = None

        for col in export_data.keys():
            data = export_data[col]

            if not np.all(np.isnan(data)):
                var = file.createVariable(col, data.dtype.type, ('Length',))

                #create variable attributes
                for v_att in mc.VARIABLE_ATTRIBUTES[col]['attrs']:
                    if v_att != '_FillValue':
                        setattr(var, v_att, mc.VARIABLE_ATTRIBUTES[col]['attrs'][v_att])

                var[:] = data


    def write_data_variables_cf(self, file, dtype):
        export_data = {}
        points = 0
        fill_value_float = None

        for col in mc.RES_VAR_NAMES_CF[dtype]:
#            if not (col in mc.RES_VAR_NAME_ALIAS):
            data = self.data.data[mc.RES_VAR_NAMES_CF[dtype][col]]

            if data['exists']:
                if 'mean' in data:
                    export_data[col] = data['mean']['data']
                    fill_value_float = data['mean']['fill_value']

                    export_data['error_' + col] = data['mean']['error']

                    if not ('altitude' in export_data):
                        export_data['altitude'] = data['mean']['alt'] + self.data.data['station_altitude']

                    else:
                        if not np.array_equal(export_data['altitude'],
                                              (data['mean']['alt'] + self.data.data['station_altitude'])):
                            logger.info('altitude axes for export are different in %s' % (dtype))

                    if not ('vertical_resolution' in export_data):
                        export_data['vertical_resolution'] = data['mean']['vert_res']
                    else:
                        if not np.array_equal(export_data['vertical_resolution'], data['mean']['vert_res']):
                            logger.info('vertical resolution profiles for export are different in %s' % (dtype))

                    if not data['mean']['lr'] is None:
                        if not ('assumed_particle_lidar_ratio' in export_data):
                            export_data['assumed_particle_lidar_ratio'] = data['mean']['lr']
                        else:
                            if not np.array_equal(export_data['assumed_particle_lidar_ratio'], data['mean']['lr']):
                                logger.info('lr profiles for export are different in %s' % (dtype))

                    if 'cloud' in data['mean']:
                        if not ('cloud_mask' in export_data):
                            export_data['cloud_mask'] = data['mean']['cloud']
                        else:
                            if not np.array_equal(export_data['cloud_mask'], data['mean']['cloud']):
                                logger.info('cloud profiles for export are different in %s' % (dtype))

                    points = max(points, export_data[col].size)

                else:
                    logger.info('No mean found for col %s in dtype %s' % (col, dtype))
            else:
                logger.info('No %s data found for %s' % (col, dtype))

        alt_dim = file.createDimension('altitude', points)
        time_dim = file.createDimension('time', 1)
        wl_dim = file.createDimension('wavelength', 1)
        nv_dim = file.createDimension('nv', 2)

        for col in export_data.keys():
            data = export_data[col]

            if not np.all(np.isnan(data)):
                if '_FillValue' in mc.VARIABLE_ATTRIBUTES[col]['attrs']:
                    fill_value = mc.VARIABLE_ATTRIBUTES[col]['attrs']['_FillValue']
                    if fill_value is None:
                        fill_value = fill_value_float
                else:
                    fill_value = None

                if fill_value is None:
                    var = file.createVariable(col, data.dtype.type, mc.VARIABLE_ATTRIBUTES[col]['dims'])
                else:
                    var = file.createVariable(col, data.dtype.type, mc.VARIABLE_ATTRIBUTES[col]['dims'],
                                          fill_value=fill_value)

                # create variable attributes
                for v_att in mc.VARIABLE_ATTRIBUTES[col]['attrs']:
                    if v_att != '_FillValue':
                        setattr(var, v_att, mc.VARIABLE_ATTRIBUTES[col]['attrs'][v_att])

                var[:] = data


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
        obj.data = copy.deepcopy(mc.RES_DATA_SETTINGS)
        obj.axis_limits = {}
        obj.axis_limits.update(mc.RES_AXES_LIMITS)
        meas_id = os.path.split(filepath)[-1]
        obj.meas_id = meas_id
        if len(meas_id) == 12:
            obj.station_id = meas_id[8:10]
        elif len(meas_id) == 15:
            obj.station_id = meas_id[8:11]
        else:
            raise Exception('unknown format of measurement id')

        obj.filepath = filepath

        for filename in os.listdir(filepath):
            obj.read_nc_file(os.path.join(filepath, filename))

        obj.get_mean_profile()

        obj.set_depol()

        obj.set_lr_type()

        obj.set_angestroem_profile()

        obj.set_axes_limits()

        obj.set_zero_line_data()

        obj.set_title()

        obj.set_original_data()

        return obj

    def time_from_nc(self, nc_timestamp):
        return datetime(1970,1,1) + timedelta(seconds=int(nc_timestamp))


    def get_attributes(self, parent, exclude):
        attributes = OrderedDict()
        for att in parent.ncattrs():
            if not att in exclude:
                attributes[att] = parent.getncattr(att)
        return copy.deepcopy(attributes)

    def read_nc4_var(self, file, varname):
        if file.variables[varname].size == 1:
            vdata = np.array([file.variables[varname][0]])
        else:
            vdata = file.variables[varname][:]

        return {'attrs': self.get_attributes(file.variables[varname], {}),
                 'values': vdata,
                 'dtype': file.variables[varname].dtype,
                 'dims': file.variables[varname].dimensions,
                 }

    def read_nc4_file_complete(self, f):
        self.data['version'] = 'nc4-cf'

        if not 'global_vars' in self.data:
            self.data['global_vars']= {}
            for gvar in mc.GLOBAL_VARS_CF:
                if gvar in f.variables:
                    if gvar == 'molecular_calculation_source':
                        var = self.read_nc4_var(f, gvar)
                        if var['values'][0] == 6:
                            var['values'][0] = 4
                        self.data['global_vars']['atmospheric_molecular_calculation_source'] = var
                    else:
                        self.data['global_vars'][gvar] = self.read_nc4_var(f, gvar)

        if not 'global_attributes' in self.data:
            self.data['global_attributes'] = self.get_attributes(f, mc.PRODUCT_SPECIFIC_GLOBAL_ATTS)
            self.data['global_attributes']['PI_affiliation'] = 'DWD'
            self.data['global_attributes']['Data_Originator_affiliation'] = 'DWD'
            self.data['global_attributes']['Data_Originator_email'] = 'ina.mattis@dwd.de'
            if self.data['global_attributes']['Data_Originator'] == 'ina':
                self.data['global_attributes']['Data_Originator'] = 'Ina Mattis'
                self.data['global_attributes']['Data_Originator_email'] = 'ina.mattis@dwd.de'

        file_start = self.time_from_nc(f.variables['time_bounds'][0, 0])
        file_end = self.time_from_nc(f.variables['time_bounds'][0, 1])
        self.data['start_time'] = min(self.data['start_time'], file_start)
        self.data['end_time'] = max(self.data['end_time'], file_end)
        self.data['Comments'] = f.comment#.decode("utf-8")
        self.data['station_altitude'] = f.variables['station_altitude'][0]

        alt = f.variables['altitude'][:].filled(np.nan)
        alt[np.where (alt > 1E30)[0]] = np.nan
        alt = alt - f.variables['station_altitude'][0]

        self.data['max_alt'] = max(self.data['max_alt'], max(alt))

        if f.scc_version > "5.0.0":
            cloud_data = f.variables['cloud_mask'][0,:].filled(NC_FILL_BYTE)
        else:
            cloud_data = f.variables['cloud_mask'][0,0,:].filled(NC_FILL_BYTE)

        cloud_data[np.where(cloud_data > 5)[0]] = NC_FILL_BYTE
        cloud_data[np.where(cloud_data > 0)[0]] = CIRRUS # this tool can plot only 1 type of clouds (cirrus = 2). Thus, all flagged cloud bins are set to cirrus

        res_data = f.variables['vertical_resolution'][0,0,:].filled(np.nan)

        if 'assumed_particle_lidar_ratio' in f.variables:
            lr_data = f.variables['assumed_particle_lidar_ratio'][0,0,:].filled(np.nan)
        else:
            lr_data = None

        ftype = f.filepath().split('.')[1]

        for v in mc.RES_VAR_NAMES_CF[ftype]:
            if v in f.variables.keys() :
                dtype = mc.RES_VAR_NAMES_CF[ftype][v]

                if not self.data[dtype]['exists']:

                    # read product specific global attributes
                    self.data[dtype]['attrs'] = {}
                    for att in mc.PRODUCT_SPECIFIC_GLOBAL_ATTS:
                        self.data[dtype]['attrs'][att] = f.getncattr(att)

                    # read ancillary data
                    self.data[dtype]['anc_vars'] = {}
                    for anc_var in f.variables.keys():
                        if (not anc_var in mc.GLOBAL_VARS_CF)  and \
                                (not anc_var in mc.VARIABLE_ATTRIBUTES): # if it is not a global variable

                            # does it belong to another dataype ?
                            belongs_to_other_dtype = False
                            for dt in mc.RES_VAR_NAMES_CF[ftype]:
                                if (dt in anc_var) and (dt != v):
                                    belongs_to_other_dtype = True

                            if not belongs_to_other_dtype:
                                self.data[dtype]['anc_vars'][anc_var] = self.read_nc4_var(f, anc_var)

                    self.data[dtype]['single'] = []
                if not ('single' in self.data[dtype].keys()):
                    pass

                vdata = f.variables[v][0, 0, :].filled(np.nan)

                error_var_name = 'error_' + v
                edata = f.variables[error_var_name][0, 0, :].filled(np.nan)

                self.data[dtype]['single'].append({'alt': alt,
                                                   'data': vdata,
                                                   'error': edata,
                                                   'cloud': cloud_data,
                                                   'vert_res': res_data,
                                                   'lr': lr_data,
                                                   'fill_value': f.variables[v].getncattr('_FillValue'),
                                                   'file_name': os.path.split(f.filepath())[1]}
                                                  )
                self.data[dtype]['exists'] = True

        f.close()

    # def read_nc4_file(self, f):
    #     self.data['version'] = 'nc4'
    #     file_start = self.time_from_nc(f.variables['time_bounds'][0, 0])
    #     file_end = self.time_from_nc(f.variables['time_bounds'][0, 1])
    #     self.data['start_time'] = min(self.data['start_time'], file_start)
    #     self.data['end_time'] = max(self.data['end_time'], file_end)
    #     self.data['comment'] = f.comments#.decode("utf-8")
    #     self.data['Altitude_meter_asl'] = f.variables['station_altitude'][0]
    #
    #     alt = f.variables['altitude'][:]
    #     alt[np.where(alt > 1E30)[0]] = np.nan
    #     alt = alt - f.variables['station_altitude'][0]
    #
    #     self.data['max_alt'] = max(self.data['max_alt'], max(alt))
    #
    #     cloud_data = np.ma.masked_array(f.variables['cloud_mask'][0,0,:])
    #     cloud_data.mask = (cloud_data > 5)
    #     cloud_data[np.where(cloud_data > 0)[0]] = 2 # this tool can plot only 1 type of clouds (cirrus = 2). Thus, all flagged cloud bins are set to cirrus
    #
    #     res_data = f.variables['vertical_resolution'][0,0,:]
    #
    #     global_attributes = OrderedDict()
    #     for att in f.ncattrs():
    #         global_attributes[att] = f.getncattr(att)
    #
    #     ftype = f.filepath().split('.')[1]
    #
    #     #for v in f.variables.keys():
    #     #    dtype = mc.RES_VAR_NAMES_CF[ftype][v]
    #     #    if v in mc.RES_VAR_NAMES_CF[ftype]:
    #
    #     for v in mc.RES_VAR_NAMES_CF[ftype]:
    #         if v in f.variables.keys():
    #
    #             if v in mc.RES_VAR_NAME_ALIAS.keys():
    #                 va = mc.RES_VAR_NAME_ALIAS[v]
    #             else:
    #                 va = v
    #
    #             dtype = mc.RES_VAR_NAMES_CF[ftype][v]
    #
    #             if not ('single' in self.data[dtype].keys()):
    #                 self.data[dtype]['single'] = []
    #
    #             vdata = f.variables[v][0,0,:]
    #             vdata[np.where(vdata > 1E30)[0]] = np.nan
    #
    #             error_var_name = 'error_' + v
    #             edata = f.variables[error_var_name][0,0,:]
    #             edata[np.where(edata > 1E30)[0]] = np.nan
    #
    #             self.data[dtype]['single'].append({'alt': alt,
    #                                                'data': vdata ,
    #                                                'error': edata ,
    #                                                'cloud': cloud_data,
    #                                                'vert_res': res_data})
    #             self.data[dtype]['exists'] = True
    #
    #             # copy global (file) attributes
    #             self.data[dtype]['attributes'] = copy.deepcopy(global_attributes)
    #
    #     f.close()

    def read_nc3_file(self, f):
        self.data['version'] = 'nc3'
        file_start = datetime.strptime(str(f.StartDate) + str(f.StartTime_UT).zfill(6), '%Y%m%d%H%M%S')
        file_end = datetime.strptime(str(f.StartDate) + str(f.StopTime_UT).zfill(6), '%Y%m%d%H%M%S')
        self.data['start_time'] = min(self.data['start_time'], file_start)
        self.data['end_time'] = max(self.data['end_time'], file_end)
        self.data['Comments'] = f.Comments.decode("utf-8")
        self.data['station_altitude'] = f.Altitude_meter_asl

        alt = f.variables['Altitude'].data[:]
        alt[np.where(alt > 1E30)[0]] = np.nan
        alt = alt - f.Altitude_meter_asl

        cloud_data = f.variables['__CloudFlag'].data

        res_data = f.variables['VerticalResolution'].data

        self.data['max_alt'] = max(self.data['max_alt'], max(alt))

        global_attributes = f._attributes
        ftype = f.filename.split('.')[-1] # file type

        for v in mc.RES_VAR_NAMES[ftype].keys():
            if v in f.variables.keys():
                if v in mc.RES_VAR_NAME_ALIAS.keys():
                    va = mc.RES_VAR_NAME_ALIAS[v]
                else:
                    va = v

                dtype = mc.RES_VAR_NAMES[ftype][v]

                if not ('single' in self.data[dtype].keys()):
                    self.data[dtype]['single'] = []

                vdata = f.variables[v].data[:]
                vdata[np.where(vdata > 1E30)[0]] = np.nan

                error_var_name = 'Error' + v
                edata = f.variables[error_var_name].data[:]
                edata[np.where(edata > 1E30)[0]] = np.nan

                self.data[dtype]['single'].append({'alt': alt,
                                                   'data': vdata ,
                                                   'error': edata ,
                                                   'cloud': cloud_data,
                                                   'vert_res': res_data})
                self.data[dtype]['exists'] = True

                # copy global (file) attributes
                self.data[dtype]['attributes'] = global_attributes.copy()

        f.close()

    def read_nc_file(self, file_name):
        nc_version = 0
        try:
            f = netcdf.netcdf_file(file_name, 'r', False, 1)
            nc_version = 3
        except TypeError:
            try:
                f = Dataset(file_name, 'r', format="NETCDF4")
                nc_version = 4
            except:
                logger.error('%s is no valid file.' % file_name)
                return
        except IsADirectoryError:
            logger.error('%s is no valid file.' % file_name)
            return

        if nc_version == 3:
            self.read_nc3_file(f)

        if nc_version == 4:
            #self.read_nc4_file(f)
            self.read_nc4_file_complete(f)

    def calc_mean_data(self, single_profiles):
        min_start = 15000
        min_start_idx = np.nan
        max_len = 0
        if 'file_name' in single_profiles[0]:
            file_name = single_profiles[0]['file_name']
        else:
            file_name = None

        for p in range(len(single_profiles)):
            while np.isnan(single_profiles[p]['alt'][0]):
                single_profiles[p]['alt'] = np.delete(single_profiles[p]['alt'], 0)
                single_profiles[p]['data'] = np.delete(single_profiles[p]['data'], 0)
                single_profiles[p]['error'] = np.delete(single_profiles[p]['error'], 0)
                single_profiles[p]['cloud'] = np.delete(single_profiles[p]['cloud'], 0)
                single_profiles[p]['vert_res'] = np.delete(single_profiles[p]['vert_res'], 0)
                if not (single_profiles[p]['lr'] is None):
                    single_profiles[p]['lr'] = np.delete(single_profiles[p]['lr'], 0)

            if single_profiles[p]['alt'][0] < min_start:
                min_start = single_profiles[p]['alt'][0]
                min_start_idx = p
            max_len = max(max_len, len(single_profiles[p]['alt']))

        data_arr = []
        err_arr = []
        weight_arr = []
        alt_arr = []
        cloud_arr = []
        vert_res_arr = []
        lr_arr = []

        for p in range(len(single_profiles)):

            # insert nans in the beginning of profile until beginning of its altitude axis fits to the one of max_start_idx
            idx_shift = int(
                np.where(single_profiles[min_start_idx]['alt'] == single_profiles[p]['alt'][0])[0])
            fill_array = np.ones(idx_shift) * np.nan
            fill_array_c = np.ones(idx_shift, dtype=np.int8) * NC_FILL_BYTE

            d = np.append(fill_array, single_profiles[p]['data'])
            e = np.append(fill_array, single_profiles[p]['error'])
            w = np.abs(d / e)  # weight = 1/relative error = value/error
            a = np.append(fill_array, single_profiles[p]['alt'])
            v = np.append(fill_array, single_profiles[p]['vert_res'])
            c = np.append(fill_array_c, single_profiles[p]['cloud'])
            if 'lr' in single_profiles[p]:
                if single_profiles[p]['lr'] is not None:
                    l = np.append(fill_array, single_profiles[p]['lr'])
                else:
                    l = None
            else:
                l = None

            fill_length = max_len - len(d)  # len(single_profiles[p]['data'])
            if fill_length < 0:
                dd = d[:fill_length]
                ee = e[:fill_length]
                ww = w[:fill_length]
                aa = a[:fill_length]
                cc = c[:fill_length]
                vv = v[:fill_length]
                if l is not None:
                    ll = l[:fill_length]
                else:
                    ll = None
            else:
                fill_array = np.ones(fill_length) * np.nan
                fill_array_c = np.ones(fill_length, dtype=np.int8) * NC_FILL_BYTE

                dd = np.append(d, fill_array)  # fill the end of profile with nans until its length is equal max_len
                ee = np.append(e, fill_array)
                ww = np.append(w, fill_array)
                aa = np.append(a, fill_array)
                cc = np.append(c, fill_array_c)
                vv = np.append(v, fill_array)
                if l is not None:
                    ll = np.append(l, fill_array)
                else:
                    ll = None

            data_arr.append(dd)
            err_arr.append(ee)
            weight_arr.append(ww)
            alt_arr.append(aa)
            cloud_arr.append(cc)
            vert_res_arr.append(vv)
            if ll is not None:
                lr_arr.append(ll)

            if not file_name is None:
                file_name = min(file_name, single_profiles[p]['file_name'])

        cloud_mask = np.array(cloud_arr)
        cloud_mask[:, np.where(cloud_mask == NC_FILL_BYTE)[1]] = NC_FILL_BYTE
        cloud_mask = np.max(cloud_mask, axis=0)
        if len(lr_arr) == len(weight_arr):
            lr = np.average(lr_arr, weights=weight_arr, axis=0)
        else:
            lr = None

        return {'data': np.average(data_arr, weights=weight_arr, axis=0),
                'error': np.average(err_arr, weights=weight_arr, axis=0),
                'alt': np.max(alt_arr, axis=0),
                'cloud': cloud_mask,
                'vert_res': np.max(vert_res_arr, axis=0),
                'lr': lr,
                'fill_value': single_profiles[0]['fill_value'],
                'file_name': file_name
                }

    def get_mean_profile(self):
        for dtype in mc.RES_DTYPES_FOR_MEAN_PROFILE:
            if self.data[dtype]['exists']:
                single_profiles = self.data[dtype]['single']
                if len(single_profiles) == 1:
                    self.data[dtype]['mean'] = {'alt': single_profiles[0]['alt'],
                                                'data': single_profiles[0]['data'],
                                                'error': single_profiles[0]['error'],
                                                'cloud': single_profiles[0]['cloud'],
                                                'vert_res': single_profiles[0]['vert_res'],
                                                'lr': single_profiles[0]['lr'],
                                                'fill_value':single_profiles[0]['fill_value'],
                                                'file_name': single_profiles[0]['file_name']
                                                }
                else:
                    self.data[dtype]['mean'] = self.calc_mean_data(single_profiles)
                    self.data[dtype]['scale_str'] = ''

    def set_depol(self):
        self.plot_depol = False
        if self.data['pldr532']['exists'] and self.data['vldr532']['exists']:
            self.pldr532_90 = np.nanpercentile(self.data['pldr532']['mean']['data'], 90)
            self.vldr532_90 = np.nanpercentile(self.data['vldr532']['mean']['data'], 90)
            self.plot_depol = True
        else:
            self.pldr532_90 = None
            self.vldr532_90 = None

        if self.data['pldr355']['exists'] and self.data['vldr355']['exists']:
            self.pldr355_90 = np.nanpercentile(self.data['pldr355']['mean']['data'], 90)
            self.vldr355_90 = np.nanpercentile(self.data['vldr355']['mean']['data'], 90)
            self.plot_depol = True
        else:
            self.pldr355_90 = None
            self.vldr355_90 = None

        if self.plot_depol:
            if self.pldr532_90:
                if (self.pldr532_90 / self.vldr532_90 > 5.0):
                    self.data['pldr532']['scale_factor'] = 10.0
                    self.data['pldr532']['scale_str'] = '/10'

            if self.pldr355_90:
                if (self.pldr355_90 / self.vldr355_90 > 5.0):
                    self.data['pldr355']['scale_factor'] = 10.0
                    self.data['pldr355']['scale_str'] = '/10'

            if self.pldr532_90 and self.pldr355_90:
                if (self.pldr532_90 / self.vldr532_90 > 5.0) or (self.pldr355_90 / self.vldr355_90 > 5.0):
                    self.data['pldr532']['scale_factor'] = 10.0
                    self.data['pldr355']['scale_factor'] = 10.0
                    self.data['pldr532']['scale_str'] = '/10'
                    self.data['pldr355']['scale_str'] = '/10'

    def set_lr_type(self):
        for dtype in mc.LIDAR_RATIO_CALCULATIONS:
            self.get_lr(dtype)

    def set_angestroem_profile(self):
        for ae_type in mc.ANGSTROEM_CALCULATIONS:
            type_1 = mc.ANGSTROEM_CALCULATIONS[ae_type]['profile_1']
            type_2 = mc.ANGSTROEM_CALCULATIONS[ae_type]['profile_2']

            if self.data[type_1]['exists'] and self.data[type_2]['exists']:
                self.get_angstroem_profile(self.data[ae_type],
                                           self.data[type_1]['mean'], self.data[type_2]['mean'],
                                           mc.ANGSTROEM_CALCULATIONS[ae_type]['wl_1'],
                                           mc.ANGSTROEM_CALCULATIONS[ae_type]['wl_2'])

    def get_lr(self, lr_type):
        bsc_type = mc.LIDAR_RATIO_CALCULATIONS[lr_type]['bsc']
        ext_type = mc.LIDAR_RATIO_CALCULATIONS[lr_type]['ext']

        if self.data[bsc_type]['exists'] and self.data[ext_type]['exists']:
            bsc_data = self.data[bsc_type]['mean']['data']
            bsc_err = self.data[bsc_type]['mean']['error']
            ext_data = self.data[ext_type]['mean']['data']
            ext_err = self.data[ext_type]['mean']['error']

            data = ext_data[:] / bsc_data[:]
            error = data[:] * np.sqrt(np.square(ext_err[:] / ext_data[:]) + \
                                      np.square(bsc_err[:] / bsc_data[:]))

            self.data[lr_type]['mean'] = {'data': data,
                                          'error': error,
                                          'cloud': self.data[ext_type]['mean']['cloud'],
                                          'alt': self.data[ext_type]['mean']['alt'],
                                          'vert_res': self.data[ext_type]['mean']['vert_res'],
                                          'fill_value': self.data[ext_type]['mean']['fill_value']}

            self.data[lr_type]['exists'] = True

    def get_angstroem_profile(self, target, source1, source2, wl1, wl2):

#        logger.info('calculate Angström profile from %s and %s' % (source1, source2))
        logger.info('calculate Angström profile')

        if source1['alt'][0] < source2['alt'][0]:
            f_source = source1  # first profile
            s_source = source2  # second profile
            f_wl = wl1
            s_wl = wl2
        else:
            f_source = source2  # first profile
            s_source = source1  # second profile
            f_wl = wl2
            s_wl = wl1

        if s_source['alt'][0] in f_source['alt']:  # both profiles have the same altitude grid
            idx_shift = int(np.where(f_source['alt'] == s_source['alt'][0])[0])
            max_bin = min(len(f_source['data']) - idx_shift, len(s_source['data']))
            f_profile = f_source['data'][idx_shift: max_bin + idx_shift]
            f_error = f_source['error'][idx_shift: max_bin + idx_shift]
            f_cloud = f_source['cloud'][idx_shift: max_bin + idx_shift]
            s_profile = s_source['data'][:max_bin]
            s_error = s_source['error'][:max_bin]
            s_cloud = s_source['cloud'][:max_bin]
            f_alt = f_source['alt'][idx_shift: max_bin + idx_shift]
            s_alt = s_source['alt'][:max_bin]
            f_vert_res = f_source['vert_res'][idx_shift: max_bin + idx_shift]
            s_vert_res = s_source['vert_res'][:max_bin]

        else:  # the altitude grid is different -> interpolation is needed

            logger.info('interpolation')

            s_profile = np.interp(f_source['alt'], s_source['alt'], s_source['data'],
                                  left=np.nan,
                                  right=np.nan)  # interpolation of bsc2 profile to alt1 axis, missing values = nan
            s_error = np.interp(f_source['alt'], s_source['alt'], s_source['error'],
                                left=np.nan,
                                right=np.nan)  # interpolation of bsc2 profile to alt1 axis, missing values = nan
            f_profile = f_source['data']
            f_error = f_source['error']
            f_alt = f_source['alt']
            f_cloud = f_source['cloud']
            s_alt = f_alt
            s_cloud = s_source['cloud']
            f_vert_res = f_source['vert_res']
            s_vert_res = f_vert_res

        factor = 1 / (log(s_wl) - log(f_wl))

        if isinstance(f_profile, np.ma.MaskedArray) or isinstance(s_profile, np.ma.MaskedArray) :
            data = (np.log(f_profile) - np.log(s_profile)) * factor
            data[data.mask] = np.nan
        else:
            data = np.ma.array((np.log(f_profile) - np.log(s_profile)) * factor, mask=np.zeros(f_profile.shape))

        error = data[:] * np.sqrt(np.square(s_error[:] / s_profile[:]) + \
                                  np.square(f_error[:] / f_profile[:]))
        error[error.mask] = np.nan

        target['mean'] = {'data': data,
                          'error': error,
                          'cloud': np.max([f_cloud, s_cloud], axis = 0),
                          'alt': np.max([f_alt, s_alt ], axis = 0),
                          'vert_res': np.max([f_vert_res, s_vert_res ], axis = 0),
                          'fill_value': f_source['fill_value']}
        target['exists'] = True

    def set_axes_limits(self):
        for plot_type in mc.PROFILES_IN_PLOT:
            self.axis_limits[plot_type]['min'] = mc.RES_AXES_LIMITS[plot_type]['min']
            self.axis_limits[plot_type]['max'] = mc.RES_AXES_LIMITS[plot_type]['max']
            if mc.INI_AUTO_SCALE:
                for dtype in mc.PROFILES_IN_PLOT[plot_type]:
                    if self.data[dtype]['exists']:
                        profile = self.data[dtype]['mean']['data']

                        profile_min = np.nanpercentile(profile, self.axis_limits[plot_type]['min_percentile']) \
                                      * mc.RES_DATA_SETTINGS[dtype]['scale_factor']
                        profile_max = np.nanpercentile(profile, self.axis_limits[plot_type]['max_percentile']) \
                                      * mc.RES_DATA_SETTINGS[dtype]['scale_factor']

                        self.axis_limits[plot_type]['min'] = min(self.axis_limits[plot_type]['min'], profile_min)
                        self.axis_limits[plot_type]['max'] = max(self.axis_limits[plot_type]['max'], profile_max)

    def set_zero_line_data(self):
        self.zero_line_data = np.zeros((100))
        self.zero_line_alt = np.array(range(100)) * (self.data['max_alt'] / 99.)

    def set_title(self):
        self.title = self.meas_id + ': ' + self.data['start_time'].strftime('%Y-%m-%d %H:%M:%S - ') + self.data[
            'end_time'].strftime('%H:%M:%S')

    def set_original_data(self):
        self.original_data = copy.deepcopy(self.data)

    def set_invalid(self, min, max, data_path):

        if not self.data[data_path]['exists']:
            return

        data = self.data[data_path]['mean']

        alt = data['alt']
        data_array = data['data']
        error_array = data['error']

        indexes = np.where((alt > min) & (alt < max))

        data_array[indexes] = np.NaN
        error_array[indexes] = np.NaN

    def set_valid(self, min, max, data_path):

        if not self.data[data_path]['exists']:
            return

        data = self.data[data_path]['mean']
        original_data = self.original_data[data_path]['mean']

        alt = data['alt']

        indexes = np.where((alt > min) & (alt < max))

        data['data'][indexes] = original_data['data'][indexes]
        data['error'][indexes] = original_data['error'][indexes]

    def set_cloud(self, min, max, orig_data_path):

        if not self.data[orig_data_path]['exists']:
            return

        data = self.data[orig_data_path]['mean']

        alt = data['alt']

        if 'cloud' not in data:
            data['cloud'] = np.full(alt.shape, 1, dtype=float)

        indexes = np.where((alt > min) & (alt < max) & (data['cloud'] != NC_FILL_BYTE) )

        data['cloud'][indexes] = CIRRUS

    def remove_cloud(self, min, max, orig_data_path):

        if not self.data[orig_data_path]['exists']:
            return

        data = self.data[orig_data_path]['mean']

        alt = data['alt']

        if 'cloud' not in data:
            data['cloud'] = np.full(alt.shape, 1, dtype=float)
            return

        indexes = np.where((alt > min) & (alt < max))

        data['cloud'][indexes] = NO_CLOUD

    def export(self):

        DataExport(self)


class ResultPlotRegionItem(pg.LinearRegionItem):
    def __init__(self, plot, plot_parent, parent, **kwargs):
        self.parent = parent
        self.plot_name = plot
        self.data = parent.data
        self.menu = None
        super(ResultPlotRegionItem, self).__init__(**kwargs)

    def set_menu(self):
        menu = QMenu()

        menu.clear()

        menu.view = pg.weakref.ref(
            self)  ## keep weakref to view to avoid circular reference (don't know why, but this prevents the ViewBox from being collected)
        menu.valid = False  ## tells us whether the ui needs to be updated
        menu.viewMap = pg.weakref.WeakValueDictionary()  ## weakrefs to all views listed in the link combos

        menu.setTitle("Region options")

        if self.plot_name in mc.RES_DISPLAY_CLOUD_MENU:
            set_cloud = QAction("Mark as cloud", self)
            set_cloud.triggered.connect(self.mark_cloud)
            menu.addAction(set_cloud)
            remove_cloud = QAction("Unmark as cloud", self)
            remove_cloud.triggered.connect(self.unmark_cloud)
            menu.addAction(remove_cloud)

        if self.plot_name in mc.RES_VALIDATION_MENU:
            invalid = menu.addMenu("Set as Invalid")
            valid = menu.addMenu("Set as valid")
            names = mc.RES_VALIDATION_MENU[self.plot_name].keys()
            for name in names:
                add_valid = QAction(name, self)
                add_valid.triggered.connect(functools.partial(self.set_valid, name))
                valid.addAction(add_valid)
                add_invalid = QAction(name, self)
                add_invalid.triggered.connect(functools.partial(self.set_invalid, name))
                invalid.addAction(add_invalid)

            add_valid = QAction("All", self)
            add_valid.triggered.connect(functools.partial(self.set_valid, "All"))
            valid.addAction(add_valid)
            add_invalid = QAction("All", self)
            add_invalid.triggered.connect(functools.partial(self.set_invalid, "All"))
            invalid.addAction(add_invalid)

        return menu

    def getMenu(self):
        if not self.menu:
            self.menu = self.set_menu()

    def raiseContextMenu(self, ev):
        self.getMenu()
        self.menu.popup(ev.screenPos().toPoint())

    def mouseClickEvent(self, ev):
        if self.moving and ev.button() == pg.QtCore.Qt.RightButton:
            super(ResultPlotRegionItem, self).mouseClickEvent(ev)
        elif ev.button() == pg.QtCore.Qt.RightButton:
            ev.accept()
            self.raiseContextMenu(ev)

    def set_valid(self, name):
        self.change_data(self.data.set_valid, name)

    def change_data(self, handler, name):
        if not self.parent.regions:
            return

        if name == "All":
            curves = self.get_all_curves()
        else:
            curves = mc.RES_VALIDATION_MENU[self.plot_name][name]

        for region in self.parent.regions.values():
            min, max = region.getRegion()
            for curve in curves:
                handler(min, max, curve)

        self.parent.reset_regions()
        self.parent.redraw_plots()

    def set_invalid(self, name):

        self.change_data(self.data.set_invalid, name)

    def get_all_curves(self):
        curves = []
        for x in mc.RES_VALIDATION_MENU[self.plot_name].values():
            curves += x

        return list(set(curves))

    def mark_cloud(self):
        handler = self.data.set_cloud
        self.change_cloud(handler)

    def unmark_cloud(self):
        handler = self.data.remove_cloud
        self.change_cloud(handler)

    def change_cloud(self, handler):
        curves = mc.RES_DISPLAY_CLOUD_MENU[self.plot_name]

        for region in self.parent.regions.values():
            min, max = region.getRegion()
            for curve in curves:
                handler(min, max, curve)
        self.parent.reset_regions()
        self.parent.redraw_plots()




class ResultPlotViewBox(pg.ViewBox):
    def __init__(self, plot_parent, plot_name):
        self.plot_parent = plot_parent
        self.plot_name = plot_name
        self.regions = {}
        self.data = self.plot_parent.mes_data
        self.ctrl = {}

        super(ResultPlotViewBox, self).__init__()

        self.menu = None

    def set_menu(self):
        curve = getattr(self.plot_parent, self.plot_name)
        curve.ctrlMenu = None

        menu = QMenu()

        menu.clear()

        menu.view = pg.weakref.ref(
            self)  ## keep weakref to view to avoid circular reference (don't know why, but this prevents the ViewBox from being collected)
        menu.valid = False  ## tells us whether the ui needs to be updated
        menu.viewMap = pg.weakref.WeakValueDictionary()  ## weakrefs to all views listed in the link combos

        menu.setTitle("Plot options")

        self.viewAll = QAction("View All", self)
        self.viewAll.triggered.connect(self.autoRange)
        self.addAction(self.viewAll)

        for axis in 'XY':
            w = ui = uic.loadUi(
                resource_path(
                    os.path.join(
                        PROJECT_PATH,
                        'UI/axisCtrlTemplateSimple.ui')))

            sub_a = QWidgetAction(self)
            sub_a.setDefaultWidget(w)

            a = menu.addMenu("%s Axis" % axis)
            a.addAction(sub_a)

            self.ctrl[axis] = ui

            connects = [
                (ui.minText.editingFinished, 'MinTextChanged'),
                (ui.maxText.editingFinished, 'MaxTextChanged'),
                (ui.minText.returnPressed, 'MinTextChanged'),
                (ui.maxText.returnPressed, 'MaxTextChanged')
            ]

            for sig, fn in connects:
                sig.connect(getattr(self, axis.lower() + fn))

#        store_as_netcdf = QAction("Export as Netcdf", self)
#        store_as_netcdf.triggered.connect(self.export_data)
#        menu.addAction(store_as_netcdf)

        self.updateStates()
        self.sigStateChanged.connect(self.viewStateChanged)
        # self.sigRangeChanged.connect(self.viewStateChanged)
        # self.sigRangeChangedManually.connect(self.viewStateChanged)

        return menu

    def viewStateChanged(self):
        self.updateStates()

    def updateStates(self):
        state = self.getState(copy=False)

        for i in 'XY':  # x, y
            index = 'XY'.find(i)
            tr = state['targetRange'][index]
            self.ctrl[i].minText.setText("%0.5g" % tr[0])
            self.ctrl[i].maxText.setText("%0.5g" % tr[1])

    def xMinTextChanged(self):
        try:
            self.setLimits(xMin=float(self.ctrl['X'].minText.text()))
        except ValueError:
            self.updateStates()

    def xMaxTextChanged(self):
        try:
            self.setLimits(xMax=float(self.ctrl['X'].maxText.text()))
        except ValueError:
            self.updateStates()

    def yMinTextChanged(self):
        try:
            self.setLimits(yMin=float(self.ctrl['Y'].minText.text()))
        except ValueError:
            self.updateStates()

    def yMaxTextChanged(self):
        try:
            self.setLimits(yMax=float(self.ctrl['Y'].maxText.text()))
        except ValueError:
            self.updateStates()

#    def export_data(self):
#        self.data.export()

    def mouseClickEvent(self, ev):
        if not self.menu:
            self.menu = self.set_menu()
        if ev.button() == pg.QtCore.Qt.RightButton and self.menuEnabled():
            super(ResultPlotViewBox, self).mouseClickEvent(ev)

    def mouseDoubleClickEvent(self, event):
        self.mouse_double_click(event)

    def mouse_double_click(self, ev):
        ev.accept()

        self.add_region(ev.scenePos())

    def add_region(self, position):
        """
        Called from the viewbox  self.contour_plot.vb on click of middle mouse button
        The position is given as float value [0,1] where 0 is left and
        :return:
        """
        region = self.region_selector(position)
        self.regions[id(region)] = region

    def region_selector(self, position):
        curve = getattr(self.plot_parent, self.plot_name)
        region = ResultPlotRegionItem(
            self.plot_name,
            self.plot_parent,
            self,
            values=[0, 1],
            orientation=ResultPlotRegionItem.Horizontal,
        )

        start = self.mapSceneToView(position).y() - mc.RES_INITIAL_REGION_WIDTH / 2
        end = start + mc.RES_INITIAL_REGION_WIDTH
        region.setRegion((start, end))
        region.setZValue(1000)
        curve.addItem(region)
        return region

    def reset_regions(self):
        for region in self.regions.keys():
            self.regions[region].deleteLater()
        self.regions = {}

    def redraw_plots(self):
        self.plot_parent.redraw_plots()


class ResultPlot(pg.GraphicsLayoutWidget):
    def setup(self, data):
        self.plots = []
        self.legends = []
        self.regions = {}
        self.plots_limits = {
            'bsc_plot': 'Backscatter',
            'ext_plot': 'Extinction',
            'lr_plot': 'lidar_ratio',
            'angstroem_plot': 'angstroem',
            'depol_plot': 'Depol',
        }
        self.mes_data = data
        self.title = util.get_MDI_Win_title(self.mes_data.title)
        self.set_layout()
        self.define_axis()
        self.setup_plots()
        self.resize(mc.PLOT_WINDOW_SIZE[0] - 30, mc.PLOT_WINDOW_SIZE[1] - 30)
        self.setBackground('w')
        self.setDataRanges()
        self.set_legends()

        self.create_menu()

    # Actions for the menu
    def create_actions(self):
        """
        Here a list of Actions is provided for the menu:
            util.createMappedAction(
                mapper,
                None,
                "&", self,
                None,
                "export as quality controlled nc files"),
        Creates an action called "export as quality controlled nc files" in the menu which calls the "export as quality controlled nc files" function on the currently active instance
        """
        self.mapper = QtCore.QSignalMapper()
        self.mapper.mapped[str].connect(self.mappedQuicklookAction)
        self._actions = [

            util.createMappedAction(
                self.mapper,
                None,
                "&export as quality controlled nc files", self,
                QtGui.QKeySequence(),
                "export_data"),

            # util.createMappedAction(
            #     self.mapper,
            #     None,
            #     "&was anderes wird passieren", self,
            #     QtGui.QKeySequence(),
            #     "was_anderes"),
        ]
    # Main menu for profile plot
    def create_menu(self):
        """
        Contructs the menu and populates it with the actions defined in create_actions
        :return:
        """
        self.create_actions()
        self._menu = QtGui.QMenu('profile plot')
        for action in self._actions:
            self._menu.addAction(action)
        menuBar = util.get_main_win().menuBar()
        for action in menuBar.actions():
            if action.menu().title() == "profile plot":
                menuBar.removeAction(action)
        menuBar.addMenu(self._menu)

    @QtCore.pyqtSlot(str)
    def mappedQuicklookAction(self, method_name):
        """
        All menu actions of the quicklook menu are mapped by the Signal Mapper to this function.
        Here the currently active quicklook instance will be derived and the function name (String) of the action will be
        called on this instance.
        """
        # find currently active quicklook instance
        active_win = util.get_active_MDI_win()
        # call the function of the action on the instance
        getattr(active_win, str(method_name))()

    # Menu Handler
    # ==================================================================================================================
    def export_data(self):
        self.mes_data.export()
        QtGui.QMessageBox.about(
            self, "Done", "quality controlled nc files were created")

    # def was_anderes(self):
    #     QtGui.QMessageBox.about(
    #         self,
    #         "Es ist was geschehen",
    #         "Was anders ist in Fenster %s geschehen" %
    #         self.title)


    def setDataRanges(self):
        viewbox = self.bsc_plot.vb
        viewbox.enableAutoRange(viewbox.YAxis, False)
        min_heigth = mc.RES_MIN_ALT
        max_heigth = self.mes_data.data['max_alt']
        viewbox.setYRange(
            min_heigth,
            max_heigth)

        for plot in self.plots_limits.keys():
            plot_obj = getattr(self, plot)
            viewbox = plot_obj.vb
            min = self.mes_data.axis_limits[self.plots_limits[plot]]['min']
            max = self.mes_data.axis_limits[self.plots_limits[plot]]['max']
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
            viewBox=ResultPlotViewBox(self, 'bsc_plot')
        )
        self.update_bsc_profile()
        self.plots.append(self.bsc_plot)

    def update_bsc_profile(self):
        self.bsc_plot.clear()
        self.bsc_plot.plot(
            self.mes_data.zero_line_data, self.mes_data.zero_line_alt, pen='k', clear=True, connect='finite'
        )

        cloud = None

        for dtype in mc.PROFILES_IN_PLOT['Backscatter']:
            if self.mes_data.data[dtype]['exists']:
                profile = self.mes_data.data[dtype]['mean']
                orig_profile = self.mes_data.original_data[dtype]['mean']
                try:
                    self.bsc_plot.plot(orig_profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                       orig_profile['alt'],
                                       pen={'color': self.mes_data.data[dtype]['color'], 'width': 1},
                                       clear=False, connect='finite')
                    self.bsc_plot.plot(profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                       profile['alt'],
                                       pen={'color': self.mes_data.data[dtype]['color'], 'width': 3},
                                       name=dtype,
                                       clear=False, connect='finite')
                except ValueError:
                    logger.error('Could not plot %s.' % dtype)
                    logger.error("Traceback: %s" % tb.format_exc())

                if 'cloud' in profile:
                    if cloud is None:
                        cloud = profile
                    else:
                        cloud = self.mes_data.calc_mean_data([cloud, profile])

        if cloud is not None:
            self.add_cloud_to_plot(cloud, self.bsc_plot, 'bsc_plot')

    def setup_ext_profile(self):
        self.ext_plot = self.plot_layout.addPlot(
            axisItems={'bottom': self.plot_2_axis},
            viewBox=ResultPlotViewBox(self, 'ext_plot')
        )
        self.ext_plot.hideAxis('left')
        self.update_ext_profile()
        self.ext_plot.setYLink(self.bsc_plot)
        self.plots.append(self.ext_plot)

    def update_ext_profile(self):
        self.ext_plot.clear()
        self.ext_plot.plot(
            self.mes_data.zero_line_data, self.mes_data.zero_line_alt, pen='k', clear=True
        )

        cloud = None

        for dtype in mc.PROFILES_IN_PLOT['Extinction']:
            if self.mes_data.data[dtype]['exists']:
                profile = self.mes_data.data[dtype]['mean']
                orig_profile = self.mes_data.original_data[dtype]['mean']
                try:
                    self.ext_plot.plot(orig_profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                       orig_profile['alt'],
                                       pen={'color': self.mes_data.data[dtype]['color'], 'width': 1},
                                       clear=False, connect='finite')
                    self.ext_plot.plot(profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                       profile['alt'],
                                       pen={'color': self.mes_data.data[dtype]['color'], 'width': 3},
                                       name=dtype,
                                       clear=False, connect='finite')

                except ValueError:
                    logger.error('Could not plot %s.' % dtype)
                    logger.error("Traceback: %s" % tb.format_exc())

                if 'cloud' in profile:
                    if cloud is None:
                        cloud = profile
                    else:
                        cloud = self.mes_data.calc_mean_data([cloud, profile])

        if cloud is not None:
            self.add_cloud_to_plot(cloud, self.ext_plot, 'ext_plot')

    def setup_lidar_ratio(self):
        self.lr_plot = self.plot_layout.addPlot(
            axisItems={'bottom': self.plot_3_axis},
            viewBox=ResultPlotViewBox(self, 'lr_plot')
        )
        self.lr_plot.hideAxis('left')
        self.update_lidar_ratio()
        self.lr_plot.setYLink(self.bsc_plot)
        self.plots.append(self.lr_plot)

    def update_lidar_ratio(self):
        self.lr_plot.clear()
        self.lr_plot.plot(self.mes_data.zero_line_data, self.mes_data.zero_line_alt, pen='k', connect='finite')
        self.lr_plot.plot(self.mes_data.zero_line_data + 100., self.mes_data.zero_line_alt, pen=0.75, connect='finite')

        cloud = None

        for dtype in mc.PROFILES_IN_PLOT['lidar_ratio']:
            if self.mes_data.data[dtype]['exists']:
                profile = self.mes_data.data[dtype]['mean']
                orig_profile = self.mes_data.original_data[dtype]['mean']
                try:
                    self.lr_plot.plot(orig_profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                      orig_profile['alt'],
                                      pen={'color': self.mes_data.data[dtype]['color'], 'width': 1},
                                      clear=False, connect='finite')
                    self.lr_plot.plot(profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                      profile['alt'],
                                      pen={'color': self.mes_data.data[dtype]['color'], 'width': 3},
                                      name=dtype,
                                      clear=False, connect='finite')

                except ValueError:
                    logger.error('Could not plot %s.' % dtype)
                    logger.error("Traceback: %s" % tb.format_exc())

                if 'cloud' in profile:
                    if cloud is None:
                        cloud = profile
                    else:
                        cloud = self.mes_data.calc_mean_data([cloud, profile])

        if cloud is not None:
            self.add_cloud_to_plot(cloud, self.lr_plot, 'lr_plot')

    def setup_depol(self):
        self.depol_plot = self.plot_layout.addPlot(
            axisItems={'bottom': self.plot_4_axis},
            viewBox=ResultPlotViewBox(self, 'depol_plot')
        )
        self.depol_plot.hideAxis('left')
        self.update_depol()
        self.depol_plot.setYLink(self.bsc_plot)
        self.plots.append(self.depol_plot)

    def update_depol(self):
        self.depol_plot.clear()
        self.depol_plot.plot(self.mes_data.zero_line_data, self.mes_data.zero_line_alt, pen='k', connect='finite')

        cloud = None

        for dtype in mc.PROFILES_IN_PLOT['Depol']:
            if self.mes_data.data[dtype]['exists']:
                profile = self.mes_data.data[dtype]['mean']
                orig_profile = self.mes_data.original_data[dtype]['mean']
                try:
                    self.depol_plot.plot(orig_profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                         orig_profile['alt'],
                                         pen={'color': self.mes_data.data[dtype]['color'], 'width': 1},
                                         clear=False, connect='finite')
                    self.depol_plot.plot(profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                         profile['alt'],
                                         pen={'color': self.mes_data.data[dtype]['color'], 'width': 3},
                                         name=dtype,
                                         clear=False, connect='finite')
                except ValueError:
                    logger.error('Could not plot %s.' % dtype)
                    logger.error("Traceback: %s" % tb.format_exc())

                if 'cloud' in profile:
                    if cloud is None:
                        cloud = profile
                    else:
                        cloud = self.mes_data.calc_mean_data([cloud, profile])

        if cloud is not None:
            self.add_cloud_to_plot(cloud, self.depol_plot, 'depol_plot')

    def setup_angstroem(self):
        self.angstroem_plot = self.plot_layout.addPlot(
            axisItems={'bottom': self.plot_5_axis},
            viewBox=ResultPlotViewBox(self, 'angstroem_plot')
        )
        self.angstroem_plot.hideAxis('left')
        self.update_angetroem()
        self.angstroem_plot.setYLink(self.bsc_plot)
        self.plots.append(self.angstroem_plot)

    def update_angetroem(self):
        self.angstroem_plot.clear()

        cloud = None

        self.angstroem_plot.plot(self.mes_data.zero_line_data, self.mes_data.zero_line_alt, pen='k', connect='finite')
        self.angstroem_plot.plot(self.mes_data.zero_line_data - 1., self.mes_data.zero_line_alt, pen=0.75,
                                 connect='finite')
        self.angstroem_plot.plot(self.mes_data.zero_line_data + 3., self.mes_data.zero_line_alt, pen=0.75,
                                 connect='finite')

        for dtype in mc.PROFILES_IN_PLOT['angstroem']:
            if self.mes_data.data[dtype]['exists']:
                profile = self.mes_data.data[dtype]['mean']
                orig_profile = self.mes_data.original_data[dtype]['mean']
                try:
                    self.angstroem_plot.plot(orig_profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                             orig_profile['alt'],
                                             pen={'color': self.mes_data.data[dtype]['color'], 'width': 1},
                                             clear=False, connect='finite')
                    self.angstroem_plot.plot(profile['data'] * self.mes_data.data[dtype]['scale_factor'],
                                             profile['alt'],
                                             pen={'color': self.mes_data.data[dtype]['color'], 'width': 3},
                                             name=dtype,
                                             clear=False, connect='finite')
                except ValueError:
                    logger.error('Could not plot %s.' % dtype)
                    logger.error("Traceback: %s" % tb.format_exc())

                if 'cloud' in profile:
                    if cloud is None:
                        cloud = profile
                    else:
                        cloud = self.mes_data.calc_mean_data([cloud, profile])

        if cloud is not None:
            self.add_cloud_to_plot(cloud, self.angstroem_plot, 'angstroem_plot')

    def set_legends(self):
        if mc.RES_SHOW_LEGEND:
            for plot in self.plots:
                legend = ResultLegendItem()
                legend.setParentItem(plot)
                for item in plot.items:
                    if item.name():
                        if item.name() in self.mes_data.data:
                            if 'scale_str' in self.mes_data.data[item.name()]:
                                legend.addItem(item, item.name() + self.mes_data.data[item.name()]['scale_str'])
                            else:
                                legend.addItem(item, item.name())
                        else:
                            legend.addItem(item, item.name() )

                plot.legend = legend

    def redraw_plots(self):
        self.update_depol()
        self.update_angetroem()
        self.update_lidar_ratio()
        self.update_ext_profile()
        self.update_bsc_profile()

    def add_cloud_to_plot(self, cloud_data, plot, plot_name):
        min = self.mes_data.axis_limits[self.plots_limits[plot_name]]['min']
        max = self.mes_data.axis_limits[self.plots_limits[plot_name]]['max']

        cloud = np.ma.masked_array(cloud_data['cloud'] * 1.0, cloud_data['cloud'] != 2)
        cloud = cloud.filled(fill_value=np.NaN)
        cloud = cloud * min / 2

        plot.plot(cloud,
                  cloud_data['alt'],
                  pen={'hsv': mc.RES_CLOUD_LINE_COLOR, 'width': 6, },
                  name='cloud',
                  clear=False, connect='finite')


class ResultLegendItem(pg.LegendItem):
    def __init__(self):
        super(ResultLegendItem, self).__init__()
        self.labels = []

    def paint(self, p, *args):
        p.setPen(pg.fn.mkPen(255, 255, 255, 100))
        p.setBrush(pg.fn.mkBrush(220, 220, 220))
        p.drawRect(self.boundingRect())

    def addItem(self, item, name):
        """
        Add a new entry to the legend.

        ==============  ========================================================
        **Arguments:**
        item            A PlotDataItem from which the line and point style
                        of the item will be determined or an instance of
                        ItemSample (or a subclass), allowing the item display
                        to be customized.
        title           The title to display for this item. Simple HTML allowed.
        ==============  ========================================================
        """
        if name in self.labels:
            return
        label = pg.LabelItem(name, **mc.RES_LEGEND_LABEL_STYLE)
        if isinstance(item, ItemSample):
            sample = item
        else:
            sample = ItemSample(item)
        row = self.layout.rowCount()
        self.items.append((sample, label))
        self.layout.addItem(sample, row, 0)
        self.layout.addItem(label, row, 1)
        self.updateSize()
        self.labels.append(name)

