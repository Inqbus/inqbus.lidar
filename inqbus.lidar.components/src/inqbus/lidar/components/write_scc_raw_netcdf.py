import datetime
import os
import string

import numpy
from scipy.io import netcdf

NC_FILL_INT = -2147483647
NC_FILL_FLOAT = 9.9692099683868690e+36
NC_FILL_DOUBLE = 9.9692099683868690e+36


def ncname(measurement):
    datestr = measurement['header']['start'].strftime('%Y%m%d')
    startstr = measurement['header']['start'].strftime('%H%M%S')
    stopstr = measurement['header']['stop'].strftime('%H%M%S')

    filename = 'oh_LIDAR'
    filename = '_'.join([filename, datestr])
    filename = '_'.join([filename, startstr])
    filename = '_'.join([filename, stopstr], )
    measurement['filenamebody'] = filename

    filename = '.'.join([filename, 'nc'])
    return filename


def create_dimensions(nc_file, measurement):
    print('create_dimensions')

    dim = nc_file.createDimension('points', measurement['header']['bins'])
    dim = nc_file.createDimension(
        'channels', measurement['header']['num_channels'])
    dim = nc_file.createDimension('time', len(measurement['data']))
    dim = nc_file.createDimension(
        'nb_of_time_scales',
        measurement['header']['time_scales'])
    dim = nc_file.createDimension('scan_angles', 1)


def write_attributes(nc_file, measurement):
    print('write_attributes')

    nc_file.Measurement_ID = measurement['ID']
    nc_file.RawData_Start_Date = measurement['header']['start'].strftime(
        '%Y%m%d')
    nc_file.RawData_Start_Time_UT = measurement['header']['start'].strftime(
        '%H%M%S')
    nc_file.RawData_Stop_Time_UT = measurement['header']['stop'].strftime(
        '%H%M%S')
    nc_file.Sounding_File_Name = measurement['sounding']
    if 'comment' in measurement:
        nc_file.Comment = measurement['comment']


def write_variables(nc_file, measurement):
    print('create variables')

    bg_height_last_var = nc_file.createVariable('Background_High',
                                                numpy.float64,
                                                ('channels',))

    bg_height_first_var = nc_file.createVariable('Background_Low',
                                                 numpy.float64,
                                                 ('channels',))

    bg_mode_var = nc_file.createVariable('Background_Mode',
                                         numpy.int,
                                         ('channels',))

    lr_input_var = nc_file.createVariable('LR_Input',
                                          numpy.int,
                                          ('channels',))

    angle_var = nc_file.createVariable('Laser_Pointing_Angle',
                                       numpy.float64,
                                       ('scan_angles',))

    angle_id_var = nc_file.createVariable('Laser_Pointing_Angle_of_Profiles',
                                          numpy.int,
                                          ('time', 'nb_of_time_scales'))

    shots_var = nc_file.createVariable('Laser_Shots',
                                       numpy.int,
                                       ('time', 'channels'))

    mol_calc_var = nc_file.createVariable('Molecular_Calc',
                                          numpy.int,
                                          ())
    pres_var = nc_file.createVariable('Pressure_at_Lidar_Station',
                                      numpy.float64,
                                      ())
    temp_var = nc_file.createVariable('Temperature_at_Lidar_Station',
                                      numpy.float64,
                                      ())

    range_res_var = nc_file.createVariable('Raw_Data_Range_Resolution',
                                           numpy.float64,
                                           ('channels',))

    start_var = nc_file.createVariable('Raw_Data_Start_Time',
                                       numpy.int,
                                       ('time', 'nb_of_time_scales'))

    stop_var = nc_file.createVariable('Raw_Data_Stop_Time',
                                      numpy.int,
                                      ('time', 'nb_of_time_scales'))

    data_var = nc_file.createVariable('Raw_Lidar_Data',
                                      numpy.float64,
                                      ('time', 'channels', 'points'))

    range_id_var = nc_file.createVariable('ID_Range',
                                          numpy.int,
                                          ('channels',))

    ch_id_var = nc_file.createVariable('channel_ID',
                                       numpy.int,
                                       ('channels',))

    time_scale_id_var = nc_file.createVariable('id_timescale',
                                               numpy.int,
                                               ('channels',))

    print('write data')

    for ch in range(0, measurement['header']['num_channels']):
        range_res_var[ch] = measurement['header']['range_res'][ch]
        bg_height_first_var[ch] = measurement['header']['bg_first']
        bg_height_last_var[ch] = measurement['header']['bg_last']
        time_scale_id_var[ch] = measurement['header']['time_scale'][ch]
        ch_id_var[ch] = measurement['header']['channel_id'][ch]
        lr_input_var[ch] = 1
        bg_mode_var[ch] = 0
        range_id_var[ch] = measurement['header']['range_id'][ch]

    angle_var[0] = measurement['header']['angle']

    if 'sounding' in measurement and (measurement['sounding'] != ''):
        mol_calc_var.assignValue(1)
        pres_var.assignValue(measurement['pressure'])
        temp_var.assignValue(measurement['temperature'])
    else:
        mol_calc_var.assignValue(0)
        pres_var.assignValue(measurement['pressure'])
        temp_var.assignValue(measurement['temperature'])

    for t in range(0, len(measurement['data'])):
        angle_id_var[t, 0] = 0
        start_var[t, 0] = measurement['data'][t]['start']
        stop_var[t, 0] = measurement['data'][t]['stop']

        for ch in range(0, measurement['header']['num_channels']):
            shots_var[t, ch] = measurement['data'][t]['header']['shots'][ch]

            lastbin = len(measurement['data'][t]['data'][ch])

            data_var[t, ch] = measurement['data'][t]['data'][ch]

            data_var[t, ch, lastbin:measurement['header']
                     ['bins']] = NC_FILL_DOUBLE


def extract_session_time(measurement, sched_start, sched_stop):
    if sched_start > measurement['header']['start']:
        dt_start = (sched_start - measurement['header']['start']).seconds
    else:
        dt_start = 0
    dt_stop = (sched_stop - measurement['header']['start']).seconds

    t = 0
    while measurement['data'][t]['start'] < dt_start:
        print(measurement['data'][t]['start'])
        t = t + 1
    tmin = max(t - 1, 0)
    t = 0
    while (measurement['data'][t]['stop'] < dt_stop) and \
            (t < len(measurement['data']) - 1):
        t = t + 1
    tmax = min(t + 1, len(measurement['data']) - 1)

    measurement['header']['stop'] = measurement['header']['start'] + \
        datetime.timedelta(seconds=measurement['data'][tmax]['stop'])
    measurement['header']['start'] = measurement['header']['start'] + \
        datetime.timedelta(seconds=measurement['data'][tmin]['start'])

    measurement['data'] = measurement['data'][tmin:tmax + 1]

    t0 = measurement['data'][0]['start']
    for t in range(0, len(measurement['data'])):
        measurement['data'][t]['stop'] = measurement['data'][t]['stop'] - t0
        measurement['data'][t]['start'] = measurement['data'][t]['start'] - t0


def write(path, measurement, sched_start, sched_stop):
    extract_session_time(measurement, sched_start, sched_stop)
    print('write file', ncname(measurement))
    outfile = netcdf.netcdf_file(
        os.path.join(
            path,
            ncname(measurement)),
        'w',
        False,
        1)

    create_dimensions(outfile, measurement)
    write_attributes(outfile, measurement)
    write_variables(outfile, measurement)

    outfile.close()
