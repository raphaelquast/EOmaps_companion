import sys
import matplotlib
matplotlib.use('Qt5Agg')

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from eomaps import Maps

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QPushButton

from PyQt5.QtCore import Qt, QRectF

from pathlib import Path
# %%

class ResizableWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.press_control = 0

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.catch_cursor = 0
        self.installEventFilter(self)

        self.top_resize_margin = 30

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.HoverMove:
            if self.press_control == 0:
                self.set_cursor(event)

        elif event.type() == QtCore.QEvent.MouseButtonPress:
            self.press_control = 1
            self.press_pos = event.pos()
            self.origin = self.mapToGlobal(event.pos())
            self.ori_geo = self.geometry()

        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            self.press_control = 0
            self.set_cursor(event)

        elif event.type() == QtCore.QEvent.MouseMove:
            if not hasattr(self, "press_pos"):
                pass
            elif self.cursor().shape() != Qt.ArrowCursor:
                self.resizing(self.origin, event, self.ori_geo, self.catch_cursor)
            elif self.catch_cursor == 0:
                if self.isMaximized():
                    # minimize the window and position it centered
                    self.showNormal()
                    self.move(self.press_pos)
                    self.press_pos = QtCore.QPoint(int(self.sizeHint().width()/2), 0)
                else:
                    self.move(self.pos() + (event.pos() - self.press_pos))

        return super().eventFilter(source, event)

    def set_cursor(self, e):

        rect = self.rect()
        top_left = rect.topLeft()
        top_right = rect.topRight()
        bottom_left = rect.bottomLeft()
        bottom_right = rect.bottomRight()
        pos = e.pos()

        # catch top rectangle used for dragging
        if pos in QtCore.QRect(QtCore.QPoint(top_left.x()+5,top_left.y()+5), QtCore.QPoint(top_right.x()-10,top_right.y()+self.top_resize_margin)):
            self.setCursor(Qt.ArrowCursor)
            self.catch_cursor = 0

        # catch if window is maximized and ignore resizing
        elif self.isMaximized():
            self.catch_cursor = -1
            self.setCursor(Qt.ArrowCursor)
            return

        #top catch
        elif pos in QtCore.QRect(QtCore.QPoint(top_left.x()+5,top_left.y()), QtCore.QPoint(top_right.x()-5,top_right.y()+5)):
            self.setCursor(Qt.ArrowCursor)
            self.catch_cursor = 0

        #bottom catch
        elif pos in QtCore.QRect(QtCore.QPoint(bottom_left.x()+5,bottom_left.y()), QtCore.QPoint(bottom_right.x()-5,bottom_right.y()-5)):
            self.setCursor(Qt.SizeVerCursor)
            self.catch_cursor = 2

        #right catch
        elif pos in QtCore.QRect(QtCore.QPoint(top_right.x()-5,top_right.y()+5), QtCore.QPoint(bottom_right.x(),bottom_right.y()-5)):
            self.setCursor(Qt.SizeHorCursor)
            self.catch_cursor = 3

        #left catch
        elif pos in QtCore.QRect(QtCore.QPoint(top_left.x()+5,top_left.y()+5), QtCore.QPoint(bottom_left.x(),bottom_left.y()-5)):
            self.setCursor(Qt.SizeHorCursor)
            self.catch_cursor = 4

        #top_right catch
        elif pos in QtCore.QRect(QtCore.QPoint(top_right.x(),top_right.y()), QtCore.QPoint(top_right.x()-5,top_right.y()+5)):
            self.setCursor(Qt.SizeBDiagCursor)
            self.catch_cursor = 5

        #botom_left catch
        elif pos in QtCore.QRect(QtCore.QPoint(bottom_left.x(),bottom_left.y()), QtCore.QPoint(bottom_left.x()+5,bottom_left.y()-5)):
            self.setCursor(Qt.SizeBDiagCursor)
            self.catch_cursor = 6

        #top_left catch
        elif pos in QtCore.QRect(QtCore.QPoint(top_left.x(),top_left.y()), QtCore.QPoint(top_left.x()+5,top_left.y()+5)):
            self.setCursor(Qt.SizeFDiagCursor)
            self.catch_cursor = 7

        #bottom_right catch
        elif pos in QtCore.QRect(QtCore.QPoint(bottom_right.x(),bottom_right.y()), QtCore.QPoint(bottom_right.x()-5,bottom_right.y()-5)):
            self.setCursor(Qt.SizeFDiagCursor)
            self.catch_cursor = 8

        #default
        else:
            self.catch_cursor = -1
            self.setCursor(Qt.ArrowCursor)

    def resizing(self, ori, e, geo, value):
        if self.isMaximized():
            return

        #top_resize
        if self.catch_cursor == 1:
            last = self.mapToGlobal(e.pos())-ori
            first = geo.height()
            first -= last.y()
            Y = geo.y()
            Y += last.y()

            if first > self.minimumHeight():
                self.setGeometry(geo.x(), Y, geo.width(), first)

        #bottom_resize
        if self.catch_cursor == 2:
            last = self.mapToGlobal(e.pos())-ori
            first = geo.height()
            first += last.y()
            self.resize(geo.width(), first)

        #right_resize
        if self.catch_cursor == 3:
            last = self.mapToGlobal(e.pos())-ori
            first = geo.width()
            first += last.x()
            self.resize(first, geo.height())

        #left_resize
        if self.catch_cursor == 4:
            last = self.mapToGlobal(e.pos())-ori
            first = geo.width()
            first -= last.x()
            X = geo.x()
            X += last.x()

            if first > self.minimumWidth():
                self.setGeometry(X, geo.y(), first, geo.height())

        #top_right_resize
        if self.catch_cursor == 5:
            last = self.mapToGlobal(e.pos())-ori
            first_width = geo.width()
            first_height = geo.height()
            first_Y = geo.y()
            first_width += last.x()
            first_height -= last.y()
            first_Y += last.y()

            if first_height > self.minimumHeight():
                self.setGeometry(geo.x(), first_Y, first_width, first_height)

        #bottom_right_resize
        if self.catch_cursor == 6:
            last = self.mapToGlobal(e.pos())-ori
            first_width = geo.width()
            first_height = geo.height()
            first_X = geo.x()
            first_width -= last.x()
            first_height += last.y()
            first_X += last.x()

            if first_width > self.minimumWidth():
                self.setGeometry(first_X, geo.y(), first_width, first_height)

        #top_left_resize
        if self.catch_cursor == 7:
            last = self.mapToGlobal(e.pos())-ori
            first_width = geo.width()
            first_height = geo.height()
            first_X = geo.x()
            first_Y = geo.y()
            first_width -= last.x()
            first_height -= last.y()
            first_X += last.x()
            first_Y += last.y()

            if first_height > self.minimumHeight() and first_width > self.minimumWidth():
                self.setGeometry(first_X, first_Y, first_width, first_height)

        #bottom_right_resize
        if self.catch_cursor == 8:
            last = self.mapToGlobal(e.pos())-ori
            first_width = geo.width()
            first_height = geo.height()
            first_width += last.x()
            first_height += last.y()

            self.setGeometry(geo.x(), geo.y(), first_width, first_height)


# canvas holding the matplotib figure
class EOmapsCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100, crs=4326):

        # turn interactive mode off since we don't want the figure to appear
        # in a separate window as well
        #plt.ioff()

        self.m = self.setup_map(width, height, dpi, crs)
        # self.m.figure.f.patch.set_facecolor((53/255, 53/255, 53/255))
        # self.m.figure.f.set_edgecolor(".5")
        # self.m.figure.f.set_linewidth(2)
        # self.m.ax.patch.set_color("none")

        super().__init__(self.m.figure.f)

        self.setMinimumSize(100, 100)

        self._args = dict(parent=parent, width=width, height=height, dpi=dpi)

    def setup_map(self, width, height, dpi, crs):
        raise NotImplementedError("setup_map(widht, height, dpi) must be implemented" +
                                  "and it must return an EOmaps.Maps object!")

        # initialize EOmaps Maps object
        m = Maps(figsize=(width, height),
                 dpi=dpi,
                 crs=crs
                 )

        m.add_feature.preset.coastline()

        return m

class FloatingButtonWidget(QtWidgets.QPushButton): #1

    def __init__(self, parent):
        super().__init__(parent)
        self.paddingLeft = 0
        self.paddingTop = 0

    def update_position(self):
        parent_rect = self.parent().size()
        if not parent_rect:
            return

        x = parent_rect.width() - self.width() - self.paddingLeft
        y = self.paddingTop #3
        self.setGeometry(x, y, self.width(), self.height())

    def resizeEvent(self, event): #2
        super().resizeEvent(event)
        self.update_position()


# a splitter that uses the custom splitter handle
class MySplitter(QtWidgets.QSplitter):
    def __init__(self, *args, m=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.m = m
    def createHandle(self):
        return MySplitterHandle(self.orientation(), self)


# create a custom splitterhandle so that we can decect clicks on the splitters
class MySplitterHandle(QtWidgets.QSplitterHandle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layer = None

        m = self.splitter().m
        if "_resize_layer" not in m._get_layers():
            m.add_feature.preset.coastline(layer="_resize_layer")

    def mousePressEvent(self, event):
        m = self.splitter().m
        if event.button() == Qt.RightButton:
            self.layer = m.BM.bg_layer
            m.show_layer("_resize_layer")

        elif event.button() == Qt.LeftButton:
            self.layer = m.BM.bg_layer
            m.show_layer("_resize_layer")

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        m = self.splitter().m

        if event.button() == Qt.RightButton:
            m.show_layer(self.layer)

        elif event.button() == Qt.LeftButton:
            m.show_layer(self.layer)

        super().mousePressEvent(event)


class EOmapsWindow(ResizableWindow):
    def __init__(self, eomaps_canvas, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        self.canvas = eomaps_canvas

        # make sure focus is correctly set so that the map responds to keypress events
        # see https://stackoverflow.com/a/51383190/9703451
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        # focus the map on startup
        self.canvas.setFocus()

        # Create a matplotlib navigation-toolbar object for the map
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setMinimumHeight(30)
        self.toolbar.setMaximumHeight(30)

        # -------------------------
        # a container for nested layouts

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)


        self.split_top = MySplitter(Qt.Vertical, m=self.canvas.m)

        self.split_top.addWidget(self.toolbar)
        self.split_top.addWidget(self.canvas)
        self.layout.addWidget(self.split_top)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        toolbar = QtWidgets.QToolBar()
        # a exit-button (add it as the last object to make sure it's on top)
        self.floatb = FloatingButtonWidget(self)
        self.floatb.setFixedSize(30, 30)
        self.floatb.setText("\u274C")
        self.floatb.setStyleSheet("text-align:top;border:none;")
        self.floatb.clicked.connect(self.close_button_callback)
        self.floatb.move(0,0)

        self.floatb2 = FloatingButtonWidget(self)
        self.floatb2.setFixedSize(30, 30)
        self.floatb2.setText("\u25a0")
        self.floatb2.setStyleSheet("text-align:top;border:none;")
        self.floatb2.clicked.connect(self.maximize_button_callback)
        self.floatb2.paddingLeft = 30

        toolbar.addWidget(self.floatb)
        toolbar.addWidget(self.floatb2)

        toolbar.setFloatable(False)
        toolbar.setMovable(False)

        self.addToolBar(toolbar)

    def resizeEvent(self, event): #2
        super().resizeEvent(event)
        self.floatb.update_position()
        self.floatb2.update_position()


    @property
    def m(self):
        # the EOmaps maps-object
        return self.canvas.m

    def close_button_callback(self):
        self.close()
        # TODO detect if all windows are closed, and if so call sys.exit!
        #sys.exit(0)

    def maximize_button_callback(self):
        if not self.isMaximized():
            self.showMaximized()
        else:
            self.showNormal()
