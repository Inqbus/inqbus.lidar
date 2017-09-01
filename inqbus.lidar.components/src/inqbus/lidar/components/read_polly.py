import datetime
import os

from scipy.io import netcdf

BG_FIRST = 0
BG_LAST = 251
LIGHT_SPEED = 3E8


def add_general_header_info(measurement, CHANNEL_IDs):

    last_profile = measurement['data'][len(measurement['data']) - 1]
    last_profile['stop'] = last_profile['start'] + \
        int(last_profile['header']['shots'][0] /
            measurement['header']['rep_rate'])
    range_res = float(measurement['header']['deltaT'] * 1E-9 * LIGHT_SPEED / 2)

    measurement['header']['bg_first'] = float(BG_FIRST * range_res)
    measurement['header']['bg_last'] = float(BG_LAST * range_res)

    measurement['header']['start'] = measurement['data'][0]['header']['start']
    measurement['header']['stop'] = measurement['header']['start'] + \
        datetime.timedelta(seconds=last_profile['stop'])

    measurement['header']['range_res'] = []
    measurement['header']['time_scale'] = []
    measurement['header']['channel_id'] = []
    measurement['header']['acqtype'] = []

    for ch in range(0, measurement['header']['num_channels']):
        if CHANNEL_IDs[ch] != -1:
            measurement['header']['range_res'].append(range_res)
            measurement['header']['time_scale'].append(0)
            measurement['header']['channel_id'].append(CHANNEL_IDs[ch])
            measurement['header']['acqtype'].append(1)

    measurement['header']['num_channels'] = len(
        measurement['header']['channel_id'])
    measurement['header']['time_scales'] = 1


def read_header(nc_file, CHANNEL_IDs):
    header = {}

    header['bins'] = nc_file.dimensions['height']
    header['num_channels'] = nc_file.dimensions['channel']
    header['time_scales'] = 1
    header['angle'] = nc_file.variables['zenithangle'].getValue()
    header['deltaT'] = nc_file.variables['measurement_height_resolution'].getValue()
    header['rep_rate'] = nc_file.variables['laser_rep_rate'].getValue()

    return header


def read_time(measurement, profile, time, t):
    year = int(str(time[0])[0:4])
    month = int(str(time[0])[4:6])
    day = int(str(time[0])[6:8])
    time = datetime.timedelta(seconds=time[1])

    profile['header']['start'] = datetime.datetime(
        year, month, day, 0, 0) + time

    if t > 0:
        profile['start'] = (profile['header']['start'] -
                            measurement['data'][0]['header']['start']).seconds
        measurement['data'][t - 1]['stop'] = profile['start']
    else:
        profile['start'] = 0


def read_data(measurement, profile, t, nc_file, CHANNEL_IDs):
    profile['data'] = []
    for ch in range(0, measurement['header']['num_channels']):
        if CHANNEL_IDs[ch] != -1:
            signal = nc_file.variables['raw_signal'][t, :, ch]
            profile['data'].append(signal)


def combine(meas_parts):
    print('combine')
    measurement = meas_parts[0]

    for mp in range(1, len(meas_parts)):

        if same_header(measurement['header'], meas_parts[mp]['header']):

            measurement['header']['stop'] = meas_parts[mp]['header']['stop']
            timedelta = (
                meas_parts[mp]['header']['start'] -
                measurement['header']['start']).seconds

            for p in range(0, len(meas_parts[mp]['data'])):
                profile = meas_parts[mp]['data'][p]
                profile['start'] = profile['start'] + timedelta
                profile['stop'] = profile['stop'] + timedelta
                measurement['data'].append(profile)
        meas_parts[mp] = {}
    return measurement


def same_header(h1, h2):
    if h1['bins'] != h2['bins']:
        return False
    elif h1['num_channels'] != h2['num_channels']:
        return False
    elif h1['time_scales'] != h2['time_scales']:
        return False
    elif h1['angle'] != h2['angle']:
        return False
    elif h1['deltaT'] != h2['deltaT']:
        return False
    elif h1['rep_rate'] != h2['rep_rate']:
        return False
    elif h1['bg_first'] != h2['bg_first']:
        return False
    elif h1['bg_last'] != h2['bg_last']:
        return False
    else:
        for ch in range(0, h1['num_channels']):
            if h1['range_res'] != h2['range_res']:
                return False
            if h1['time_scale'] != h2['time_scale']:
                return False
            if h1['channel_id'] != h2['channel_id']:
                return False
            if h1['acqtype'] != h2['acqtype']:
                return False
    return True


def read(
        INPATH,
        zfilenames,
        CHANNEL_IDs,
        WAVELENGTHS,
        SCAT_TYPES,
        RANGE_ID,
        GROUND_PRES,
        GROUND_TEMP):
    zfilenames.sort()
    meas_parts = []
    for zfilename in zfilenames:
        print(zfilename)
        meas_parts.append(
            read_one_file(
                os.path.join(
                    INPATH,
                    zfilename),
                CHANNEL_IDs,
                WAVELENGTHS,
                SCAT_TYPES,
                RANGE_ID,
                GROUND_PRES,
                GROUND_TEMP))
    if len(meas_parts) > 1:
        return combine(meas_parts)
    else:
        return meas_parts[0]


def read_one_file(
        zfilename,
        CHANNEL_IDs,
        WAVELENGTHS,
        SCAT_TYPES,
        RANGE_ID,
        GROUND_PRES,
        GROUND_TEMP):
    measurement = {}
    measurement['data'] = []

    nc_file_name = os.path.splitext(zfilename)[0]
    nc_file = netcdf.netcdf_file(nc_file_name, 'r', False, 1)

    measurement['header'] = read_header(nc_file, CHANNEL_IDs)

    shots = nc_file.variables['measurement_shots'].data
    times = nc_file.variables['measurement_time'].data
    measurement['temperature'] = GROUND_TEMP
    measurement['pressure'] = GROUND_PRES
    if 'if_center' in nc_file.variables:
        measurement['header']['wavelength'] = nc_file.variables['if_center'].data
    else:
        measurement['header']['wavelength'] = WAVELENGTHS

    measurement['header']['scat_type'] = SCAT_TYPES
    measurement['header']['range_id'] = RANGE_ID

    measurement['data'] = []
    for t in range(0, len(times)):
        profile = {}
        profile['header'] = {}
        profile['header']['shots'] = shots[t]

        read_time(measurement, profile, times[t], t)

        read_data(measurement, profile, t, nc_file, CHANNEL_IDs)

        measurement['data'].append(profile)

    add_general_header_info(measurement, CHANNEL_IDs)

    nc_file.close()

    return measurement
