import os
import weakref

import numpy as np
import pyqtgraph as pg
from PyQt5 import uic
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from pyqtgraph.graphicsItems.ViewBox.ViewBoxMenu import ViewBoxMenu

from inqbus.lidar.scc_gui import PROJECT_PATH
from inqbus.lidar.scc_gui.configs.base_config import resource_path

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)


class RegionMenu(QtGui.QMenu):
    pass


class LimitsViewBoxMenu(ViewBoxMenu):

    def __init__(self, view):
        QtGui.QMenu.__init__(self)

        # keep weakref to view to avoid circular reference (don't know why, but
        # this prevents the ViewBox from being collected)
        self.view = weakref.ref(view)
        self.valid = False  # tells us whether the ui needs to be updated
        # weakrefs to all views listed in the link combos
        self.viewMap = weakref.WeakValueDictionary()

        self.setTitle("ViewBox options")
        self.viewAll = QtGui.QAction("View All", self)
        self.viewAll.triggered.connect(self.autoRange)
        self.addAction(self.viewAll)

        self.axes = []
        self.ctrl = []
        self.widgetGroups = []
        self.dv = QtGui.QDoubleValidator(self)
        for axis in 'XY':

            w = ui = uic.loadUi(
                resource_path(
                    os.path.join(
                        PROJECT_PATH,
                        'UI/axisCtrlTemplate.ui')))
            sub_a = QtGui.QWidgetAction(self)
            sub_a.setDefaultWidget(w)

            a = self.addMenu("%s Axis" % axis)
            a.addAction(sub_a)

            self.axes.append(a)
            self.ctrl.append(ui)

            connects = [
                (ui.mouseCheck.toggled, 'MouseToggled'),
                (ui.manualRadio.clicked, 'ManualClicked'),
                (ui.minText.editingFinished, 'MinTextChanged'),
                (ui.maxText.editingFinished, 'MaxTextChanged'),
                (ui.minText_2.editingFinished, 'MinTextChanged_2'),
                (ui.maxText_2.editingFinished, 'MaxTextChanged_2'),
                (ui.cbLimits.stateChanged, 'cbLimitsChanged'),
                (ui.autoRadio.clicked, 'AutoClicked'),
                (ui.autoPercentSpin.valueChanged, 'AutoSpinChanged'),
                (ui.linkCombo.currentIndexChanged, 'LinkComboChanged'),
                (ui.autoPanCheck.toggled, 'AutoPanToggled'),
                (ui.visibleOnlyCheck.toggled, 'VisibleOnlyToggled')
            ]

            for sig, fn in connects:
                sig.connect(getattr(self, axis.lower() + fn))

        self.ctrl[0].invertCheck.toggled.connect(self.xInvertToggled)
        self.ctrl[1].invertCheck.toggled.connect(self.yInvertToggled)

        self.leftMenu = QtGui.QMenu("Mouse Mode")
        group = QtGui.QActionGroup(self)

        # This does not work! QAction _must_ be initialized with a permanent
        # object as the parent or else it may be collected prematurely.

        pan = QtGui.QAction("3 button", self.leftMenu)
        zoom = QtGui.QAction("1 button", self.leftMenu)
        self.leftMenu.addAction(pan)
        self.leftMenu.addAction(zoom)
        pan.triggered.connect(self.set3ButtonMode)
        zoom.triggered.connect(self.set1ButtonMode)

        pan.setCheckable(True)
        zoom.setCheckable(True)
        pan.setActionGroup(group)
        zoom.setActionGroup(group)
        self.mouseModes = [pan, zoom]
        self.addMenu(self.leftMenu)

        self.view().sigStateChanged.connect(self.viewStateChanged)

        self.updateState()

    def updateState(self):
        # Something about the viewbox has changed; update the menu GUI

        state = self.view().getState(copy=False)
        if state['mouseMode'] == ViewBox.PanMode:
            self.mouseModes[0].setChecked(True)
        else:
            self.mouseModes[1].setChecked(True)

        limits = state['limits']
        if limits['xLimits']:
            if limits['xLimits'][0]:
                self.ctrl[0].minText_2.setText("%0.5g" % limits['xLimits'][0])
            if limits['xLimits'][1]:
                self.ctrl[0].maxText_2.setText("%0.5g" % limits['xLimits'][1])
        if limits['yLimits']:
            if limits['yLimits'][0]:
                self.ctrl[1].minText_2.setText("%0.5g" % limits['yLimits'][0])
            if limits['yLimits'][1]:
                self.ctrl[1].maxText_2.setText("%0.5g" % limits['yLimits'][1])

        for i in [0, 1]:  # x, y
            tr = state['targetRange'][i]
            self.ctrl[i].minText.setText("%0.5g" % tr[0])
            self.ctrl[i].maxText.setText("%0.5g" % tr[1])

            if state['autoRange'][i] is not False:
                self.ctrl[i].autoRadio.setChecked(True)
                if state['autoRange'][i] is not True:
                    self.ctrl[i].autoPercentSpin.setValue(
                        state['autoRange'][i] * 100)
            else:
                self.ctrl[i].manualRadio.setChecked(True)
            self.ctrl[i].mouseCheck.setChecked(state['mouseEnabled'][i])

            # Update combo to show currently linked view
            c = self.ctrl[i].linkCombo
            c.blockSignals(True)
            try:
                view = state['linkedViews'][i]  # will always be string or None
                if view is None:
                    view = ''

                ind = c.findText(view)

                if ind == -1:
                    ind = 0
                c.setCurrentIndex(ind)
            finally:
                c.blockSignals(False)

            self.ctrl[i].autoPanCheck.setChecked(state['autoPan'][i])
            self.ctrl[i].visibleOnlyCheck.setChecked(
                state['autoVisibleOnly'][i])
            xy = ['x', 'y'][i]
            self.ctrl[i].invertCheck.setChecked(
                state.get(xy + 'Inverted', False))

        self.valid = True

    def xMinTextChanged_2(self):
        # ToDo: Error! We are changing only one of many views
        self.ctrl[0].cbLimits.setChecked(True)
        self.view().setLimits(xMin=float(self.ctrl[0].minText_2.text()))

    def yMinTextChanged_2(self):
        self.ctrl[1].cbLimits.setChecked(True)
        self.view().setLimits(yMin=float(self.ctrl[0].minText_2.text()))

    def xMaxTextChanged_2(self):
        self.ctrl[0].cbLimits.setChecked(True)
        self.view().setLimits(xMax=float(self.ctrl[0].maxText_2.text()))

    def yMaxTextChanged_2(self):
        self.ctrl[1].cbLimits.setChecked(True)
        self.view().setLimits(yMax=float(self.ctrl[0].maxText_2.text()))

    def xcbLimitsChanged(self):
        if self.ctrl[0].cbLimits.isChecked():
            self.view().setLimits(
                xMin=float(
                    self.ctrl[0].minText_2.text()), xMax=float(
                    self.ctrl[0].maxText_2.text()), )
        else:
            self.view().setLimits(xMin=None)
            self.view().setLimits(xMax=None)

    def ycbLimitsChanged(self):
        if self.ctrl[1].cbLimits.isChecked():
            self.view().setLimits(
                yMin=float(
                    self.ctrl[1].minText_2.text()), yMax=float(
                    self.ctrl[1].maxText_2.text()), )
        else:
            self.view().setLimits(yMin=None)
            self.view().setLimits(yMax=None)


class FixedViewBox(pg.ViewBox):
    """
    A viewbox that has truely fixed axis
    """

    def __init__(self, plot, *args, **kwargs):
        super(FixedViewBox, self).__init__(*args, **kwargs)
        self.menu = LimitsViewBoxMenu(self)
        self.plot = plot

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton and self.menuEnabled():
            super(FixedViewBox, self).mouseClickEvent(ev)
        elif ev.button() == QtCore.Qt.MiddleButton:
            self.middle_button_clicked(ev)

    def middle_button_clicked(self, ev):
        ev.accept()

        self.plot.add_region(ev.scenePos())

    def setRange(
            self,
            rect=None,
            xRange=None,
            yRange=None,
            padding=None,
            update=True,
            disableAutoRange=True):
        """
        Set the visible range of the ViewBox.
        Must specify at least one of *rect*, *xRange*, or *yRange*.

        ================== =====================================================================
        **Arguments:**
        *rect*             (QRectF) The full range that should be visible in the view box.
        *xRange*           (min,max) The range that should be visible along the x-axis.
        *yRange*           (min,max) The range that should be visible along the y-axis.
        *padding*          (float) Expand the view by a fraction of the requested range.
                           By default, this value is set between 0.02 and 0.1 depending on
                           the size of the ViewBox.
        *update*           (bool) If True, update the range of the ViewBox immediately.
                           Otherwise, the update is deferred until before the next render.
        *disableAutoRange* (bool) If True, auto-ranging is diabled. Otherwise, it is left
                           unchanged.
        ================== =====================================================================

        """
        changes = {}   # axes
        setRequested = [False, False]

        if rect is not None:
            changes = {0: [rect.left(), rect.right()], 1: [
                rect.top(), rect.bottom()]}
            setRequested = [True, True]
        if xRange is not None:
            changes[0] = xRange
            setRequested[0] = True
        if yRange is not None:
            changes[1] = yRange
            setRequested[1] = True

        if len(changes) == 0:
            print(rect)
            raise Exception(
                "Must specify at least one of rect, xRange, or yRange. (gave rect=%s)" % str(
                    type(rect)))

        # Update axes one at a time
        changed = [False, False]
        for ax, range in changes.items():
            mn = min(range)
            mx = max(range)

            # If we requested 0 range, try to preserve previous scale.
            # Otherwise just pick an arbitrary scale.
            if mn == mx:
                dy = self.state['viewRange'][ax][1] - \
                    self.state['viewRange'][ax][0]
                if dy == 0:
                    dy = 1
                mn -= dy * 0.5
                mx += dy * 0.5
                xpad = 0.0

            # Make sure no nan/inf get through
            if not all(np.isfinite([mn, mx])):
                raise Exception(
                    "Cannot set range [%s, %s]" %
                    (str(mn), str(mx)))

            # Apply padding
            if padding is None:
                xpad = self.suggestPadding(ax)
            else:
                xpad = padding
            p = (mx - mn) * xpad
            mn -= p
            mx += p

            # Set target range
            if self.state['targetRange'][ax] != [mn, mx]:
                self.state['targetRange'][ax] = [mn, mx]
                changed[ax] = True

        # Update viewRange to match targetRange as closely as possible while
        # accounting for aspect ratio constraint
        lockX, lockY = setRequested
        if lockX and lockY:
            lockX = False
            lockY = False
        self.updateViewRange(lockX, lockY)

        # Disable auto-range for each axis that was requested to be set
        if disableAutoRange:
            xOff = False if setRequested[0] else None
            yOff = False if setRequested[1] else None
            self.enableAutoRange(x=xOff, y=yOff)
            changed.append(True)

        # If nothing has changed, we are done.
        if any(changed):

            self.sigStateChanged.emit(self)

            # Update target rect for debugging
            if self.target.isVisible():
                self.target.setRect(
                    self.mapRectFromItem(
                        self.childGroup,
                        self.targetRect()))

        # If ortho axes have auto-visible-only, update them now
        # Note that aspect ratio constraints and auto-visible probably do not
        # work together..
        if changed[0] and self.state['autoVisibleOnly'][1] and (
                self.state['autoRange'][0] is not False):
            self._autoRangeNeedsUpdate = True
        elif changed[1] and self.state['autoVisibleOnly'][0] and (self.state['autoRange'][1] is not False):
            self._autoRangeNeedsUpdate = True

    def updateViewRange(self, forceX=False, forceY=False):
        # Update viewRange to match targetRange as closely as possible, given
        # aspect ratio constraints. The *force* arguments are used to indicate
        # which axis (if any) should be unchanged when applying constraints.
        viewRange = [
            self.state['targetRange'][0][:],
            self.state['targetRange'][1][:]]
        changed = [False, False]

        #-------- Make correction for aspect ratio constraint ----------

        # aspect is (widget w/h) / (view range w/h)
        aspect = self.state['aspectLocked']  # size ratio / view ratio
        tr = self.targetRect()
        bounds = self.rect()
        if aspect is not False and 0 not in [
                aspect, tr.height(), bounds.height(), bounds.width()]:

            # This is the view range aspect ratio we have requested
            targetRatio = tr.width() / tr.height() if tr.height() != 0 else 1
            # This is the view range aspect ratio we need to obey aspect
            # constraint
            viewRatio = (bounds.width() / bounds.height()
                         if bounds.height() != 0 else 1) / aspect
            viewRatio = 1 if viewRatio == 0 else viewRatio

            # Decide which range to keep unchanged
            if forceX:
                ax = 0
            elif forceY:
                ax = 1
            else:
                # if we are not required to keep a particular axis unchanged,
                # then make the entire target range visible
                ax = 0 if targetRatio > viewRatio else 1

            if ax == 0:
                # view range needs to be taller than target
                dy = 0.5 * (tr.width() / viewRatio - tr.height())
                if dy != 0:
                    changed[1] = True
                viewRange[1] = [
                    self.state['targetRange'][1][0] - dy,
                    self.state['targetRange'][1][1] + dy]
            else:
                # view range needs to be wider than target
                dx = 0.5 * (tr.height() * viewRatio - tr.width())
                if dx != 0:
                    changed[0] = True
                viewRange[0] = [
                    self.state['targetRange'][0][0] - dx,
                    self.state['targetRange'][0][1] + dx]

        # ----------- Make corrections for view limits -----------

        limits = (
            self.state['limits']['xLimits'],
            self.state['limits']['yLimits'])
        minRng = [
            self.state['limits']['xRange'][0],
            self.state['limits']['yRange'][0]]
        maxRng = [
            self.state['limits']['xRange'][1],
            self.state['limits']['yRange'][1]]

        for axis in [0, 1]:
            if limits[axis][0] is None and limits[axis][1] is None and minRng[axis] is None and maxRng[axis] is None:
                continue

            # max range cannot be larger than bounds, if they are given
            if limits[axis][0] is not None and limits[axis][1] is not None:
                if maxRng[axis] is not None:
                    maxRng[axis] = min(
                        maxRng[axis], limits[axis][1] - limits[axis][0])
                else:
                    maxRng[axis] = limits[axis][1] - limits[axis][0]

            # Apply xRange, yRange
            diff = viewRange[axis][1] - viewRange[axis][0]
            if maxRng[axis] is not None and diff > maxRng[axis]:
                delta = maxRng[axis] - diff
                changed[axis] = True
            elif minRng[axis] is not None and diff < minRng[axis]:
                delta = minRng[axis] - diff
                changed[axis] = True
            else:
                delta = 0

            viewRange[axis][0] -= delta / 2.
            viewRange[axis][1] += delta / 2.

            # Apply xLimits, yLimits
            mn, mx = limits[axis]
            if mn is not None and viewRange[axis][0] < mn:
                delta = mn - viewRange[axis][0]
                viewRange[axis][0] += delta
                viewRange[axis][1] += delta
                changed[axis] = True
            elif mx is not None and viewRange[axis][1] < mx:
                delta = mx - viewRange[axis][1]
                viewRange[axis][0] += delta
                viewRange[axis][1] += delta
                changed[axis] = True

        changed = [(viewRange[i][0] != self.state['viewRange'][i][0]) or (
            viewRange[i][1] != self.state['viewRange'][i][1]) for i in (0, 1)]
        self.state['viewRange'] = viewRange

        # emit range change signals
        if changed[0]:
            self.sigXRangeChanged.emit(self, tuple(self.state['viewRange'][0]))
        if changed[1]:
            self.sigYRangeChanged.emit(self, tuple(self.state['viewRange'][1]))

        if any(changed):
            self.sigRangeChanged.emit(self, self.state['viewRange'])
            self.update()
            self._matrixNeedsUpdate = True

            # Inform linked views that the range has changed
            for ax in [0, 1]:
                if not changed[ax]:
                    continue
                link = self.linkedView(ax)
                if link is not None:
                    link.linkedViewChanged(self, ax)
