import collections

import numpy as np
import pyqtgraph.debug as debug
import pyqtgraph.functions as fn
from pyqtgraph import rescaleData, applyLookupTable
from pyqtgraph.Point import Point
from pyqtgraph.Qt import QtCore
from pyqtgraph.graphicsItems.ImageItem import ImageItem


def makeARGB(data, lut=None, levels=None, scale=None, useRGBA=False):
    """
    Convert an array of values into an ARGB array suitable for building QImages, OpenGL textures, etc.

    Returns the ARGB array (values 0-255) and a boolean indicating whether there is alpha channel data.
    This is a two stage process:

        1) Rescale the data based on the values in the *levels* argument (min, max).
        2) Determine the final output by passing the rescaled values through a lookup table.

    Both stages are optional.

    ============== ==================================================================================
    **Arguments:**
    data           numpy array of int/float types. If
    levels         List [min, max]; optionally rescale data before converting through the
                   lookup table. The data is rescaled such that min->1 and max->*scale*::-1

                      rescaled = (clip(data, min, max) - min) * (*scale* / (max - min))

                   It is also possible to use a 2D (N,2) array of values for levels. In this case,
                   it is assumed that each pair of min,max values in the levels array should be
                   applied to a different subset of the input data (for example, the input data may
                   already have RGB values and the levels are used to independently scale each
                   channel). The use of this feature requires that levels.shape[0] == data.shape[-1].
    scale          The maximum value to which data will be rescaled before being passed through the
                   lookup table (or returned if there is no lookup table). By default this will
                   be set to the length of the lookup table, or 256 is no lookup table is provided.
                   For OpenGL color specifications (as in GLColor4f) use scale=1.0
    lut            Optional lookup table (array with dtype=ubyte).
                   Values in data will be converted to color by indexing directly from lut.
                   The output data shape will be input.shape + lut.shape[1:].

                   Note: the output of makeARGB will have the same dtype as the lookup table, so
                   for conversion to QImage, the dtype must be ubyte.

                   Lookup tables can be built using GradientWidget.
    useRGBA        If True, the data is returned in RGBA order (useful for building OpenGL textures).
                   The default is False, which returns in ARGB order for use with QImage
                   (Note that 'ARGB' is a term used by the Qt documentation; the _actual_ order
                   is BGRA).
    ============== ==================================================================================
    """
    profile = debug.Profiler()

    if lut is not None and not isinstance(lut, np.ndarray):
        lut = np.array(lut)
    if levels is not None and not isinstance(levels, np.ndarray):
        levels = np.array(levels)

    if levels is not None:
        if levels.ndim == 1:
            if len(levels) != 2:
                raise Exception('levels argument must have length 2')
        elif levels.ndim == 2:
            if lut is not None and lut.ndim > 1:
                raise Exception(
                    'Cannot make ARGB data when bot levels and lut have ndim > 2')
            if levels.shape != (data.shape[-1], 2):
                raise Exception('levels must have shape (data.shape[-1], 2)')
        else:
            print(levels)
            raise Exception("levels argument must be 1D or 2D.")

    profile()

    if scale is None:
        if lut is not None:
            scale = lut.shape[0]
        else:
            scale = 255.

    # Apply levels if given
    if levels is not None:

        if isinstance(levels, np.ndarray) and levels.ndim == 2:
            # we are going to rescale each channel independently
            if levels.shape[0] != data.shape[-1]:
                raise Exception(
                    "When rescaling multi-channel data, there must be the same number of levels as channels (data.shape[-1] == levels.shape[0])")
            newData = np.empty(data.shape, dtype=int)
            for i in range(data.shape[-1]):
                minVal, maxVal = levels[i]
                if minVal == maxVal:
                    maxVal += 1e-16
                newData[..., i] = rescaleData(
                    data[..., i], scale / (maxVal - minVal), minVal, dtype=int)
            data = newData
        else:
            minVal, maxVal = levels

            # Change min and max values to achieve a unused bin left and right:
            fact = (scale - 2.) / (maxVal - minVal)
            offset = minVal - (maxVal - minVal) / (scale - 2.) - 0.1

            data = rescaleData(data, fact, offset, dtype=int)

    profile()

    # apply LUT if given
    if lut is not None:
        data = applyLookupTable(data, lut)
    else:
        if data.dtype is not np.ubyte:
            data = np.clip(data, 0, 255).astype(np.ubyte)

    profile()

    # copy data into ARGB ordered array
    imgData = np.empty(data.shape[:2] + (4,), dtype=np.ubyte)

    profile()

    if useRGBA:
        order = [0, 1, 2, 3]  # array comes out RGBA
    else:
        # for some reason, the colors line up as BGR in the final image.
        order = [2, 1, 0, 3]

    if data.ndim == 2:
        # This is tempting:
        #   imgData[..., :3] = data[..., np.newaxis]
        # ..but it turns out this is faster:
        for i in range(3):
            imgData[..., i] = data
    elif data.shape[2] == 1:
        for i in range(3):
            imgData[..., i] = data[..., 0]
    else:
        for i in range(0, data.shape[2]):
            imgData[..., i] = data[..., order[i]]

    profile()

    if data.ndim == 2 or data.shape[2] == 3:
        alpha = False
        imgData[..., 3] = 255
    else:
        alpha = True

    profile()
    return imgData, alpha


class Image(ImageItem):

    def render(self):
        # Convert data to QImage for display.

        profile = debug.Profiler()
        if self.image is None or self.image.size == 0:
            return
        if isinstance(self.lut, collections.Callable):
            lut = self.lut(self.image)
        else:
            lut = self.lut

        if self.autoDownsample:
            # reduce dimensions of image based on screen resolution
            o = self.mapToDevice(QtCore.QPointF(0, 0))
            x = self.mapToDevice(QtCore.QPointF(1, 0))
            y = self.mapToDevice(QtCore.QPointF(0, 1))
            w = Point(x - o).length()
            h = Point(y - o).length()
            xds = max(1, int(1 / w))
            yds = max(1, int(1 / h))
            image = fn.downsample(self.image, xds, axis=0)
            image = fn.downsample(image, yds, axis=1)
        else:
            image = self.image

        argb, alpha = makeARGB(
            image.transpose(
                (1, 0, 2)[
                    :image.ndim]), lut=lut, levels=self.levels)
        self.qimage = fn.makeQImage(argb, alpha, transpose=False)
