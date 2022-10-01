from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QRectF, QSize, QLocale, Signal
from pathlib import Path

from .base import ResizableWindow

def _str_to_bool(val):
    return val == "True"

def to_float_none(s):
    if len(s) > 0:
        return float(s.replace(",", "."))
    else:
        return None

def show_error_popup(text=None, info=None, title=None, details=None):
   global msg
   msg = QtWidgets.QMessageBox()
   msg.setIcon(QtWidgets.QMessageBox.Critical)

   if text:
       msg.setText(text)
   if info:
       msg.setInformativeText(info)
   if title:
       msg.setWindowTitle(title)
   if details:
       msg.setDetailedText(details)

   msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
   msg.setWindowFlags(Qt.Dialog|Qt.WindowStaysOnTopHint)

   msg.show()

def get_crs(crs):
    from eomaps import Maps

    try:
        if crs.startswith("Maps.CRS."):

            crsname = crs[9:]
            crs = getattr(Maps.CRS, crsname)
            if callable(crs):
                crs = crs()
        else:
            try:
                crs = int(crs)
            except Exception:
                pass

        # try if we can identify the crs
        Maps.get_crs(Maps, crs)
    except Exception:
        import traceback
        show_error_popup(text=f"{crs} is not a valid crs specifier",
                         title="Unable to identify crs",
                         details=traceback.format_exc())
    return crs


class LineEditComplete(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._options = None

        self.installEventFilter(self)

    def set_complete_vals(self, options):
        self._options = options
        completer = QtWidgets.QCompleter(self._options)
        self.setCompleter(completer)


    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self._options is not None:
            # set the completion-prefix to ensure all options are shown
            self.completer().setCompletionPrefix("")
            self.completer().complete()


class InputCRS(LineEditComplete):
    def __init__(self, *args, **kwargs):
        """
        A QtWidgets.QLineEdit widget with autocompletion for available CRS
        """
        super().__init__(*args,**kwargs)
        from eomaps import Maps

        crs_options = ["Maps.CRS." + key for key, val in Maps.CRS.__dict__.items()
                       if not key.startswith("_")
                       and (isinstance(val, Maps.CRS.ABCMeta)
                            or isinstance(val, Maps.CRS.CRS))]
        self.set_complete_vals(crs_options)
        self.setPlaceholderText("4326")

    def text(self):
        t = super().text()
        if len(t) == 0:
            return self.placeholderText()
        else:
            return t


class CmapDropdown(QtWidgets.QComboBox):
    def __init__(self, *args, startcmap="viridis", **kwargs):
        super().__init__(*args, **kwargs)

        from .app import get_cmap_pixmaps

        self.setIconSize(QSize(100, 15))
        self.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        for label, cmap in get_cmap_pixmaps():
            self.addItem(label, cmap)

        self.setStyleSheet("combobox-popup: 0;");
        self.setMaxVisibleItems(10)
        idx = self.findText(startcmap)
        if idx != -1:
            self.setCurrentIndex(idx)

    def wheelEvent(self, e):
        # ignore mouse-wheel events to disable changing the colormap with the mousewheel
        pass

class GetColorWidget(QtWidgets.QFrame):
    def __init__(self, facecolor="#ff0000", edgecolor="#000000", linewidth=1, alpha=1):
        """
        A widget that indicates a selected color (and opens a popup to change the
        color on click)

        Parameters
        ----------
        facecolor : str
            The initial facecolor to use.
        edgecolor : str
            The initial edgecolor to use.

        Attributes
        -------
        facecolor, edgecolor:
            The QColor object of the currently assigned facecolor/edgecolor.
            To get the hex-string, use    the  ".name()" property.

        """

        super().__init__()

        if isinstance(facecolor, str):
            self.facecolor = QtGui.QColor(facecolor)
        else:
            self.facecolor = QtGui.QColor(*facecolor)
        if isinstance(edgecolor, str):
            self.edgecolor = QtGui.QColor(edgecolor)
        else:
            self.edgecolor = QtGui.QColor(*edgecolor)

        self.linewidth = linewidth
        self.alpha = alpha


        self.setMinimumSize(15, 15)
        self.setMaximumSize(100, 100)


        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)


        self.setToolTip("<b>click</b>: set facecolor <br> <b>alt + click</b>: set edgecolor")

        self.setStyleSheet("""QToolTip {
                           font-family: "SansSerif";
                           font-size:10;
                           background-color: rgb(53, 53, 53);
                           color: white;
                           border: none;
                           }""")


    def resizeEvent(self, e):
        # make frame rectangular
        self.setMaximumHeight(self.width())


    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QtGui.QPainter(self)

        painter.setRenderHints(QtGui.QPainter.HighQualityAntialiasing )
        size = self.size()

        if self.linewidth > 0.01:
            painter.setPen(QtGui.QPen(self.edgecolor, 1.1*self.linewidth, Qt.SolidLine))
        else:
            painter.setPen(QtGui.QPen(self.facecolor, 1.1*self.linewidth, Qt.SolidLine))

        painter.setBrush(QtGui.QBrush(self.facecolor, Qt.SolidPattern))

        w, h = size.width(), size.height()
        s = min(min(0.9 * h, 0.9 * w), 100)
        rect = QRectF(w/2 - s/2, h/2 - s/2, s, s)
        painter.drawRoundedRect(rect, s/5, s/5)

        # painter.setFont(QtGui.QFont("Arial", 7))
        # painter.drawText(0, 0, w, h, Qt.AlignCenter,
        #                  f"α:  {self.alpha:.2f}" + "\n" + f"lw: {self.linewidth:.2f}")



    def mousePressEvent(self, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.buttons() & (bool(modifiers == Qt.AltModifier)):
            self.set_edgecolor_dialog()
        else:
            self.set_facecolor_dialog()

    def cb_colorselected(self):
        # a general callback that will always be connected to .colorSelected
        pass

    def set_facecolor_dialog(self):
        self._dialog = QtWidgets.QColorDialog()
        self._dialog.setWindowTitle("Select facecolor")
        self._dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        self._dialog.setOption(QtWidgets.QColorDialog.ShowAlphaChannel, on=True)
        self._dialog.colorSelected.connect(self.set_facecolor)
        self._dialog.colorSelected.connect(self.cb_colorselected)
        self._dialog.setCurrentColor(QtGui.QColor(self.facecolor))
        self._dialog.open()

    def set_edgecolor_dialog(self):
        self._dialog = QtWidgets.QColorDialog()
        self._dialog.setWindowTitle("Select edgecolor")
        self._dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        self._dialog.setOption(QtWidgets.QColorDialog.ShowAlphaChannel, on=True)
        self._dialog.colorSelected.connect(self.set_edgecolor)
        self._dialog.colorSelected.connect(self.cb_colorselected)
        self._dialog.setCurrentColor(QtGui.QColor(self.edgecolor))
        self._dialog.open()

    def set_facecolor(self, color):
        if isinstance(color, str):
            color = QtGui.QColor(color)

        self.alpha = color.alpha() / 255

        color = QtGui.QColor(*color.getRgb()[:3], int(self.alpha * 255))

        self.facecolor = color
        self.update()

    def set_edgecolor(self, color):
        if isinstance(color, str):
            color = QtGui.QColor(color)

        #color = QtGui.QColor(*color.getRgb()[:3], int(self.alpha * 255))
        #color = QtGui.QColor(*color.getRgbF())

        self.edgecolor = color
        self.update()

    def set_linewidth(self, linewidth):
        self.linewidth = linewidth
        self.update()

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.set_facecolor(QtGui.QColor(*self.facecolor.getRgb()[:3], int(self.alpha * 255)))
        #self.set_edgecolor(QtGui.QColor(*self.edgecolor.getRgb()[:3], int(self.alpha * 255)))


class EditLayoutButton(QtWidgets.QPushButton):
    def __init__(self, *args, m=None, **kwargs):
        """
        A subclass of QtWidgets.QPushButton that toggles the layout editor
        of an associated EOmaps.Maps object.

        All additional arguments are passed to QtWidgets.QPushButton

        Parameters
        ----------
        m : EOmaps.Maps
            The EOmaps.Maps object to use.

        Examples
        --------

        >>> b = EditLayoutButton('Edit layout', parent, m=self.m)

        """
        super().__init__(*args, **kwargs)

        self.m = m

        self.clicked.connect(self.callback)

    def callback(self):
        if not self.m._layout_editor._modifier_pressed:
            self.m.edit_layout()
        else:
            self.m._layout_editor._undo_draggable()



class AlphaSlider(QtWidgets.QSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.alpha = 1

        self.setRange(0, 100)
        self.setSingleStep(1)
        self.setTickInterval(10)
        self.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.setValue(100)

        #self.setMinimumWidth(50)
        self.setMaximumWidth(300)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.Minimum)

        self.valueChanged.connect(self.value_changed)


        self.setToolTip("Opacity")

        self.setStyleSheet("""QToolTip {
                           font-family: "SansSerif";
                           font-size:10;
                           background-color: rgb(53, 53, 53);
                           color: white;
                           border: none;
                           }""")



    def value_changed(self, i):
        self.alpha = i/100


class DrawerWidget(QtWidgets.QWidget):

    _polynames = {
                  "Polygon": "polygon",
                  "Rectangle": "rectangle",
                  "Circle": "circle",
                  }


    def __init__(self, parent=None):

        super().__init__()

        self.parent = parent

        self.shapeselector = QtWidgets.QComboBox()

        self.shapeselector.setMinimumWidth(50)
        self.shapeselector.setMaximumWidth(200)

        names = list(self._polynames)
        self._use_poly_type = self._polynames[names[0]]
        for key in names:
            self.shapeselector.addItem(key)
        self.shapeselector.activated[str].connect(self.set_poly_type)

        b1 = QtWidgets.QPushButton('Draw!')
        b1.clicked.connect(self.draw_shape_callback)

        self.colorselector = GetColorWidget()

        self.alphaslider = AlphaSlider(Qt.Horizontal)
        self.alphaslider.valueChanged.connect(lambda i: self.colorselector.set_alpha(i / 100))
        self.alphaslider.setValue(100)

        self.linewidthslider = AlphaSlider(Qt.Horizontal)
        self.linewidthslider.valueChanged.connect(lambda i: self.colorselector.set_linewidth(i / 10))
        self.linewidthslider.setValue(20)


        layout = QtWidgets.QGridLayout()

        layout.addWidget(self.colorselector, 0, 0, 2, 1)
        layout.addWidget(self.alphaslider, 0, 1)
        layout.addWidget(self.linewidthslider, 1, 1)

        layout.addWidget(self.shapeselector, 0, 2)
        layout.addWidget(b1, 1, 2)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)


    def set_poly_type(self, s):
        self._use_poly_type = self._polynames[s]

    def draw_shape_callback(self):

        p = self.m.util.draw.new_poly()
        getattr(p, self._use_poly_type)(
            facecolor = self.colorselector.facecolor.name(),
            edgecolor = self.colorselector.edgecolor.name(),
            alpha=self.alphaslider.alpha,
            linewidth=self.linewidthslider.alpha * 10
            )

    @property
    def m(self):
        return self.parent.m

class AutoUpdateLayerDropdown(QtWidgets.QComboBox):
    def __init__(self, *args, m=None, layers=None, exclude=None, use_active=False, empty_ok=True, **kwargs):
        super().__init__(*args, **kwargs)

        self.m = m
        self._layers = layers
        self._exclude = exclude
        self._use_active = use_active
        self._empty_ok = empty_ok

        self.last_layers = []

        self._last_active = None

        # update layers on every change of the Maps-object background layer
        self.m.BM.on_layer(self.update_visible_layer, persistent=True)
        self.update_layers()

        self.setSizeAdjustPolicy(self.AdjustToContents)

        self.activated.connect(self.set_last_active)

    def set_last_active(self):
        self._last_active = self.currentText()

    def update_visible_layer(self, m, l):
        # make sure to re-fetch layers first
        self.update_layers()

        if self._use_active:
            # set current index to active layer if _use_active
            currindex = self.findText(l)
            self.setCurrentIndex(currindex)
        elif self._last_active is not None:
            # set current index to last active layer otherwise
            idx = self.findText(self._last_active)
            if idx != -1:
                self.setCurrentIndex(idx)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.update_layers()
        elif event.button() == Qt.LeftButton:
            self.update_layers()


        super().mousePressEvent(event)

    @property
    def layers(self):
        if self._layers is not None:
            return self._layers
        else:
            return [i for i in self.m._get_layers(exclude = self._exclude) if not str(i).startswith("_")]

    def update_layers(self):
        layers = self.layers
        if set(layers) == set(self.last_layers):
            return


        self.last_layers = layers
        self.clear()

        if self._empty_ok:
            self.addItem("")

        for key in layers:
            self.addItem(str(key))

        if self._use_active:
            # set current index to active layer if _use_active
            currindex = self.findText(str(self.m.BM.bg_layer))
            self.setCurrentIndex(currindex)
        elif self._last_active is not None:
            # set current index to last active layer otherwise
            idx = self.findText(self._last_active)
            if idx != -1:
                self.setCurrentIndex(idx)


class PeekMethodButtons(QtWidgets.QWidget):
    methodChanged = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._method = "?"
        self.rectangle_size = 1
        self.how = (self.rectangle_size, self.rectangle_size)
        self.alpha = 1

        self.symbols = dict(zip(
            ("🡇", "🡅", "🡆", "🡄", "⛋", "🞑"),
            ("top", "bottom", "left", "right", "rectangle", "square"),
            ))

        self.symbols_inverted = {v: k for k, v in self.symbols.items()}

        self.buttons = dict()
        for symbol, method in self.symbols.items():
            b = QtWidgets.QToolButton()
            b.setText(symbol)
            b.setAutoRaise(True)
            b.clicked.connect(self.button_clicked)

            self.buttons[method] = b

        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.sider_value_changed)
        self.slider.setToolTip("Set rectangle size")
        self.slider.setRange(0, 100)
        self.slider.setSingleStep(1)
        self.slider.setTickPosition(QtWidgets.QSlider.NoTicks)
        self.slider.setValue(50)
        self.slider.setMinimumWidth(50)

        self.alphaslider = QtWidgets.QSlider(Qt.Horizontal)
        self.alphaslider.valueChanged.connect(self.alpha_changed)
        self.alphaslider.setToolTip("Set transparency")
        self.alphaslider.setRange(0, 100)
        self.alphaslider.setSingleStep(1)
        self.alphaslider.setTickPosition(QtWidgets.QSlider.NoTicks)
        self.alphaslider.setValue(100)
        self.alphaslider.setMinimumWidth(50)

        # -------------------------


        buttons = QtWidgets.QHBoxLayout()
        buttons.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        buttons.addWidget(self.buttons["top"])
        buttons.addWidget(self.buttons["bottom"])
        buttons.addWidget(self.buttons["right"])
        buttons.addWidget(self.buttons["left"])
        buttons.addWidget(self.buttons["rectangle"])
        buttons.addWidget(self.slider, 1)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(buttons)
        layout.addWidget(self.alphaslider)

        self.setLayout(layout)

        self.methodChanged.connect(self.method_changed)

        self.methodChanged.emit("square")
        self.buttons["rectangle"].setText(self.symbols_inverted["square"])


    def button_clicked(self):

        sender = self.sender().text()
        if self._method in ["rectangle", "square"]:
            if sender == self.symbols_inverted["square"]:
                method = "rectangle"
                self.buttons["rectangle"].setText(self.symbols_inverted["rectangle"])
            elif sender == self.symbols_inverted["rectangle"]:
                method = "square"
                self.buttons["rectangle"].setText(self.symbols_inverted["square"])
            else:
                method = self.symbols[sender]

        else:
            method = self.symbols[sender]

        self.methodChanged.emit(method)


    def sider_value_changed(self, i):
        self.rectangle_size = i/100
        if self._method in ["rectangle", "square"]:
            self.methodChanged.emit(self._method)
        else:
            self.methodChanged.emit("rectangle")

    def alpha_changed(self, i):
        self.alpha = i/100
        self.methodChanged.emit(self._method)

    def method_changed(self, method):
        self._method = method

        for key, val in self.buttons.items():
            if key == method:
                val.setStyleSheet('QToolButton {color: red; }')
            else:
                val.setStyleSheet("")

        if method == "square":
            self.buttons["rectangle"].setStyleSheet('QToolButton {color: red; }')



        if method == "rectangle":
            if self.rectangle_size < .99:
                self.how = (self.rectangle_size, self.rectangle_size)
            else:
                self.how = "full"
        elif method == "square":
            if self.rectangle_size < .99:
                self.how = self.rectangle_size
            else:
                self.how = "full"
        else:
            self.how = method





class PeekLayerWidget(QtWidgets.QWidget):

    def __init__(self, *args, parent=None, layers=None, exclude=None, how=(.5, .5), **kwargs):
        """
        A dropdown-list that attaches a peek-callback to look at the selected layer

        Parameters
        ----------
        layers : list or None, optional
            If a list is provided, only layers in the list will be used.
            Otherwise the available layers are fetched from the given Maps-object.
            The default is None.
        exclude : list, optional
            A list of layer-names to exclude. The default is None.

        Returns
        -------
        None.

        """
        super().__init__(*args, **kwargs)


        self.parent = parent
        self._layers = layers
        self._exclude = exclude

        self.cid = None
        self.current_layer = None

        self.layerselector = AutoUpdateLayerDropdown(m=self.m, layers=layers, exclude=exclude)
        self.layerselector.update_layers() # do this before attaching the callback!
        self.layerselector.currentIndexChanged[str].connect(self.set_layer_callback)
        self.layerselector.setMinimumWidth(100)

        self.buttons = PeekMethodButtons()
        self.buttons.methodChanged.connect(self.method_changed)

        modifier_label = QtWidgets.QLabel("Modifier:")
        self.modifier = QtWidgets.QLineEdit()
        self.modifier.setMaximumWidth(50)
        self.modifier.textChanged.connect(self.method_changed)

        modifier_layout = QtWidgets.QHBoxLayout()
        modifier_layout.addWidget(modifier_label, 0, Qt.AlignLeft)
        modifier_layout.addWidget(self.modifier, 0, Qt.AlignLeft)
        modifier_widget = QtWidgets.QWidget()
        modifier_widget.setLayout(modifier_layout)

        label = QtWidgets.QLabel("<b>Peek Layer</b>:")
        width = label.fontMetrics().boundingRect(label.text()).width()
        label.setFixedWidth(width + 5)

        selectorlayout = QtWidgets.QVBoxLayout()
        selectorlayout.addWidget(label, 0, Qt.AlignTop)
        selectorlayout.addWidget(self.layerselector, 0, Qt.AlignCenter|Qt.AlignLeft)
        selectorlayout.addWidget(modifier_widget)
        selectorlayout.setAlignment(Qt.AlignTop)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(selectorlayout)
        layout.addWidget(self.buttons)

        layout.setAlignment(Qt.AlignTop)

        self.setLayout(layout)

    @property
    def m(self):
        return self.parent.m

    def set_layer_callback(self, l):
        self.remove_peek_cb()
        if self.cid is not None:
            self.current_layer = None

        if l == "":
            return

        modifier = self.modifier.text().strip()
        if modifier == "":
            modifier = None

        self.cid = self.m.all.cb.click.attach.peek_layer(l,
                                                         how=self.buttons.how,
                                                         alpha=self.buttons.alpha,
                                                         modifier=modifier)
        self.current_layer = l


    def method_changed(self, method):
        self.add_peek_cb()

    def add_peek_cb(self):
        if self.current_layer is None:
            return

        self.remove_peek_cb()

        modifier = self.modifier.text()
        if modifier == "":
            modifier = None

        self.cid = self.m.all.cb.click.attach.peek_layer(self.current_layer,
                                                         how=self.buttons.how,
                                                         alpha=self.buttons.alpha,
                                                         modifier=modifier)


    def remove_peek_cb(self):
        if self.cid is not None:
            self.m.all.cb.click.remove(self.cid)
            self.cid = None

class NewWindowWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        """
        """
        super().__init__(*args, **kwargs)

        l0 = QtWidgets.QLabel("<b>Create a new Window:<b>")
        b1 = QtWidgets.QPushButton("New Window")
        b1.clicked.connect(self.new_window)
        l1 = QtWidgets.QLabel("crs:")
        self.t1 = InputCRS()
        self.t1.setPlaceholderText("Maps.CRS.GOOGLE_MERCATOR")

        new = QtWidgets.QGridLayout()

        new.addWidget(l0, 0, 0, 1, 2, Qt.AlignBottom)
        new.addWidget(l1, 1, 0, Qt.AlignVCenter)
        new.addWidget(self.t1, 1, 1,Qt.AlignBottom)
        new.addWidget(b1, 1, 2, Qt.AlignRight)

        self.setLayout(new)

    def new_window(self):
        try:
            from .app import MainWindow
            MainWindow(crs=get_crs(self.t1.text()))
        except Exception:
            import traceback
            show_error_popup(
                text="There was an error while trying to open a new window!",
                title="Error",
                details=traceback.format_exc())


class ShowLayerWidget(QtWidgets.QWidget):

    def __init__(self, *args, m=None, layers=None, exclude=None, **kwargs):
        """
        A dropdown-list to change the base-layer of the map

        Parameters
        ----------
        m : eomaps.Maps, optional
            The eomaps.Maps object to use. The default is None.
        layers : list or None, optional
            If a list is provided, only layers in the list will be used.
            Otherwise the available layers are fetched from the given Maps-object.
            The default is None.
        exclude : list, optional
            A list of layer-names to exclude. The default is None.

        Returns
        -------
        None.

        """
        super().__init__(*args, **kwargs)

        self.m = m
        self._layers = layers
        self._exclude = exclude

        self.cid = None

        self.layerselector = AutoUpdateLayerDropdown(m=self.m, layers=layers, exclude=exclude, use_active=True, empty_ok=False)
        self.layerselector.activated[str].connect(self.set_layer_callback)


        label = QtWidgets.QLabel("<b>Active layer:</b>")
        #width = label.fontMetrics().boundingRect(label.text()).width()
        #label.setFixedWidth(width + 2)


        vis_layer_layout = QtWidgets.QHBoxLayout()
        vis_layer_layout.addWidget(label)
        vis_layer_layout.addWidget(self.layerselector)
        vis_layer_layout.setAlignment(Qt.AlignRight|Qt.AlignTop)
        vis_layer_layout.setContentsMargins(0,0,0,0)
        self.setLayout(vis_layer_layout)


    def set_layer_callback(self, l):
        print("showlayer cb", l)
        if l == "":
            return

        try:
            self.m.show_layer(l)
        except Exception:
            print(f"showing the layer '{l}' did not work")



class ShowPeekLayerWidget(QtWidgets.QWidget):
    def __init__(self, *args, parent=None, **kwargs):
        """
        A layer-control widget to select both the base-layer and the peek-layer

        Parameters
        ----------
        m : eomaps.Maps, optional
            The eomaps.Maps object to use. The default is None.
        """
        super().__init__(*args, **kwargs)
        self.parent = parent

        peek = PeekLayerWidget(parent=self.parent)

        leftlayout = QtWidgets.QVBoxLayout()
        leftlayout.setAlignment(Qt.AlignTop)

        rightlayout = QtWidgets.QVBoxLayout()
        rightlayout.addWidget(peek)

        left = QtWidgets.QWidget()
        left.setLayout(leftlayout)

        right = QtWidgets.QWidget()
        right.setLayout(rightlayout)

        split = QtWidgets.QSplitter(Qt.Horizontal)
        split.addWidget(left)
        split.addWidget(right)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(split)

        self.setLayout(layout)

    @property
    def m(self):
        return self.parent.m


class ShapeSelector(QtWidgets.QWidget):


    _ignoreargs = ["shade_hook", "agg_hook"]

    _argspecials = dict(aggregator = {"None": None},
                        mask_radius = {"None": None})

    _argtypes = dict(radius = (float, str),
                     radius_crs = (int, str),
                     n = (int,),
                     mesh = (_str_to_bool,),
                     masked = (_str_to_bool,),
                     mask_radius = (float,),
                     flat = (_str_to_bool,),
                     aggregator = (str,)
                     )


    def __init__(self, *args, m=None, default_shape = "shade_raster", **kwargs):
        super().__init__(*args, **kwargs)
        self.m = m
        self.shape = default_shape


        self.layout = QtWidgets.QVBoxLayout()
        self.options = QtWidgets.QVBoxLayout()



        self.shape_selector = QtWidgets.QComboBox()
        for i in self.m.set_shape._shp_list:
            self.shape_selector.addItem(i)

        label = QtWidgets.QLabel("Shape:")
        self.shape_selector.activated[str].connect(self.shape_changed)
        shapesel = QtWidgets.QHBoxLayout()
        shapesel.addWidget(label)
        shapesel.addWidget(self.shape_selector)


        self.layout.addLayout(shapesel)
        self.layout.addLayout(self.options)

        self.setLayout(self.layout)

        self.shape_selector.setCurrentIndex(self.shape_selector.findText(self.shape))
        self.shape_changed(self.shape)

    def argparser(self, key, val):
        special = self._argspecials.get(key, None)
        if special and val in special:
            return special[val]

        convtype = self._argtypes.get(key, (str,))

        for t in convtype:
            try:
                convval = t(val)
            except ValueError:
                continue

            return convval

        print(r"WARNING value-conversion for {key} = {val} did not succeed!")
        return val

    @property
    def shape_args(self):

        out = dict(shape=self.shape)
        for key, val in self.paraminputs.items():
            out[key] = self.argparser(key, val.text())

        return out


    def shape_changed(self, s):
        self.shape = s

        import inspect
        signature = inspect.signature(getattr(self.m.set_shape, s))

        self.clear_item(self.options)

        self.options = QtWidgets.QVBoxLayout()


        self.paraminputs = dict()
        for key, val in signature.parameters.items():

            paramname, paramdefault = val.name, val.default

            if paramname in self._ignoreargs:
                continue

            param = QtWidgets.QHBoxLayout()
            name = QtWidgets.QLabel(paramname)
            valinput = QtWidgets.QLineEdit(str(paramdefault))

            param.addWidget(name)
            param.addWidget(valinput)

            self.paraminputs[paramname] = valinput

            self.options.addLayout(param)

        self.layout.addLayout(self.options)

    def clear_item(self, item):
        if hasattr(item, "layout"):
            if callable(item.layout):
                layout = item.layout()
        else:
            layout = None

        if hasattr(item, "widget"):
            if callable(item.widget):
                widget = item.widget()
        else:
            widget = None

        if widget:
            widget.setParent(None)
        elif layout:
            for i in reversed(range(layout.count())):
                self.clear_item(layout.itemAt(i))



class PlotFileWidget(QtWidgets.QWidget):

    file_endings = None
    default_shape = "shade_raster"

    def __init__(self, *args, parent=None, close_on_plot=True, attach_tab_after_plot=True, tab=None, **kwargs):
        """
        A widget to add a layer from a file

        Parameters
        ----------
        *args : TYPE
            DESCRIPTION.
        m : TYPE, optional
            DESCRIPTION. The default is None.
        **kwargs : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        super().__init__(*args, **kwargs)


        self.parent = parent
        self.tab = tab
        self.attach_tab_after_plot = attach_tab_after_plot
        self.close_on_plot = close_on_plot

        self.m2 = None
        self.cid_annotate = None

        self.file_path = None


        self.b_plot = QtWidgets.QPushButton('Plot!', self)
        self.b_plot.clicked.connect(self.b_plot_file)


        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        self.file_info = QtWidgets.QLabel()
        self.file_info.setWordWrap(True)
        # self.file_info.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.file_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        scroll.setWidget(self.file_info)


        self.cb1 = QtWidgets.QCheckBox("Annotate on click")
        self.cb1.stateChanged.connect(self.b_add_annotate_cb)

        self.cb2 = QtWidgets.QCheckBox("Add colorbar")
        self.cb2.stateChanged.connect(self.b_add_colorbar)

        self.blayer = QtWidgets.QCheckBox()
        self._blayer_text = ""
        self.blayer.stateChanged.connect(self.b_layer_checkbox)
        self.t1_label = QtWidgets.QLabel("Layer:")
        self.t1 = QtWidgets.QLineEdit()
        self.t1.setPlaceholderText(str(self.m.BM.bg_layer))

        self.shape_selector= ShapeSelector(m=self.m, default_shape=self.default_shape)

        self.setlayername = QtWidgets.QWidget()
        layername = QtWidgets.QHBoxLayout()
        layername.addWidget(self.blayer)
        layername.addWidget(self.t1_label)
        layername.addWidget(self.t1)
        self.setlayername.setLayout(layername)

        self.cmaps = CmapDropdown()

        validator = QtGui.QDoubleValidator()
        # make sure the validator uses . as separator
        validator.setLocale(QLocale("en_US"))

        vminlabel = QtWidgets.QLabel("vmin=")
        self.vmin = QtWidgets.QLineEdit()
        self.vmin.setValidator(validator)
        vmaxlabel = QtWidgets.QLabel("vmax=")
        self.vmax = QtWidgets.QLineEdit()
        self.vmax.setValidator(validator)

        minmaxupdate = QtWidgets.QPushButton("🗘")
        minmaxupdate.clicked.connect(self.do_update_vals)

        minmaxlayout = QtWidgets.QHBoxLayout()
        minmaxlayout.setAlignment(Qt.AlignLeft)
        minmaxlayout.addWidget(vminlabel)
        minmaxlayout.addWidget(self.vmin)
        minmaxlayout.addWidget(vmaxlabel)
        minmaxlayout.addWidget(self.vmax)
        minmaxlayout.addWidget(minmaxupdate, Qt.AlignRight)


        options = QtWidgets.QVBoxLayout()
        options.addWidget(self.cb1)
        options.addWidget(self.cb2)
        options.addWidget(self.setlayername)
        options.addWidget(self.shape_selector)
        options.addWidget(self.cmaps)
        options.addLayout(minmaxlayout)

        optionwidget = QtWidgets.QWidget()
        optionwidget.setLayout(options)

        optionscroll = QtWidgets.QScrollArea()
        optionscroll.setWidgetResizable(True)
        optionscroll.setMinimumWidth(200)

        optionscroll.setWidget(optionwidget)

        options_split = QtWidgets.QSplitter(Qt.Horizontal)
        options_split.addWidget(scroll)
        options_split.addWidget(optionscroll)
        options_split.setSizes((500, 300))

        self.options_layout = QtWidgets.QHBoxLayout()
        self.options_layout.addWidget(options_split)

        self.x = LineEditComplete("x")
        self.y = LineEditComplete("y")
        self.parameter = LineEditComplete("param")


        self.crs = InputCRS()

        tx = QtWidgets.QLabel("x:")
        ty = QtWidgets.QLabel("y:")
        tparam = QtWidgets.QLabel("parameter:")
        tcrs = QtWidgets.QLabel("crs:")

        plotargs = QtWidgets.QHBoxLayout()
        plotargs.addWidget(tx)
        plotargs.addWidget(self.x)
        plotargs.addWidget(ty)
        plotargs.addWidget(self.y)
        plotargs.addWidget(tparam)
        plotargs.addWidget(self.parameter)
        plotargs.addWidget(tcrs)
        plotargs.addWidget(self.crs)

        plotargs.addWidget(self.b_plot)

        self.title = QtWidgets.QLabel("<b>Set plot variables:</b>")
        withtitle = QtWidgets.QVBoxLayout()
        withtitle.addWidget(self.title)
        withtitle.addLayout(plotargs)
        withtitle.setAlignment(Qt.AlignBottom)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.options_layout, stretch=1)
        self.layout.addLayout(withtitle)

        self.setLayout(self.layout)

    @property
    def m(self):
        return self.parent.m

    def get_layer(self):
        layer = self.m.BM.bg_layer

        if self.blayer.isChecked():
            layer = self.t1.text()
            if len(layer) == 0 and self.file_path is not None:
                layer = self.file_path.stem
                self.t1.setText(layer)

        return layer


    def b_layer_checkbox(self):
        if self.blayer.isChecked():
            self.t1.setReadOnly(False)
            if len(self.t1.text()) == 0 and self.file_path is not None:
                layer = self.file_path.stem
                self.t1.setText(layer)
        else:
            self.t1.setReadOnly(True)
            self.t1.setText("")

    def b_add_colorbar(self):
        if self.m2 is None:
            return

        if self.cb2.isChecked():
            cb = self.m2.add_colorbar()
            cb[2].patch.set_color("none")
            cb[3].patch.set_color("none")
        else:
            try:
                self.m2._remove_colorbar()
            except:
                pass

    def b_add_annotate_cb(self):
        if self.m2 is None:
            return

        if self.cb1.isChecked():
            if self.cid_annotate is None:
                self.cid_annotate = self.m2.cb.pick.attach.annotate()
        else:
            if self.cid_annotate is not None:
                self.m2.cb.pick.remove(self.cid_annotate)
                self.cid_annotate = None

    def open_file(self, file_path=None):
        info = self.do_open_file(file_path)

        if self.file_endings is not None:
            if file_path.suffix.lower() not in self.file_endings:
                self.file_info.setText(
                    f"the file {self.file_path.name} is not a valid file"
                    )
                self.file_path = None
                return

        if file_path is not None:
            if self.blayer.isChecked():
                self.t1.setText(file_path.stem)
            self.file_path = file_path

        if info is not None:
            self.file_info.setText(info)

        self.window = NewWindow(parent=self.parent)
        self.window.setWindowFlags(Qt.FramelessWindowHint|Qt.Dialog|Qt.WindowStaysOnTopHint)

        self.window.layout.addWidget(self)
        self.window.resize(800, 500)
        self.window.show()


    def b_plot_file(self):
        try:
            self.do_plot_file()
        except Exception:
            import traceback
            show_error_popup(
                text="There was an error while trying to plot the data!",
                title="Error",
                details=traceback.format_exc())
            return

        if self.close_on_plot:
            self.window.close()


        if self.attach_tab_after_plot:
            self.attach_as_tab()

    def do_open_file(self):
        file_path = Path(QtWidgets.QFileDialog.getOpenFileName()[0])

        return (file_path,
                f"The file {file_path.stem} has\n {file_path.stat().st_size} bytes.")

    def do_plot_file(self):
        self.file_info.setText("Implement `.do_plot_file()` to plot the data!")

    def do_update_vals(self):
        return

    def attach_as_tab(self):
        if self.tab is None:
            return

        if self.file_path is not None:
            name = self.file_path.stem
        else:
            return

        if len(name) > 10:
            name = name[:7] + "..."
        self.tab.addTab(self, name)

        tabindex = self.tab.indexOf(self)

        self.tab.setCurrentIndex(tabindex)
        self.tab.setTabToolTip(tabindex, str(self.file_path))

        self.title.setText("<b>Variables used for plotting:</b>")

        self.t1.setReadOnly(True)
        self.x.setReadOnly(True)
        self.y.setReadOnly(True)
        self.parameter.setReadOnly(True)
        self.crs.setReadOnly(True)
        self.vmin.setReadOnly(True)
        self.vmax.setReadOnly(True)

        self.cmaps.setEnabled(False)
        self.shape_selector.setEnabled(False)
        self.setlayername.setEnabled(False)
        self.b_plot.close()



class PlotGeoTIFFWidget(PlotFileWidget):

    file_endings = (".tif", ".tiff")

    def do_open_file(self, file_path):
        import xarray as xar

        with xar.open_dataset(file_path) as f:
            import io
            info = io.StringIO()
            f.info(info)

            coords = list(f.coords)
            variables = list(f.variables)

            self.crs.setText(f.rio.crs.to_string())
            self.parameter.setText(next((i for i in variables if i not in coords)))


        self.x.setText("x")
        self.y.setText("y")

        # set values for autocompletion
        cols = sorted(set(variables + coords))
        self.x.set_complete_vals(cols)
        self.y.set_complete_vals(cols)
        self.parameter.set_complete_vals(cols)


        return info.getvalue()


    def do_plot_file(self):
        if self.file_path is None:
            return

        m2 = self.m.new_layer_from_file.GeoTIFF(
            self.file_path,
            shape=self.shape_selector.shape_args,
            coastline=False,
            layer=self.get_layer(),
            cmap=self.cmaps.currentText(),
            vmin=to_float_none(self.vmin.text()),
            vmax=to_float_none(self.vmax.text()),
            )

        m2.cb.pick.attach.annotate(modifier=1)

        m2.show_layer(m2.layer)

        self.m2 = m2
        # check if we want to add an annotation
        self.b_add_annotate_cb()

    def do_update_vals(self):
        import xarray as xar

        try:
            with xar.open_dataset(self.file_path) as f:
                vmin = f[self.parameter.text()].min()
                vmax = f[self.parameter.text()].max()

                self.vmin.setText(str(float(vmin)))
                self.vmax.setText(str(float(vmax)))

        except Exception:
            import traceback
            show_error_popup(
                text="There was an error while trying to update the values.",
                title="Unable to update values.",
                details=traceback.format_exc())




class PlotNetCDFWidget(PlotFileWidget):

    file_endings = (".nc")

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        l = QtWidgets.QHBoxLayout()
        self.sel = QtWidgets.QLineEdit("")

        tsel = QtWidgets.QLabel("isel:")


        l.addWidget(tsel)
        l.addWidget(self.sel)

        withtitle = QtWidgets.QWidget()
        withtitlelayout = QtWidgets.QVBoxLayout()

        withtitlelayout.addLayout(l)

        withtitle.setLayout(withtitlelayout)
        withtitle.setMaximumHeight(60)

        self.layout.addWidget(withtitle)

    def get_crs(self):
        return get_crs(self.crs.text())

    def get_sel(self):
        import ast

        try:
            sel = self.sel.text()
            if len(sel) == 0:
                return

            return ast.literal_eval("{'date':1}")
        except Exception:
            import traceback
            show_error_popup(text=f"{sel} is not a valid selection",
                             title="Invalid selection args",
                             details=traceback.format_exc())


    def do_open_file(self, file_path):
        import xarray as xar

        with xar.open_dataset(file_path) as f:
            import io
            info = io.StringIO()
            f.info(info)

            coords = list(f.coords)
            variables = list(f.variables)
            if len(coords) >= 2:
                self.x.setText(coords[0])
                self.y.setText(coords[1])

            self.parameter.setText(next((i for i in variables if i not in coords)))

            # set values for autocompletion
            cols = sorted(set(variables + coords))
            self.x.set_complete_vals(cols)
            self.y.set_complete_vals(cols)

            if "lon" in cols:
                self.x.setText("lon")
            else:
                self.x.setText(cols[0])

            if "lat" in cols:
                self.y.setText("lat")
            else:
                self.x.setText(cols[1])

            self.parameter.set_complete_vals(cols)

        return info.getvalue()


    def do_update_vals(self):
        import xarray as xar

        try:
            with xar.open_dataset(self.file_path) as f:
                isel = self.get_sel()
                if isel is not None:
                    vmin = f.isel(**isel)[self.parameter.text()].min()
                    vmax = f.isel(**isel)[self.parameter.text()].max()
                else:
                    vmin = f[self.parameter.text()].min()
                    vmax = f[self.parameter.text()].max()

                self.vmin.setText(str(float(vmin)))
                self.vmax.setText(str(float(vmax)))

        except Exception:
            import traceback
            show_error_popup(
                text="There was an error while trying to update the values.",
                title="Unable to update values.",
                details=traceback.format_exc())



    def do_plot_file(self):
        if self.file_path is None:
            return

        m2 = self.m.new_layer_from_file.NetCDF(
            self.file_path,
            shape=self.shape_selector.shape_args,
            coastline=False,
            layer=self.get_layer(),
            coords=(self.x.text(), self.y.text()),
            parameter=self.parameter.text(),
            data_crs=self.get_crs(),
            isel=self.get_sel(),
            cmap=self.cmaps.currentText(),
            vmin=to_float_none(self.vmin.text()),
            vmax=to_float_none(self.vmax.text()),
            )

        m2.cb.pick.attach.annotate(modifier=1)

        m2.show_layer(m2.layer)

        self.m2 = m2
        # check if we want to add an annotation
        self.b_add_annotate_cb()


class PlotCSVWidget(PlotFileWidget):

    default_shape = "ellipses"
    file_endings = (".csv")

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)


    def get_crs(self):
        return get_crs(self.crs.text())

    def do_open_file(self, file_path):
        import pandas as pd

        head = pd.read_csv(file_path, nrows=50)
        cols = head.columns

        # set values for autocompletion
        self.x.set_complete_vals(cols)
        self.y.set_complete_vals(cols)
        self.parameter.set_complete_vals(cols)


        if len(cols) == 3:

            if "lon" in cols:
                self.x.setText("lon")
            else:
                self.x.setText(cols[0])

            if "lat" in cols:
                self.y.setText("lat")
            else:
                self.x.setText(cols[1])

            self.parameter.setText(cols[2])
        if len(cols) > 3:

            if "lon" in cols:
                self.x.setText("lon")
            else:
                self.x.setText(cols[1])

            if "lat" in cols:
                self.y.setText("lat")
            else:
                self.x.setText(cols[2])

            self.parameter.setText(cols[3])

        return head.__repr__()


    def do_plot_file(self):
        if self.file_path is None:
            return

        m2 = self.m.new_layer_from_file.CSV(
            self.file_path,
            shape=self.shape_selector.shape_args,
            coastline=False,
            layer=self.get_layer(),
            parameter=self.parameter.text(),
            x=self.x.text(),
            y=self.y.text(),
            data_crs=self.get_crs(),
            cmap=self.cmaps.currentText(),
            vmin=to_float_none(self.vmin.text()),
            vmax=to_float_none(self.vmax.text()),
            )

        m2.show_layer(m2.layer)

        self.m2 = m2

        # check if we want to add an annotation
        self.b_add_annotate_cb()


    def do_update_vals(self):
        try:
            import pandas as pd
            df = pd.read_csv(self.file_path)

            vmin = df[self.parameter.text()].min()
            vmax = df[self.parameter.text()].max()

            self.vmin.setText(str(float(vmin)))
            self.vmax.setText(str(float(vmax)))

        except Exception:
            import traceback
            show_error_popup(
                text="There was an error while trying to update the values.",
                title="Unable to update values.",
                details=traceback.format_exc())




from . import base
class NewWindow(ResizableWindow):
    def __init__(self, *args, parent = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.setWindowTitle("OpenFile")

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(5, 20, 5, 5)

        widget = QtWidgets.QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        # a exit-button (add it as the last object to make sure it's on top)
        self.floatb = base.FloatingButtonWidget(self)
        self.floatb.setFixedSize(30, 30)
        self.floatb.setText("\u274C")
        self.floatb.setStyleSheet("text-align:top;border:none;")
        self.floatb.clicked.connect(self.close_button_callback)
        self.floatb.move(0,0)

        self.floatb2 = base.FloatingButtonWidget(self)
        self.floatb2.setFixedSize(30, 30)
        self.floatb2.setText("\u25a0")
        self.floatb2.setStyleSheet("text-align:top;border:none;")
        self.floatb2.clicked.connect(self.maximize_button_callback)
        self.floatb2.paddingLeft = 30



    def resizeEvent(self, event): #2
        super().resizeEvent(event)
        self.floatb.update_position()
        self.floatb2.update_position()

    def close_button_callback(self):
        self.close()

    def maximize_button_callback(self):
        if not self.isMaximized():
            self.showMaximized()
        else:
            self.showNormal()

    @property
    def m(self):
        return self.parent.m


class OpenDataStartTab(QtWidgets.QWidget):
    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)


        self.t1 = QtWidgets.QLabel()
        self.t1.setAlignment(Qt.AlignBottom|Qt.AlignCenter)
        self.set_std_text()

        self.b1 = self.FileButton("Open File", tab=parent, txt=self.t1)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.b1, 0, 0)
        layout.addWidget(self.t1, 3, 0)


        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        self.setAcceptDrops(True)

    def set_std_text(self):
        self.t1.setText(
            "\n"+
            "Open or DRAG & DROP files!\n\n"+
            "Currently supported filetypes are:\n"+
            "    NetCDF | GeoTIFF | CSV")

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
            self.t1.setText("DROP IT!")
        else:
            e.ignore()
            self.set_std_text()

    def dragLeaveEvent(self, e):
        self.set_std_text()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if len(urls) > 1:
            return

        self.b1.new_file_tab(urls[0].toLocalFile())




    class FileButton(QtWidgets.QPushButton):
        def __init__(self, *args, tab=None, txt=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.tab = tab
            self.clicked.connect(lambda: self.new_file_tab())
            self.txt = txt


        @property
        def m(self):
            return self.tab.m

        def new_file_tab(self, file_path = None):

            if self.txt:
                self.txt.setText("")

            if file_path is None:
                file_path = Path(QtWidgets.QFileDialog.getOpenFileName()[0])
            elif isinstance(file_path, str):
                file_path = Path(file_path)

            global plc
            ending = file_path.suffix.lower()
            if ending in [".nc"]:
                plc = PlotNetCDFWidget(parent = self.tab.parent, tab=self.tab)
            elif ending in [".csv"]:
                plc = PlotCSVWidget(parent = self.tab.parent, tab=self.tab)
            elif ending in [".tif", ".tiff"]:
                plc = PlotGeoTIFFWidget(parent = self.tab.parent, tab=self.tab)
            else:
                print("unknown file extension")

            try:
                plc.open_file(file_path)
            except Exception:
                if self.txt:
                    self.txt.setText("File could not be opened...")
                import traceback
                show_error_popup(
                    text="There was an error while trying to open the file.",
                    title="Unable to open file.",
                    details=traceback.format_exc())



class OpenFileTabs(QtWidgets.QTabWidget):
    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.parent = parent

        t1 = OpenDataStartTab(parent=self)
        self.addTab(t1, "NEW")

    @property
    def m(self):
        return self.parent.m

class SaveFileWidget(QtWidgets.QWidget):

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

        b_edit = EditLayoutButton('Edit layout', m=self.m)
        width = b_edit.fontMetrics().boundingRect(b_edit.text()).width()
        b_edit.setFixedWidth(width + 30)



        b1 = QtWidgets.QPushButton('Save!')
        width = b1.fontMetrics().boundingRect(b1.text()).width()
        b1.setFixedWidth(width + 30)

        b1.clicked.connect(self.save_file)

        # dpi
        l1 = QtWidgets.QLabel("DPI:")
        width = l1.fontMetrics().boundingRect(l1.text()).width()
        l1.setFixedWidth(width + 5)


        self.dpi_input = QtWidgets.QLineEdit()
        self.dpi_input.setMaximumWidth(50)
        validator = QtGui.QIntValidator()
        self.dpi_input.setValidator(validator)
        self.dpi_input.setText("200")

        # transparent
        self.transp_cb = QtWidgets.QCheckBox()
        transp_label = QtWidgets.QLabel("Tranparent")
        width = transp_label.fontMetrics().boundingRect(transp_label.text()).width()
        transp_label.setFixedWidth(width + 5)


        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(b_edit)
        layout.addStretch(1)
        layout.addWidget(l1)
        layout.addWidget(self.dpi_input)
        layout.addWidget(transp_label)
        layout.addWidget(self.transp_cb)

        layout.addWidget(b1)

        layout.setAlignment(Qt.AlignBottom)

        self.setLayout(layout)

    @property
    def m(self):
        return self.parent.m

    def save_file(self):
        savepath = QtWidgets.QFileDialog.getSaveFileName()[0]

        if savepath is not None:
            self.m.savefig(savepath, dpi=int(self.dpi_input.text()),
                           transparent = self.transp_cb.isChecked())

class PeekTabs(QtWidgets.QTabWidget):
    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent


        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_handler)

        w = PeekLayerWidget(parent=self.parent)
        self.addTab(w, "    ")

        # update the tab title with the modifier key
        cb = self.settxt_factory(w)
        w.modifier.textChanged.connect(cb)
        w.buttons.methodChanged.connect(cb)
        w.layerselector.currentIndexChanged[str].connect(cb)

        # emit signal to set text
        w.buttons.methodChanged.emit(w.buttons._method)

        # a tab that is used to create new tabs
        self.addTab(QtWidgets.QWidget(), "+")
        # don't show the close button for this tab
        self.tabBar().setTabButton(self.count()-1, self.tabBar().RightSide, None)

        self.tabBarClicked.connect(self.tabbar_clicked)

        self.setCurrentIndex(0)


    def tabbar_clicked(self, index):
        if self.tabText(index) == "+":
            w = PeekLayerWidget(parent=self.parent)
            self.insertTab(self.count() - 1, w, "    ")

            # update the tab title with the modifier key
            cb = self.settxt_factory(w)
            w.modifier.textChanged.connect(cb)
            w.buttons.methodChanged.connect(cb)
            w.layerselector.currentIndexChanged[str].connect(cb)
            # emit signal to set text
            w.buttons.methodChanged.emit(w.buttons._method)

    def close_handler(self, index):
        self.widget(index).remove_peek_cb()
        self.removeTab(index)

    def settxt_factory(self, w):
        def settxt():
            self.setTabText(self.indexOf(w),
                            w.buttons.symbols_inverted.get(w.buttons._method, "") +
                            ((
                            " [" +
                            w.modifier.text() +
                            "]: "
                            ) if w.modifier.text().strip() != "" else ": ") +
                            (w.current_layer if w.current_layer is not None else ""))
        return settxt


class ControlTabs(QtWidgets.QTabWidget):
    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

        tab1 = QtWidgets.QWidget()
        tab1layout = QtWidgets.QVBoxLayout()

        peektabs = PeekTabs(parent= self.parent)
        tab1layout.addWidget(peektabs)

        from .wms_utils import AddWMSMenuButton
        try:
            addwms = AddWMSMenuButton(m=self.m, new_layer=True)
        except:
            addwms = QtWidgets.QPushButton("WMS services unavailable")
        tab1layout.addWidget(addwms)

        tab1layout.addStretch(1)
        tab1layout.addWidget(SaveFileWidget(parent=self.parent))

        tab1.setLayout(tab1layout)


        self.tab1 = tab1
        self.tab2 = OpenFileTabs(parent=self.parent)
        self.tab3 = DrawerWidget(parent=self.parent)


        from .layer import LayerArtistEditor
        self.tab6 = LayerArtistEditor(m=self.m)

        self.addTab(self.tab1, "Compare")
        self.addTab(self.tab6, "Edit")
        self.addTab(self.tab2, "Open Files")
        if hasattr(self.m.util, "draw"):   # for future "draw" capabilities
            self.addTab(self.tab3, "Draw Shapes")

        # re-populate artists on tab-change
        self.currentChanged.connect(self.tabchanged)

        self.setAcceptDrops(True)


    def tabchanged(self):
        if self.currentWidget() == self.tab6:
            self.tab6.populate()
            self.tab6.populate_layer()

    @property
    def m(self):
        return self.parent.m


    def dragEnterEvent(self, e):
        # switch to open-file-tab on drag-enter
        # (the open-file-tab takes over from there!)
        self.setCurrentWidget(self.tab2)
        self.tab2.setCurrentIndex(0)
