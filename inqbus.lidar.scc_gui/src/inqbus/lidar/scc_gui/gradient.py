import numpy as np
import pyqtgraph.functions as fn
from pyqtgraph import GradientEditorItem
from pyqtgraph.Qt import QtGui


class Gradient(GradientEditorItem):
    """
    Custom Gradient with min/manx Values.
    """

    def __init__(self):
        self.edge_colors = None
        super(Gradient, self).__init__()

    def getLookupTable(self, nPts, alpha=None):
        """
        Return an RGB(A) lookup table (ndarray).

        ==============  ============================================================================
        **Arguments:**
        nPts            The number of points in the returned lookup table.
        alpha           True, False, or None - Specifies whether or not alpha values are included
                        in the table.If alpha is None, alpha will be automatically determined.
        ==============  ============================================================================
        """
        if alpha is None:
            alpha = self.usesAlpha()
        if alpha:
            table = np.empty((nPts, 4), dtype=np.ubyte)
        else:
            table = np.empty((nPts, 3), dtype=np.ubyte)

        if self.edge_colors:
            for i in range(nPts)[1:-2]:
                x = float(i) / (nPts - 3)
                color = self.getColor(x, toQColor=False)
                table[i] = color[:table.shape[1]]
            color = self.edge_colors[0]
            table[0] = color[:table.shape[1]]
            color = self.edge_colors[1]
            table[nPts - 1] = color[:table.shape[1]]
        else:
            for i in range(nPts):
                x = float(i) / (nPts - 1)
                color = self.getColor(x, toQColor=False)
                table[i] = color[:table.shape[1]]

        return table

    def restoreState(self, state):
        """
        Restore the gradient specified in state.

        ==============  ====================================================================
        **Arguments:**
        state           A dictionary with same structure as those returned by
                        :func:`saveState <pyqtgraph.GradientEditorItem.saveState>`

                        Keys must include:

                            - 'mode': hsv or rgb
                            - 'ticks': a list of tuples (pos, (r,g,b,a))
        ==============  ====================================================================
        """
        if 'edge_colors' in state:
            self.edge_colors = state['edge_colors']
        else:
            self.below_above_color = None
        self.setColorMode(state['mode'])
        for t in list(self.ticks.keys()):
            self.removeTick(t, finish=False)
        for t in state['ticks']:
            c = QtGui.QColor(*t[1])
            self.addTick(t[0], c, finish=False)
        self.updateGradient()
        self.sigGradientChangeFinished.emit(self)

    def isLookupTrivial(self):
        """Return True if the gradient has exactly two stops in it: black at 0.0 and white at 1.0"""
        ticks = self.listTicks()
        if self.edge_colors:
            return False
        if len(ticks) != 2:
            return False
        if ticks[0][1] != 0.0 or ticks[1][1] != 1.0:
            return False
        c1 = fn.colorTuple(ticks[0][0].color)
        c2 = fn.colorTuple(ticks[1][0].color)
        if c1 != (0, 0, 0, 255) or c2 != (255, 255, 255, 255):
            return False
        return True
