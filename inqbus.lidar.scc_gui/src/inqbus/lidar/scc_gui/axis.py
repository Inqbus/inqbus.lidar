import pyqtgraph as pg
import time
import datetime
import sys
import traceback as tb

from inqbus.lidar.scc_gui.log import logger

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

    # def tickStrings(self, values, scale, spacing):
    #     strns = []
    #     datavalues = []
    #     for value in values:
    #         if value < self.axis_data.shape[0]:
    #             datavalues.append(self.axis_data[int(value)])
    #     try:
    #         min_value = min(datavalues)
    #     except BaseException:
    #         logger.error("Exception: %s" % sys.exc_info()[0])
    #         logger.error("Traceback: %s" % tb.format_exc())
    #         min_value = self.axis_data[0]
    #     try:
    #         max_value = max(datavalues)
    #     except BaseException:
    #         logger.error("Exception: %s" % sys.exc_info()[0])
    #         logger.error("Traceback: %s" % tb.format_exc())
    #         max_value = self.axis_data[-1]
    #
    #     rng = abs(max_value - min_value)
    #
    #     if rng < KILOMETER_LABEL_RANGE:
    #         for x in datavalues:
    #             try:
    #                 strns.append(str(round(x, 3)))
    #             except BaseException:
    #                 strns.append('')
    #         label = 'm'
    #     else:
    #         # TODO: Sometimes single values are displayed as meter
    #         for x in datavalues:
    #             try:
    #                 strns.append(str(round(x / 1000., 2)))
    #             except BaseException:
    #                 strns.append('')
    #         label = 'km'
    #
    #     self.setLabel(text=label)
    #     return strns

    def setRange(self, mn, mx):
        if self.axis_data is None:
            return super(HeightAxis, self).setRange(mn, mx)
        size = self.axis_data.size
        if int(mn) > size:
            mn_new = self.calculate_over_end(int(mn))
        else:
            mn_new = self.axis_data[int(mn)]

        if int(mx) > size:
            mx_new = self.calculate_over_end(int(mx))
        else:
            mx_new = self.axis_data[int(mx)]

        rng = abs(mx_new-mn_new)

        if rng == 0.0:
            return
        elif rng < KILOMETER_LABEL_RANGE:
            label = 'm'
        else:
            label = 'km'
            mx_new = mx_new / 1000.0
            mn_new = mn_new / 1000.0
        self.setLabel(text=label)
        return super(HeightAxis, self).setRange(mn_new, mx_new)

    def calculate_over_end(self, mn):
        size = self.axis_data.size
        last_entry = self.axis_data[-1]
        first_entry = self.axis_data[0]
        distance = (last_entry-first_entry) / size
        offset_index = mn - size
        res = distance * offset_index + last_entry
        return res

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
