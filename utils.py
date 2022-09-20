from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QRectF, QSize, QLocale, QEvent
from pathlib import Path

from .base import ResizableWindow
from .layer import LayerEditor


import matplotlib.pyplot as plt


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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setIconSize(QSize(100, 15))

        cmaps = plt.cm._colormaps()

        self.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        for cmap in sorted(cmaps):
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(getattr(plt.cm, cmap)._repr_png_(), "png")
            label = QtGui.QIcon()
            label.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.On)
            label.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
            label.addPixmap(pixmap, QtGui.QIcon.Disabled, QtGui.QIcon.On)
            label.addPixmap(pixmap, QtGui.QIcon.Disabled, QtGui.QIcon.Off)


            self.addItem(label, cmap)

        self.setStyleSheet("combobox-popup: 0;");
        self.setMaxVisibleItems(10)

        idx = self.findText("viridis")
        self.setCurrentIndex(idx)



class GetColorWidget(QtWidgets.QWidget):
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


        self.facecolor = QtGui.QColor(facecolor)
        self.edgecolor = QtGui.QColor(edgecolor)
        self.linewidth = linewidth
        self.alpha = alpha


        self.setMinimumSize(15, 15)
        self.setMaximumSize(100, 100)

        self.setToolTip("<b>click</b>: set facecolor <br> <b>alt + click</b>: set edgecolor!")

        self.setStyleSheet("""QToolTip {
                           font-family: "SansSerif";
                           font-size:10;
                           background-color: rgb(53, 53, 53);
                           color: white;
                           border: none;
                           }""")

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)

        painter.setRenderHints(QtGui.QPainter.HighQualityAntialiasing )
        size = self.size()

        if self.linewidth > 0.01:
            painter.setPen(QtGui.QPen(self.edgecolor, self.linewidth, Qt.SolidLine))
        else:
            painter.setPen(QtGui.QPen(self.facecolor, self.linewidth, Qt.SolidLine))

        painter.setBrush(QtGui.QBrush(self.facecolor, Qt.SolidPattern))

        w, h = size.width(), size.height()
        s = min(min(0.9 * h, 0.9 * w), 100)
        #painter.drawRect(w/2 - s/2, h/2 - s/2, s, s)
        rect = QRectF(w/2 - s/2, h/2 - s/2, s, s)
        painter.drawRoundedRect(rect, s/5, s/5)

    def mousePressEvent(self, event):
        print("clicked!")
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.buttons() & (bool(modifiers == Qt.AltModifier)):
            print("clicked! edge")
            self.set_edgecolor_dialog()
        else:
            print("clicked! face")
            self.set_facecolor_dialog()

    def set_facecolor_dialog(self):
        c = QtWidgets.QColorDialog.getColor()
        self.set_facecolor(c)

    def set_edgecolor_dialog(self):
        c = QtWidgets.QColorDialog.getColor()
        self.set_edgecolor(c)

    def set_facecolor(self, color):
        if isinstance(color, str):
            color = QtGui.QColor(color)

        color = QtGui.QColor(*color.getRgb()[:3], int(self.alpha * 255))

        self.facecolor = color
        self.update()

    def set_edgecolor(self, color):
        if isinstance(color, str):
            color = QtGui.QColor(color)

        color = QtGui.QColor(*color.getRgb()[:3], int(self.alpha * 255))

        self.edgecolor = color
        self.update()

    def set_linewidth(self, linewidth):
        self.linewidth = linewidth
        self.update()

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.set_facecolor(QtGui.QColor(*self.facecolor.getRgb()[:3], int(self.alpha * 255)))
        self.set_edgecolor(QtGui.QColor(*self.edgecolor.getRgb()[:3], int(self.alpha * 255)))


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

        self.setMinimumWidth(50)
        self.setMaximumWidth(100)

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

        # update layers on every change of the Maps-object background layer
        self.m.BM.on_layer(self.update_visible_layer, persistent=True)
        self.update_layers()

        self.setSizeAdjustPolicy(self.AdjustToContents)

    def update_visible_layer(self, m, l):
        # make sure to re-fetch layers first
        self.update_layers()

        if self._use_active:
            currindex = self.findText(l)
            self.setCurrentIndex(currindex)

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
            currindex = self.findText(str(self.m.BM.bg_layer))
            self.setCurrentIndex(currindex)


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
        self._how = how
        self.custom_how = 1

        self.cid = None
        self.current_layer = None

        self.layerselector = AutoUpdateLayerDropdown(m=self.m, layers=layers, exclude=exclude)
        self.layerselector.update_layers() # do this before attaching the callback!
        self.layerselector.currentIndexChanged[str].connect(self.set_layer_callback)

        label = QtWidgets.QLabel("<b>Peek Layer</b>:")
        width = label.fontMetrics().boundingRect(label.text()).width()
        label.setFixedWidth(width + 5)

        dropdown = QtWidgets.QHBoxLayout()
        dropdown.addWidget(label)
        dropdown.addWidget(self.layerselector)

        self.b1 = QtWidgets.QRadioButton("🡇")
        self.b1.toggled.connect(self.bcb1)

        self.b2 = QtWidgets.QRadioButton("🡅")
        self.b2.toggled.connect(self.bcb2)

        self.b3 = QtWidgets.QRadioButton("🡆")
        self.b3.toggled.connect(self.bcb3)

        self.b4 = QtWidgets.QRadioButton("🡄")
        self.b4.toggled.connect(self.bcb4)

        self.b5 = QtWidgets.QRadioButton(f"rectangle\n(size={self.custom_how*100:.0f}%)")
        self.b5.toggled.connect(self.bcb5)
        self.b5.setChecked(True)

        self.b6 = QtWidgets.QRadioButton("🞑")
        self.b6.toggled.connect(self.bcb6)


        alphalabel = QtWidgets.QLabel("Transparency:")
        self.alphaslider = AlphaSlider(Qt.Horizontal)
        self.alphaslider.valueChanged.connect(self.add_peek_cb)
        self.alphaslider.setMaximumWidth(400)

        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.slider.setToolTip("set percentage")

        self.slider.setRange(0, 100)
        self.slider.setSingleStep(1)
        self.slider.setTickInterval(10)
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.slider.setValue(50)
        self.sider_value_changed(50)

        self.slider.setMinimumWidth(50)
        self.slider.valueChanged.connect(self.sider_value_changed)

        self.slider.setStyleSheet("""QToolTip {
                               font-family: "SansSerif";
                               font-size:10;
                               background-color: rgb(53, 53, 53);
                               color: white;
                               border: none;
                               }""")

        custom_how_layout = QtWidgets.QHBoxLayout()
        custom_how_layout.addWidget(self.b5)
        custom_how_layout.addWidget(self.slider)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addLayout(custom_how_layout)
        buttons.addWidget(self.b3)
        buttons.addWidget(self.b1)
        buttons.addWidget(self.b2)
        buttons.addWidget(self.b4)
        buttons.addWidget(self.b6)

        #buttons.setAlignment(Qt.AlignTop|Qt.AlignRight)


        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(dropdown)
        layout.addLayout(buttons)
        layout.addWidget(alphalabel)
        layout.addWidget(self.alphaslider)

        layout.setAlignment(Qt.AlignTop)

        self.setLayout(layout)

    @property
    def m(self):
        return self.parent.m

    def sider_value_changed(self, i):
        self.custom_how = i/100
        self.bcb5()

    def bcb1(self):
        if self.b1.isChecked():
            self.set_how("top")
            self.add_peek_cb()

    def bcb2(self):
        if self.b2.isChecked():
            self.set_how("bottom")
            self.add_peek_cb()

    def bcb3(self):
        if self.b3.isChecked():
            self.set_how("left")
            self.add_peek_cb()

    def bcb4(self):
        if self.b4.isChecked():
            self.set_how("right")
            self.add_peek_cb()

    def bcb5(self):
        if self.b5.isChecked():
            self.b5.setText(f"rectangle\n(size={self.custom_how*100:.0f}%)")
            self.set_how((self.custom_how, self.custom_how))
            self.add_peek_cb()

    def bcb6(self):
        if self.b6.isChecked():
            self.set_how("full")
            self.add_peek_cb()

    def set_layer_callback(self, l):
        if self.cid is not None:
            self.m.all.cb.click.remove(self.cid)
            self.cid = None
            self.current_layer = None

        if l == "":
            return

        self.cid = self.m.all.cb.click.attach.peek_layer(l, how=self._how, alpha=self.alphaslider.alpha)
        self.current_layer = l

    def set_how(self, how):
        self._how = how


    def add_peek_cb(self):
        if self.current_layer is None:
            return

        if self.cid is not None:
            self.m.all.cb.click.remove(self.cid)
            self.cid = None

        self.cid = self.m.all.cb.click.attach.peek_layer(self.current_layer, how=self._how, alpha=self.alphaslider.alpha)


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

        layout = QtWidgets.QHBoxLayout()

        #show = ShowLayerWidget(m=self.m)

        show = LayerEditor(m = self.m)

        new = NewWindowWidget()
        show.layout().addStretch(10)
        show.layout().addWidget(new)

        peek = PeekLayerWidget(parent=self.parent)


        leftlayout = QtWidgets.QVBoxLayout()
        leftlayout.addWidget(show)

        rightlayout = QtWidgets.QVBoxLayout()
        rightlayout.addWidget(peek)


        left = QtWidgets.QWidget()
        left.setLayout(leftlayout)

        right = QtWidgets.QWidget()
        right.setLayout(rightlayout)

        split = QtWidgets.QSplitter(Qt.Horizontal)
        split.addWidget(left)
        split.addWidget(right)


        #split.setSizes((500, 200))
        layout.addWidget(split)

        self.setLayout(layout)

    @property
    def m(self):
        return self.parent.m

def _str_to_bool(val):
    return val == "True"

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
        # self.widget_name.deleteLater()
        # self.widget_name = None

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

    def get_layer(self):#
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

    def open_file(self):
        file_path, info = self.do_open_file()

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

        # # TODO
        self.window = NewWindow(parent=self.parent)
        self.window.layout.addWidget(self)
        #self.window.setWindowFlags(Qt.WindowStaysOnTopHint)
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
   msg.show()
   #msg.exec_()


def to_float_none(s):
    if len(s) > 0:
        return float(s.replace(",", "."))
    else:
        return None


class PlotGeoTIFFWidget(PlotFileWidget):

    file_endings = (".tif", ".tiff")

    def do_open_file(self):
        import xarray as xar

        file_path = Path(QtWidgets.QFileDialog.getOpenFileName()[0])

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


        return file_path, info.getvalue()


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


    def do_open_file(self):
        import xarray as xar

        file_path = Path(QtWidgets.QFileDialog.getOpenFileName()[0])

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
            self.parameter.set_complete_vals(cols)

        return file_path, info.getvalue()


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

    def do_open_file(self):
        import pandas as pd

        file_path = Path(QtWidgets.QFileDialog.getOpenFileName()[0])

        head = pd.read_csv(file_path, nrows=50)
        cols = head.columns

        # set values for autocompletion
        self.x.set_complete_vals(cols)
        self.y.set_complete_vals(cols)
        self.parameter.set_complete_vals(cols)


        if len(cols) == 3:
            self.x.setText(cols[0])
            self.y.setText(cols[1])
            self.parameter.setText(cols[2])
        if len(cols) > 3:
            self.x.setText(cols[1])
            self.y.setText(cols[2])
            self.parameter.setText(cols[3])

        return file_path, head.__repr__()


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
        # TODO detect if all windows are closed, and if so call sys.exit!
        #sys.exit(0)

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


        t1 = QtWidgets.QLabel()
        t1.setAlignment(Qt.AlignBottom)

        b1 = self.FileButton("Open GeoTIFF", tab=parent, txt=t1, plotclass=PlotGeoTIFFWidget)
        b2 = self.FileButton("Open NetCDF", tab=parent, txt=t1, plotclass=PlotNetCDFWidget)
        b3 = self.FileButton("Open CSV", tab=parent, txt=t1, plotclass=PlotCSVWidget)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(b1, 0, 0)
        layout.addWidget(b2, 1, 0)
        layout.addWidget(b3, 2, 0)
        layout.addWidget(t1, 3, 0)


        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)


    class FileButton(QtWidgets.QPushButton):
        def __init__(self, *args, tab=None, plotclass=None, txt=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.tab = tab
            self.clicked.connect(self.new_file_tab)
            self.txt = txt

            self.PlotClass = plotclass

        @property
        def m(self):
            return self.tab.m

        def new_file_tab(self):

            if self.txt:
                self.txt.setText("")


            t = self.PlotClass(parent = self.tab.parent, tab=self.tab)

            try:
                t.open_file()
            except Exception:
                if self.txt:
                    self.txt.setText("File could not be opened...")
                import traceback
                show_error_popup(
                    text="There was an error while trying to open the file.",
                    title="Unable to open file.",
                    details=traceback.format_exc())

            return

            # if t.file_path is not None:
            #     name = t.file_path.stem
            # else:
            #     return

            # if len(name) > 10:
            #     name = name[:7] + "..."
            # self.tab.addTab(t, name)

            # tabindex = self.tab.indexOf(t)

            # self.tab.setCurrentIndex(tabindex)
            # self.tab.setTabToolTip(tabindex, str(t.file_path))


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

        b1 = QtWidgets.QPushButton('Save!')
        b1.clicked.connect(self.save_file)

        # resolution
        res = QtWidgets.QHBoxLayout()
        l1 = QtWidgets.QLabel("DPI:")
        self.dpi_input = QtWidgets.QLineEdit()
        validator = QtGui.QIntValidator()
        self.dpi_input.setValidator(validator)
        self.dpi_input.setText("200")

        res.addWidget(l1)
        res.addWidget(self.dpi_input)
        res.setAlignment(Qt.AlignTop)


        layout = QtWidgets.QGridLayout()
        layout.addLayout(res, 0, 0, 1, 2)
        layout.addWidget(b_edit, 1, 0)
        layout.addWidget(b1, 1, 1)

        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

    @property
    def m(self):
        return self.parent.m

    def save_file(self):
        savepath = QtWidgets.QFileDialog.getSaveFileName()[0]

        if savepath is not None:
            # self.m.figure.f.set_dpi(int(self.dpi_input.text()))
            # self.m.redraw()
            self.m.savefig(savepath, dpi=int(self.dpi_input.text()))
            # self.m.figure.f.set_dpi(100)
            # self.m.redraw()


class ControlTabs(QtWidgets.QTabWidget):
    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

        self.tab1 = ShowPeekLayerWidget(parent=self.parent)
        self.tab2 = OpenFileTabs(parent=self.parent)
        self.tab3 = DrawerWidget(parent=self.parent)
        self.tab4 = SaveFileWidget(parent=self.parent)

        self.tab5 = LayerEditor(m = self.m)

        self.addTab(self.tab1, r"Edit || Compare")
        self.addTab(self.tab2, "Open Files")
        self.addTab(self.tab3, "Draw Shapes")
        self.addTab(self.tab4, "Save")

    @property
    def m(self):
        return self.parent.m
