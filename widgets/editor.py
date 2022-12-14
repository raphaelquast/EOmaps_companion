from PyQt5 import QtCore, QtWidgets, QtGui

from .wms import AddWMSMenuButton
from .utils import GetColorWidget, AlphaSlider

from ..common import iconpath

from PyQt5.QtCore import Qt


class AddFeaturesMenuButton(QtWidgets.QPushButton):
    def __init__(self, *args, m=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.m = m

        self.props = dict(
            # alpha = 1,
            facecolor="r",
            edgecolor="g",
            linewidth=1,
            zorder=0,
        )

        feature_types = [i for i in dir(self.m.add_feature) if not i.startswith("_")]
        self.setText("Add Feature")
        # self.setMaximumWidth(200)

        width = self.fontMetrics().boundingRect(self.text()).width()
        self.setFixedWidth(width * 1.6)

        feature_menu = QtWidgets.QMenu()
        feature_menu.setStyleSheet("QMenu { menu-scrollable: 1;}")

        for featuretype in feature_types:
            try:
                sub_menu = feature_menu.addMenu(featuretype)

                sub_features = [
                    i
                    for i in dir(getattr(self.m.add_feature, featuretype))
                    if not i.startswith("_")
                ]
                for feature in sub_features:
                    action = sub_menu.addAction(str(feature))
                    action.triggered.connect(
                        self.menu_callback_factory(featuretype, feature)
                    )
            except:
                print("there was a problem with the NaturalEarth feature", featuretype)
                continue

        self.setMenu(feature_menu)
        self.clicked.connect(
            lambda: feature_menu.popup(self.mapToGlobal(self.menu_button.pos()))
        )

    def menu_callback_factory(self, featuretype, feature):
        def cb():
            if self.m.BM.bg_layer.startswith("_"):
                print(
                    "Adding features to temporary multi-layers is not supported!"
                    "Create a specific multi-layer (e.g. 'layer1|layer2' first!"
                )
                return
            try:
                getattr(getattr(self.m.add_feature, featuretype), feature)(
                    layer=self.m.BM.bg_layer, **self.props
                )

                self.m.BM.update()
            except Exception:
                import traceback

                print(
                    "---- adding the feature", featuretype, feature, "did not work----"
                )
                print(traceback.format_exc())

        return cb


class AddFeatureWidget(QtWidgets.QFrame):
    def __init__(self, m=None):

        super().__init__()
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)

        self.m = m

        self.selector = AddFeaturesMenuButton(m=self.m)
        self.selector.clicked.connect(self.update_props)

        self.colorselector = GetColorWidget()
        self.colorselector.cb_colorselected = self.update_on_color_selection

        self.alphaslider = AlphaSlider(Qt.Horizontal)
        self.alphaslider.valueChanged.connect(
            lambda i: self.colorselector.set_alpha(i / 100)
        )
        self.alphaslider.valueChanged.connect(self.update_props)

        self.linewidthslider = AlphaSlider(Qt.Horizontal)
        self.linewidthslider.valueChanged.connect(
            lambda i: self.colorselector.set_linewidth(i / 10)
        )
        self.linewidthslider.valueChanged.connect(self.update_props)

        self.zorder = QtWidgets.QLineEdit("0")
        validator = QtGui.QIntValidator()
        self.zorder.setValidator(validator)
        self.zorder.setMaximumWidth(30)
        self.zorder.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )
        self.zorder.textChanged.connect(self.update_props)

        zorder_label = QtWidgets.QLabel("zorder: ")
        zorder_label.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )

        zorder_layout = QtWidgets.QHBoxLayout()
        zorder_layout.addWidget(zorder_label)
        zorder_layout.addWidget(self.zorder)
        zorder_label.setAlignment(Qt.AlignRight | Qt.AlignCenter)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.colorselector, 0, 0, 2, 1)
        layout.addWidget(self.alphaslider, 0, 1)
        layout.addWidget(self.linewidthslider, 1, 1)
        layout.addLayout(zorder_layout, 0, 2)
        layout.addWidget(self.selector, 1, 2)

        # set stretch factor to expand the color-selector first
        layout.setColumnStretch(0, 1)

        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        # do this at the end to ensure everything has already been set up properly
        self.alphaslider.setValue(100)
        self.linewidthslider.setValue(20)

        self.update_props()

    def update_on_color_selection(self):
        self.update_alphaslider()
        self.update_props()

    def update_alphaslider(self):
        # to always round up to closest int use -(-x//1)
        self.alphaslider.setValue(-(-self.colorselector.alpha * 100 // 1))

    def update_props(self):
        self.selector.props.update(
            dict(
                facecolor=self.colorselector.facecolor.getRgbF(),
                edgecolor=self.colorselector.edgecolor.getRgbF(),
                linewidth=self.linewidthslider.alpha * 5,
                zorder=int(self.zorder.text()),
                # alpha = self.alphaslider.alpha,   # don't specify alpha! it interferes with the alpha of the colors!
            )
        )


class NewLayerWidget(QtWidgets.QFrame):
    def __init__(self, *args, m=None, **kwargs):

        super().__init__(*args, **kwargs)

        self.m = m

        self.new_layer_name = QtWidgets.QLineEdit()
        self.new_layer_name.setMaximumWidth(300)
        self.new_layer_name.setPlaceholderText("Create a new layer")

        self.new_layer_name.returnPressed.connect(self.new_layer)

        try:
            addwms = AddWMSMenuButton(m=self.m, new_layer=False)
        except:
            addwms = QtWidgets.QPushButton("WMS services unavailable")

        newlayer = QtWidgets.QHBoxLayout()
        newlayer.setAlignment(Qt.AlignLeft)

        newlayer.addWidget(addwms)
        newlayer.addStretch(1)
        newlayer.addWidget(self.new_layer_name)

        addfeature = AddFeatureWidget(m=self.m)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(addfeature)
        layout.addLayout(newlayer)
        self.setLayout(layout)

    def new_layer(self):
        layer = self.new_layer_name.text()
        if len(layer) == 0:
            QtWidgets.QToolTip.showText(
                self.mapToGlobal(self.new_layer_name.pos()),
                "Type a layer-name and press return!",
            )
            return

        m2 = self.m.new_layer(layer)
        self.m.show_layer(layer)

        return m2


class ArtistEditor(QtWidgets.QWidget):
    def __init__(self, m=None):

        super().__init__()

        self.m = m
        self._hidden_artists = dict()

        self.tabs = QtWidgets.QTabWidget()

        newlayer = NewLayerWidget(m=self.m)
        newlayer.new_layer_name.returnPressed.connect(self.populate)

        splitter = QtWidgets.QSplitter(Qt.Vertical)
        splitter.addWidget(newlayer)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(splitter)

        self.setLayout(layout)

        self.populate()

        self.tabs.tabBarClicked.connect(self.tabchanged)
        self.tabs.currentChanged.connect(self.populate_layer)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_handler)

        self._current_tab_idx = None
        self._current_tab_name = None

        self.m.BM.on_layer(self.color_active_tab, persistent=True)

        self.m.BM._on_add_bg_artist.append(self.populate)
        self.m.BM._on_remove_bg_artist.append(self.populate)

    def close_handler(self, index):
        layer = self.tabs.tabText(index)

        self._msg = QtWidgets.QMessageBox(self)
        self._msg.setIcon(QtWidgets.QMessageBox.Question)
        self._msg.setText(f"Do you really want to delete the layer '{layer}'")
        self._msg.setWindowTitle(f"Delete layer: '{layer}'?")

        self._msg.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        self._msg.buttonClicked.connect(lambda: self.do_close_tab(index))

        ret = self._msg.show()

    def do_close_tab(self, index):

        if self._msg.standardButton(self._msg.clickedButton()) != self._msg.Yes:
            return

        layer = self.tabs.tabText(index)

        if self.m.layer == layer:
            print("can't delete the base-layer")
            return

        for m in list(self.m._children):
            if layer == m.layer:
                m.cleanup()

        if self.m.BM._bg_layer == layer:
            try:
                switchlayer = next((i for i in self.m.BM._bg_artists if i != layer))
                self.m.show_layer(switchlayer)
            except StopIteration:
                # don't allow deletion of last layer
                print("you cannot delete the last available layer!")
                return

        if layer in list(self.m.BM._bg_artists):
            for a in self.m.BM._bg_artists[layer]:
                self.m.BM.remove_bg_artist(a)
                a.remove()
            del self.m.BM._bg_artists[layer]

        if layer in self.m.BM._bg_layers:
            del self.m.BM._bg_layers[layer]

        # also remove not-yet-fetched WMS services!
        if layer in self.m.BM._on_layer_activation:
            del self.m.BM._on_layer_activation[layer]

        self.populate()

    def color_active_tab(self, m=None, l=None):

        defaultcolor = self.tabs.palette().color(self.tabs.foregroundRole())
        activecolor = QtGui.QColor(50, 200, 50)
        multicolor = QtGui.QColor(200, 50, 50)

        for i in range(self.tabs.count()):
            layer = self.tabs.tabText(i)

            active_layers = self.m.BM._bg_layer.split("|")
            color = activecolor if len(active_layers) == 1 else multicolor
            if layer in active_layers:
                self.tabs.tabBar().setTabTextColor(i, color)
            else:
                self.tabs.tabBar().setTabTextColor(i, defaultcolor)

            if l == layer:
                self.tabs.tabBar().setTabTextColor(i, activecolor)

    def _get_artist_layout(self, a, layer):
        # label
        name = str(a)
        if len(name) > 50:
            label = QtWidgets.QLabel(name[:46] + "... >")
            label.setToolTip(name)
        else:
            label = QtWidgets.QLabel(name)
        label.setStyleSheet(
            "border-radius: 5px;"
            "border-style: solid;"
            "border-width: 1px;"
            "border-color: rgba(0, 0, 0,100);"
        )
        label.setAlignment(Qt.AlignCenter)
        label.setMaximumHeight(25)

        # remove
        b_r = QtWidgets.QToolButton()
        b_r.setText("????")
        b_r.setAutoRaise(True)
        b_r.setStyleSheet("QToolButton {color: red;}")
        b_r.clicked.connect(self.remove(artist=a, layer=layer))

        # show / hide
        b_sh = QtWidgets.QToolButton()
        b_sh.setAutoRaise(True)

        # #b_sh.setStyleSheet("background-color : #79a76e")
        if a in self._hidden_artists.get(layer, []):
            b_sh.setIcon(QtGui.QIcon(str(iconpath / "eye_closed.png")))
        else:
            b_sh.setIcon(QtGui.QIcon(str(iconpath / "eye_open.png")))

        b_sh.clicked.connect(self.show_hide(artist=a, layer=layer))

        # zorder
        l_z = QtWidgets.QLabel("zoder:")
        b_z = QtWidgets.QLineEdit()
        b_z.setToolTip("zorder")
        b_z.setMinimumWidth(25)
        b_z.setMaximumWidth(25)
        validator = QtGui.QIntValidator()
        b_z.setValidator(validator)
        b_z.setText(str(a.get_zorder()))
        b_z.returnPressed.connect(self.set_zorder(artist=a, layer=layer, widget=b_z))

        # alpha
        alpha = a.get_alpha()
        if alpha is not None:
            l_a = QtWidgets.QLabel("alpha:")
            b_a = QtWidgets.QLineEdit()
            b_a.setToolTip("alpha")

            b_a.setMinimumWidth(25)
            b_a.setMaximumWidth(50)

            validator = QtGui.QDoubleValidator(0.0, 1.0, 3)
            validator.setLocale(QtCore.QLocale("en_US"))

            b_a.setValidator(validator)
            b_a.setText(str(alpha))
            b_a.returnPressed.connect(self.set_alpha(artist=a, layer=layer, widget=b_a))
        else:
            l_a, b_a = None, None

        # linewidth
        try:
            lw = a.get_linewidth()
            if isinstance(lw, list) and len(lw) > 1:
                pass
            else:
                lw = lw[0]

            if lw is not None:
                l_lw = QtWidgets.QLabel("linewidth:")
                b_lw = QtWidgets.QLineEdit()
                b_lw.setToolTip("linewidth")

                b_lw.setMinimumWidth(25)
                b_lw.setMaximumWidth(50)
                validator = QtGui.QDoubleValidator(0, 100, 3)
                validator.setLocale(QtCore.QLocale("en_US"))

                b_lw.setValidator(validator)
                b_lw.setText(str(lw))
                b_lw.returnPressed.connect(
                    self.set_linewidth(artist=a, layer=layer, widget=b_lw)
                )
            else:
                l_lw, b_lw = None, None
        except Exception:
            l_lw, b_lw = None, None

        # color
        from .utils import GetColorWidget

        try:
            facecolor = a.get_facecolor()
            edgecolor = a.get_edgecolor()
            if facecolor.shape[0] != 1:
                facecolor = (0, 0, 0, 0)
                use_cmap = True
            else:
                facecolor = (facecolor.squeeze() * 255).tolist()
                use_cmap = False

            if edgecolor.shape[0] != 1:
                edgecolor = (0, 0, 0, 0)
            else:
                edgecolor = (edgecolor.squeeze() * 255).tolist()

            b_c = GetColorWidget(facecolor=facecolor, edgecolor=edgecolor)
            b_c.cb_colorselected = self.set_color(
                artist=a, layer=layer, colorwidget=b_c
            )
            b_c.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)

            b_c.setSizePolicy(
                QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
            )
            b_c.setMaximumWidth(25)

        except:
            b_c = None
            use_cmap = True
            pass

        # cmap
        from .utils import CmapDropdown

        if use_cmap is True:
            try:
                cmap = a.get_cmap()
                b_cmap = CmapDropdown(startcmap=cmap.name)
                b_cmap.activated.connect(
                    self.set_cmap(artist=a, layer=layer, widget=b_cmap)
                )
            except:
                b_cmap = None
                pass
        else:
            b_cmap = None

        layout = []
        layout.append((b_sh, 0))  # show hide
        if b_c is not None:
            layout.append((b_c, 1))  # color
        layout.append((b_z, 2))  # zorder

        layout.append((label, 3))  # title
        if b_lw is not None:
            layout.append((b_lw, 4))  # linewidth

        if b_a is not None:
            layout.append((b_a, 5))  # alpha

        if b_cmap is not None:
            layout.append((b_cmap, 5))  # cmap

        layout.append((b_r, 6))  # remove

        return layout

    def populate_layer(self):
        layer = self.tabs.tabText(self.tabs.currentIndex())
        widget = self.tabs.currentWidget()

        if widget is None:
            # ignore events without tabs (they happen on re-population of the tabs)
            return

        layout = QtWidgets.QGridLayout()
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # make sure that we don't create an empty entry in the defaultdict!
        # TODO avoid using defaultdicts!!
        if layer in self.m.BM._bg_artists:
            artists = self.m.BM._bg_artists[layer]
        else:
            artists = []

        for i, a in enumerate(
            sorted((*artists, *self._hidden_artists.get(layer, [])), key=str)
        ):

            a_layout = self._get_artist_layout(a, layer)
            for art, pos in a_layout:
                layout.addWidget(art, i, pos)

        tabwidget = QtWidgets.QWidget()
        tabwidget.setLayout(layout)

        widget.setWidget(tabwidget)

    def populate(self):
        self._current_tab_idx = self.tabs.currentIndex()
        self._current_tab_name = self.tabs.tabText(self._current_tab_idx)

        alllayers = sorted(list(self.m._get_layers()))
        self.tabs.clear()

        self.tabwidgets = dict()
        for i, layer in enumerate(alllayers):

            layout = QtWidgets.QGridLayout()
            layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

            if layer.startswith("_"):  # or "|" in layer:
                # make sure the currently opened tab is always added (even if empty)
                if layer != self._current_tab_name:
                    # don't show empty layers
                    continue

            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)

            self.tabs.addTab(scroll, layer)

            if layer == "all" or layer == self.m.layer:
                tabbar = self.tabs.tabBar()
                # don't show the close button for this tab
                tabbar.setTabButton(self.tabs.count() - 1, tabbar.RightSide, None)

        for i in range(self.tabs.count()):
            self.tabs.setTabToolTip(
                i, "Use (control + click) to switch the visible layer!"
            )

        try:
            # restore the previously opened tab
            found = False
            ntabs = self.tabs.count()
            if ntabs > 0 and self._current_tab_name != "":
                for i in range(ntabs):
                    if self.tabs.tabText(i) == self._current_tab_name:
                        self.tabs.setCurrentIndex(self._current_tab_idx)
                        found = True
                        break

                if found is False:
                    print(
                        "Unable to restore previously opened tab "
                        + f"'{self._current_tab_name}'!"
                    )
                    self.tabs.setCurrentIndex(self.m.BM._bg_layer)
        except:
            print("unable to activate tab")
            pass

        self.color_active_tab()

    def tabchanged(self, index):
        # TODO
        # modifiers are only released if the canvas has focus while the event happens!!
        # (e.g. button is released but event is not fired on the canvas)
        # see https://stackoverflow.com/questions/60978379/why-alt-modifier-does-not-trigger-key-release-event-the-first-time-you-press-it

        # simply calling  canvas.setFocus() does not work!

        # for w in QtWidgets.QApplication.topLevelWidgets():
        #     if w.inherits('QMainWindow'):
        #         w.canvas.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        #         w.canvas.setFocus()
        #         w.raise_()
        #         print("raising", w, w.canvas)

        layer = self.tabs.tabText(index)

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            if layer != "":
                self.m.show_layer(layer)
                # TODO this is a workaround since modifier-releases are not
                # forwarded to the canvas if it is not in focus
                self.m.figure.f.canvas.key_release_event("control")

        elif modifiers == Qt.ShiftModifier:
            currlayers = [i for i in self.m.BM._bg_layer.split("|") if i != "_"]

            for l in (i for i in layer.split("|") if i != "_"):
                if l not in currlayers:
                    currlayers.append(l)
                else:
                    currlayers.remove(l)

            if len(currlayers) > 1:
                uselayer = "_|" + "|".join(sorted(currlayers))

                self.m.show_layer(uselayer)
            else:
                self.m.show_layer(layer)
            # TODO this is a workaround since modifier-releases are not
            # forwarded to the canvas if it is not in focus
            self.m.figure.f.canvas.key_release_event("shift")

    def set_color(self, artist, layer, colorwidget):
        def cb():
            artist.set_fc(colorwidget.facecolor.getRgbF())
            artist.set_edgecolor(colorwidget.edgecolor.getRgbF())

            self.m.redraw()

        return cb

    def _do_remove(self, artist, layer):
        if self._msg.standardButton(self._msg.clickedButton()) != self._msg.Yes:
            return

        self.m.BM.remove_bg_artist(artist, layer)

        if artist in self._hidden_artists.get(layer, []):
            self._hidden_artists[layer].remove(artist)

        artist.remove()

        self.populate()
        self.m.redraw()

    def remove(self, artist, layer):
        def cb():
            self._msg = QtWidgets.QMessageBox(self)
            self._msg.setIcon(QtWidgets.QMessageBox.Question)
            self._msg.setWindowTitle(f"Delete artist?")
            self._msg.setText(
                "Do you really want to delete the following artist"
                + f"from the layer '{layer}'?\n\n"
                + f"    '{artist}'"
            )

            self._msg.setStandardButtons(
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            self._msg.buttonClicked.connect(lambda: self._do_remove(artist, layer))
            ret = self._msg.show()

        return cb

    def show_hide(self, artist, layer):
        def cb():
            if artist in self.m.BM._bg_artists[layer]:
                self._hidden_artists.setdefault(layer, []).append(artist)
                self.m.BM.remove_bg_artist(artist, layer=layer)
                artist.set_visible(False)
            else:
                if layer in self._hidden_artists:
                    try:
                        self._hidden_artists[layer].remove(artist)
                    except ValueError:
                        print("could not find hidden artist in _hidden_artists list")
                        pass

                try:
                    self.m.BM.add_bg_artist(artist, layer=layer)
                except:
                    print("problem unhiding", artist, "from layer", layer)

            self.m.redraw()

        return cb

    def set_zorder(self, artist, layer, widget):
        def cb():
            val = widget.text()
            if len(val) > 0:
                artist.set_zorder(int(val))

            self.m.redraw()

        return cb

    def set_alpha(self, artist, layer, widget):
        def cb():
            val = widget.text()
            if len(val) > 0:
                artist.set_alpha(float(val.replace(",", ".")))

            self.m.redraw()

        return cb

    def set_linewidth(self, artist, layer, widget):
        def cb():
            val = widget.text()
            if len(val) > 0:
                artist.set_linewidth(float(val.replace(",", ".")))

            self.m.redraw()

        return cb

    def set_cmap(self, artist, layer, widget):
        def cb():
            val = widget.currentText()
            if len(val) > 0:
                artist.set_cmap(val)

            self.m.redraw()

        return cb
