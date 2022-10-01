from .base import EOmapsWindow, EOmapsCanvas, ResizableWindow
from . import utils

import sys

from pathlib import Path
iconpath = Path(__file__).parent / "icons"

from eomaps import Maps

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from functools import lru_cache


import matplotlib.pyplot as plt
@lru_cache()
def get_cmap_pixmaps():
    # cache the pixmaps for matplotlib colormaps
    # Note: the cache must be cleared if new colormaps are registered!
    # (emit the cmapsChanged signal of MenuWindow to clear the cache)
    cmap_pixmaps = list()
    for cmap in sorted(plt.cm._colormaps()):
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(plt.cm.get_cmap(cmap)._repr_png_(), "png")
        label = QtGui.QIcon()
        label.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)
        label.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
        label.addPixmap(pixmap, QtGui.QIcon.Disabled, QtGui.QIcon.On)
        label.addPixmap(pixmap, QtGui.QIcon.Disabled, QtGui.QIcon.Off)
        cmap_pixmaps.append((label, cmap))

    return cmap_pixmaps


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

        logo = QtGui.QPixmap(str(iconpath / "logo.png"))
        logolabel = QtWidgets.QLabel()
        logolabel.setMaximumHeight(25)
        logolabel.setAlignment(Qt.AlignBottom|Qt.AlignRight)
        logolabel.setPixmap(logo.scaled(logolabel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))


        from .layer import AutoUpdateLayerMenuButton
        showlayer = AutoUpdateLayerMenuButton(m=self.m)

        b_close = QtWidgets.QToolButton()
        b_close.setAutoRaise(True)
        b_close.setFixedSize(25, 25)
        b_close.setText("🞫")
        b_close.clicked.connect(self.close_button_callback)


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
        self.addWidget(b_close)

        self.setMovable(False)

        self.setStyleSheet("QToolBar{border: none; spacing:20px;}"
                           'QToolButton[autoRaise="true"]{text-align:center; color: red;}'
                           "QPushButton{border:none;}"
                           )
        self.setContentsMargins(5, 0, 0, 5)

    def close_button_callback(self):
        self.window().close()


class transparentWindow(ResizableWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.out_alpha = 0.25

        # make sure the window does not steal focus from the matplotlib-canvas
        # on show (otherwise callbacks are inactive as long as the window is focused!)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Dialog|Qt.WindowStaysOnTopHint)

    def focusInEvent(self, e):
        self.setWindowOpacity(1)
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        if not self.isActiveWindow():
            self.setWindowOpacity(self.out_alpha)
        super().focusInEvent(e)



from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtCore import Signal

class MenuWindow(transparentWindow):

    cmapsChanged = Signal()

    def __init__(self, *args, m=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.m = m

        # clear the colormaps-dropdown pixmap cache if the colormaps have changed
        # (the signal is emmited by Maps-objects if a new colormap is registered)
        self.cmapsChanged.connect(lambda: get_cmap_pixmaps.cache_clear())

        self.titlebar = EOmaps_titlebar(m=self.m)
        self.titlebar.transparentQ.clicked.connect(self.cb_transparentQ)
        self.addToolBar(self.titlebar)

        tabs = utils.ControlTabs(parent=self)
        tabs.setMouseTracking(True)

        self.setStyleSheet("""QToolTip {
                                font-family: "SansSerif";
                                font-size:10;
                                background-color: rgb(53, 53, 53);
                                color: white;
                                border: none;
                                }""")
        self.cb_transparentQ()

        sizegrip = QtWidgets.QSizeGrip(self)


        menu_layout = QtWidgets.QVBoxLayout()
        menu_layout.addWidget(tabs)
        menu_layout.addWidget(sizegrip, 0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)

        menu_widget = QtWidgets.QWidget()
        menu_widget.setLayout(menu_layout)

        # prevent context-menu's from appearing to avoid the "hide toolbar"
        # context menu when right-clicking the toolbar
        self.setContextMenuPolicy(Qt.NoContextMenu)

        self.setCentralWidget(menu_widget)

        self.show()


    def cb_transparentQ(self):
        if self.out_alpha == 1:
            self.out_alpha = 0.25
            self.setFocus()
            self.titlebar.transparentQ.setIcon(QtGui.QIcon(str(iconpath / "eye_closed.png")))

        else:
            self.out_alpha = 1
            self.setFocus()
            self.titlebar.transparentQ.setIcon(QtGui.QIcon(str(iconpath / "eye_open.png")))



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

        b_showhide = QtWidgets.QToolButton()
        b_showhide.setIcon(QtGui.QIcon(str(iconpath / "logo.png")))
        b_showhide.clicked.connect(self.cb_showhide)
        b_showhide.setAutoRaise(True)

        self.toolbar.addSeparator()
        self.toolbar.addWidget(b_showhide)

        from .layer import AutoUpdateLayerMenuButton
        showlayer = AutoUpdateLayerMenuButton(m=self.m)

        self.toolbar.addWidget(showlayer)

        self.toolbar.addWidget(self.b_enlarge)
        self.toolbar.addWidget(self.b_close)

        self.toolbar.setMovable(False)
        self.setStyleSheet("border: none; spacing:5px;")

        self.addToolBar(self.toolbar)

        self.menu_window = MenuWindow(m=self.m)

        self.show()
        self.activateWindow()

        self.center()



    def cb_showhide(self):
        if self.menu_window.isVisible():
            self.menu_window.hide()
        else:
            self.menu_window.show()

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


if __name__ == "__main__":
    run()
