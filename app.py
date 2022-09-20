from .base import EOmapsWindow, EOmapsCanvas
from . import utils

import sys

from eomaps import Maps

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

import matplotlib.pyplot as plt
plt.ioff()


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


from PyQt5.QtWidgets import QDesktopWidget

class MainWindow(EOmapsWindow):

    def __init__(self, *args, crs=None, m=None, **kwargs):
        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        canvas = MyMap(self, width=12, height=8, dpi=72, crs=crs, m=m)

        super().__init__(eomaps_canvas = canvas, *args, **kwargs)
        self.setWindowTitle("EOmaps QT embedding example")

        tabs = utils.ControlTabs(parent=self)

        self.menu_widget = QtWidgets.QWidget()
        menu_layout = QtWidgets.QVBoxLayout()

        logo = QtGui.QPixmap("logo.png")
        logolabel = QtWidgets.QLabel()
        logolabel.setMaximumHeight(30)
        logolabel.setAlignment(Qt.AlignBottom|Qt.AlignRight)
        logolabel.setPixmap(logo.scaled(logolabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))


        from .utils import ShowLayerWidget
        showlayer = ShowLayerWidget(m = self.m)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(showlayer)
        self.toolbar.addWidget(self.b_enlarge)
        self.toolbar.addWidget(self.b_close)
        self.toolbar.setAllowedAreas(Qt.TopToolBarArea|Qt.BottomToolBarArea)

        self.addToolBar(self.toolbar)

        tabs.setContentsMargins(5, 5, 5, 5)


        menu_layout.addWidget(tabs)
        self.menu_widget.setLayout(menu_layout)

        self.menu_dock = QtWidgets.QDockWidget(flags=Qt.Window)
        self.menu_dock.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
                                   QtWidgets.QDockWidget.DockWidgetMovable)
        self.menu_dock.setAllowedAreas(Qt.TopDockWidgetArea|Qt.BottomDockWidgetArea)
        self.menu_dock.setWidget(self.menu_widget)
        self.menu_dock.setTitleBarWidget(QtWidgets.QLabel(""))

        #self.addDockWidget(Qt.BottomDockWidgetArea, self.menu_dock)

        menu_toolbar = QtWidgets.QDockWidget(flags=Qt.Window)
        menu_toolbar.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
                                   QtWidgets.QDockWidget.DockWidgetMovable)
        menu_toolbar.setAllowedAreas(Qt.TopDockWidgetArea|Qt.BottomDockWidgetArea)
        menu_toolbar.setWidget(self.menu_widget)
        menu_toolbar.setTitleBarWidget(QtWidgets.QLabel(""))

        self.addDockWidget(Qt.BottomDockWidgetArea, menu_toolbar)


        self.show()
        self.resize(1200,900)
        self.center()
        #menu_dock.setFloating(True)

        #self.setStyleSheet("QMainWindow::separator {width: 1px; border: none;}")

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @property
    def m(self):
        # the EOmaps maps-object
        return self.canvas.m

def run(m=None):
    app = QtWidgets.QApplication(sys.argv)
    logo = QtGui.QIcon("logo_rect.png")
    app.setWindowIcon(logo)
    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")

    # Now use a palette to switch to dark colors:
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
