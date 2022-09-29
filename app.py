from .base import EOmapsWindow, EOmapsCanvas, ResizableWindow
from . import utils

import sys

from pathlib import Path
iconpath = Path(__file__).parent / "icons"

from eomaps import Maps

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

# import matplotlib.pyplot as plt
# plt.ioff()

# import matplotlib
# matplotlib.use("agg")


class MyMap(EOmapsCanvas):
    def __init__(self, *args, m=None, **kwargs):
        self._m = m

        super().__init__(*args, **kwargs)

    def setup_map(self, width, height, dpi, crs):
        if self._m is not None:
            return self._m

        # initialize EOmaps Maps object
        m = Maps(figsize=(width, height),
                 dpi=dpi,
                 crs=crs,
                 layer="default")

        m.add_feature.preset.coastline()

        try:
            m.add_wms.OpenStreetMap.add_layer.default(layer="OSM")
            m.add_wms.OpenStreetMap.add_layer.stamen_watercolor(layer="OSM watercolor")
            m.add_wms.ESA_WorldCover.add_layer.WORLDCOVER_2020_MAP(layer="ESA WorldCover")

        except Exception:
            print("WebMap layers could not be added...")
            pass

        m.all.cb.click.attach.annotate(modifier=1)

        return m



class EOmaps_titlebar(QtWidgets.QToolBar):
    def __init__(self, *args, m=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.m = m

        layout = QtWidgets.QHBoxLayout()

        logo = QtGui.QPixmap(str(iconpath / "logo.png"))
        logolabel = QtWidgets.QLabel()
        logolabel.setMaximumHeight(25)
        logolabel.setAlignment(Qt.AlignBottom|Qt.AlignRight)
        logolabel.setPixmap(logo.scaled(logolabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))



        from .utils import ShowLayerWidget
        from .layer import AutoUpdateLayerMenuButton
        #showlayer = ShowLayerWidget(m = self.m)
        showlayer = AutoUpdateLayerMenuButton(m=self.m)


        self.transparentQ = QtWidgets.QToolButton()
        self.transparentQ.setStyleSheet("border:none")
        self.transparentQ.setToolTip("Make window semi-transparent.")
        self.transparentQ.setIcon(QtGui.QIcon(str(iconpath / "eye_closed.png")))

        space = QtWidgets.QWidget()
        space.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.addWidget(self.transparentQ)
        self.addWidget(space)
        self.addWidget(showlayer)
        self.addWidget(logolabel)

        self.setMovable(False)
        self.setStyleSheet("border: none; spacing:20px;")
        self.setContentsMargins(5, 0, 5,5)


class transparentWindow(ResizableWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.out_alpha = 0.25
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Dialog|Qt.WindowStaysOnTopHint)

    def focusInEvent(self, e):
        self.setWindowOpacity(1)
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        if not self.isActiveWindow():
            self.setWindowOpacity(self.out_alpha)
        super().focusInEvent(e)



from PyQt5.QtWidgets import QDesktopWidget

class MainWindow(EOmapsWindow):

    def __init__(self, *args, crs=None, m=None, **kwargs):
        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.

        if m is None:
            width = 12
            height = 8
            dpi = 72
        else:
            width = m.figure.f.get_figwidth()
            height = m.figure.f.get_figheight()
            dpi = m.figure.f.dpi

        canvas = MyMap(self, width=width, height=height, dpi=dpi, crs=crs, m=m)

        super().__init__(eomaps_canvas = canvas, *args, **kwargs)
        self.setWindowTitle("EOmaps QT embedding example")

        tabs = utils.ControlTabs(parent=self)



        b_showhide = QtWidgets.QToolButton()
        b_showhide.setIcon(QtGui.QIcon(str(iconpath / "logo.png")))
        b_showhide.clicked.connect(self.cb_showhide)
        b_showhide.setAutoRaise(True)


        self.menu_window = transparentWindow(flags=Qt.Window)
        menu_layout = QtWidgets.QVBoxLayout()
        tabs.setMouseTracking(True)


        self.toolbar.addSeparator()
        self.toolbar.addWidget(b_showhide)

        self.toolbar.addWidget(self.b_enlarge)
        self.toolbar.addWidget(self.b_close)

        self.toolbar.setMovable(False)
        self.setStyleSheet("border: none; spacing:5px;")

        #self.toolbar.setAllowedAreas(Qt.TopToolBarArea|Qt.BottomToolBarArea)

        self.addToolBar(self.toolbar)



        self.titlebar = EOmaps_titlebar(m=self.m)
        self.titlebar.transparentQ.clicked.connect(self.cb_transparentQ)



        self.menu_window.addToolBar(self.titlebar)
        # prevent context-menu's from appearing to avoid the "hide toolbar"
        # context menu when right-clicking the toolbar
        self.menu_window.setContextMenuPolicy(Qt.NoContextMenu)

        menu_layout.addWidget(tabs)

        sizegrip = QtWidgets.QSizeGrip(self.menu_window)
        menu_layout.addWidget(sizegrip, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)

        menu_widget = QtWidgets.QWidget()
        menu_widget.setLayout(menu_layout)

        self.menu_window.setCentralWidget(menu_widget)
        #self.menu_dock = transparentWindow(flags=Qt.Window)
        # self.menu_dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
        #                            QtWidgets.QDockWidget.DockWidgetMovable)
        # self.menu_dock.setAllowedAreas(Qt.TopDockWidgetArea|Qt.BottomDockWidgetArea)
        #self.menu_dock.setWidget(self.menu_widget)

        #self.titlebar = EOmaps_titlebar(m=self.m)
        #self.menu_dock.addToolBar(self.titlebar)


        #self.menu_dock.setTitleBarWidget(self.titlebar)

        # self.addDockWidget(Qt.BottomDockWidgetArea, self.menu_dock)

        # self.menu_dock.topLevelChanged.connect(self.toplevelchanged)







        # TODO this prevents resizing of the figure!!
        # keep the size fixed when docking widgets
        # sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
        #                                    QtWidgets.QSizePolicy.Fixed)
        # self.canvas.setSizePolicy(sizePolicy)

        #self.menu_window.show()

        self.show()
        self.activateWindow()

        # if m is None:
        #     self.resize(1200,900)
        # else:
        #     self.menu_dock.setFloating(True)

        self.center()

        self.setAnimated(False)


        #self.setStyleSheet("QMainWindow::separator {width: 1px; border: none;}")

        #self.titlebar.transparentQ.clicked.connect(self.cb_transparentQ)


    def cb_showhide(self):
        if self.menu_window.isVisible():
            self.menu_window.hide()
        else:
            self.menu_window.show()

    def cb_transparentQ(self):
        if self.menu_window.out_alpha == 1:
            self.menu_window.out_alpha = 0.25
            self.menu_window.setFocus()
            self.titlebar.transparentQ.setIcon(QtGui.QIcon(str(iconpath / "eye_closed.png")))

        else:
            self.menu_window.out_alpha = 1
            self.menu_window.setFocus()
            self.titlebar.transparentQ.setIcon(QtGui.QIcon(str(iconpath / "eye_open.png")))


    # def toplevelchanged(self):
    #     # TODO this does not yet work!!
    #     print("level changed", self.canvas.width(), self.canvas.height())
    #     sh = self.layout.sizeHint()
    #     dsh = self.menu_dock.sizeHint()

    #     sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
    #                                        QtWidgets.QSizePolicy.Fixed)
    #     self.canvas.setSizePolicy(sizePolicy)


    #     if self.menu_dock.isFloating():
    #         self.resize(self.width(), sh.height())
    #     else:
    #         self.resize(self.width(), self.height() + dsh.height())

    #     sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
    #                                        QtWidgets.QSizePolicy.Expanding)
    #     self.canvas.setSizePolicy(sizePolicy)


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @property
    def m(self):
        # the EOmaps maps-object
        return self.canvas.m


    def focusInEvent(self, e):
        self.menu_window.show()
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        self.menu_window.show()
        super().focusInEvent(e)




def run(m=None):
    app = QtWidgets.QApplication(sys.argv)
    logo = QtGui.QIcon(str(iconpath / "logo.png"))
    app.setWindowIcon(logo)
    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")

    # # Now use a palette to switch to dark colors:
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.WindowText, Qt.white)
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ToolTipBase, Qt.black)
    palette.setColor(QtGui.QPalette.ToolTipText, Qt.white)
    palette.setColor(QtGui.QPalette.Text, Qt.white)
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ButtonText, Qt.white)
    palette.setColor(QtGui.QPalette.BrightText, Qt.red)
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.HighlightedText, Qt.black)


    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ToolTipText, Qt.white)

    app.setPalette(palette)


    w = MainWindow(m=m)
    w.show()
    #sys.exit(app.exec_())


if __name__ == "__main__":
    run()
