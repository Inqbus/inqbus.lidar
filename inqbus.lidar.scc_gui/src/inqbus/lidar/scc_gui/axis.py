import pyqtgraph as pg
import time
import datetime
import sys
import traceback as tb

from inqbus.lidar.scc_gui import logger

ONE_DAY = datetime.timedelta(1)
ONE_MONTH = datetime.timedelta(30)
TWO_YEARS = datetime.timedelta(365 * 2)

KILOMETER_LABEL_RANGE = 10000


class DataAxis(pg.AxisItem):
    """
    """
    axis_data = None


class HeightAxis(DataAxis):
    """
    """
    axis_data = None

    def tickStrings(self, values, scale, spacing):
        strns = []
        datavalues = []
        for value in values:
            if value < self.axis_data.shape[0]:
                datavalues.append(self.axis_data[int(value)])
        try:
            min_value = min(datavalues)
        except BaseException:
            logger.error("Exception: %s" % sys.exc_info()[0])
            logger.error("Traceback: %s" % tb.format_tb(sys.exc_info()[2]))
            min_value = self.axis_data[0]
        try:
            max_value = max(datavalues)
        except BaseException:
            logger.error("Exception: %s" % sys.exc_info()[0])
            logger.error("Traceback: %s" % tb.format_tb(sys.exc_info()[2]))
            max_value = self.axis_data[-1]

        rng = abs(max_value - min_value)

        if rng < KILOMETER_LABEL_RANGE:
            for x in datavalues:
                try:
                    strns.append(str(round(x, 3)))
                except BaseException:
                    strns.append('')
            label = 'm'
        else:
            # TODO: Sometimes single values are displayed as meter
            for x in datavalues:
                try:
                    strns.append(str(round(x / 1000., 2)))
                except BaseException:
                    strns.append('')
            label = 'km'

        self.setLabel(text=label)
        return strns


class DateAxis(DataAxis):
    """
    Axis with datetimes as tics
    """

    def tickStrings(self, values, scale, spacing):
        strns = []
        try:
            min_time = self.axis_data[min(values)]
        except BaseException:
            min_time = self.axis_data[0]
        try:
            max_time = self.axis_data[max(values)]
        except BaseException:
            max_time = self.axis_data[-1]

        rng = max_time - min_time

        if rng < ONE_DAY:
            string = '%H:%M:%S'
            label1 = '%b %d -'
            label2 = ' %b %d, %Y'
        elif rng >= ONE_DAY and rng < ONE_MONTH:
            string = '%d'
            label1 = '%b - '
            label2 = '%b, %Y'
        elif rng >= ONE_MONTH and rng < TWO_YEARS:
            string = '%b'
            label1 = '%Y -'
            label2 = ' %Y'
        elif rng >= TWO_YEARS:
            string = '%Y'
            label1 = ''
            label2 = ''
        for x in values:
            try:
                strns.append(self.axis_data[int(x)].strftime(string))
            except ValueError:  # Windows can't handle dates before 1970
                strns.append('')
            except IndexError:
                strns.append('')

        try:
            label = min_time.strftime(label1) + max_time.strftime(label2)
        except ValueError:
            label = ''
        self.setLabel(text=label)
        return strns
