from PyQt5 import QtCore, QtWidgets


# class AddWMS(QtWidgets.QWidget):
#     signal_layer_created = QtCore.Signal(str)

#     def __init__(self, *args, m, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.m = m

#         osm = AddWMS_OSM(m=self.m)
#         osm.signal_layer_created.connect(self._layer_created)

#         s1gbm = AddWMS_S1GBM(m=self.m)
#         s1gbm.signal_layer_created.connect(self._layer_created)

#         esawc = AddWMS_ESA_WorldCover(m=self.m)
#         esawc.signal_layer_created.connect(self._layer_created)

#         s2cloud = AddWMS_S2_cloudless(m=self.m)
#         s2cloud.signal_layer_created.connect(self._layer_created)


#         layout = QtWidgets.QVBoxLayout()
#         layout.addWidget(osm)
#         layout.addWidget(s1gbm)
#         layout.addWidget(esawc)
#         layout.addWidget(s2cloud)

#         layout.setAlignment(QtCore.Qt.AlignTop)

#         self.setLayout(layout)

#     def _layer_created(self, layer):
#         self.signal_layer_created.emit(layer)




# class AddWMSBase(QtWidgets.QWidget):
#     signal_layer_created = QtCore.Signal(str)
#     layer_prefix = "WMS_"
#     name = "WMS"
#     drop_items = []

#     def __init__(self, *args, m, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.m = m

#         self.t = QtWidgets.QLabel(self.name)
#         self.b = QtWidgets.QPushButton("Add")
#         self.b.clicked.connect(self.add_to_layer)
#         self.b2 = QtWidgets.QPushButton("New")
#         self.b2.clicked.connect(self.new_layer)

#         self.drop = QtWidgets.QComboBox()

#         layout = QtWidgets.QHBoxLayout()
#         layout.setAlignment(QtCore.Qt.AlignRight)
#         layout.setContentsMargins(0,0,0,0)

#         layout.addWidget(self.t)
#         layout.addWidget(self.drop)
#         layout.addWidget(self.b)
#         layout.addWidget(self.b2)

#         self.setLayout(layout)

#     def fill_dropdown(self):
#         for key in self.drop_items:
#             self.drop.addItem(key)

#     def do_add_layer(self, wmslayer, layer):
#         raise NotImplementedError

#     def add_to_layer(self):
#         wmslayer = self.drop.currentText()
#         layer = self.m.BM.bg_layer
#         self.do_add_layer(wmslayer=wmslayer, layer=layer)
#         self.m.show_layer(layer)
#         self.signal_layer_created.emit(layer)

#     def new_layer(self):
#         wmslayer = self.drop.currentText()
#         layer = self.layer_prefix + wmslayer
#         self.do_add_layer(wmslayer=wmslayer, layer=layer)
#         self.m.show_layer(layer)
#         self.signal_layer_created.emit(layer)

# class AddWMS_S1GBM(AddWMSBase):
#     layer_prefix = "S1GBM_"
#     name = "S1GBM"

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.drop_items = ["vv", "vh"]
#         self.fill_dropdown()

#     def do_add_layer(self, wmslayer, layer):
#         getattr(self.m.add_wms.S1GBM.add_layer, wmslayer)(layer=layer)

# class AddWMS_OSM(AddWMSBase):
#     layer_prefix = "OSM_"
#     name = "OpenStreetMap"

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.drop_items = [key for key in self.m.add_wms.OpenStreetMap.add_layer.__dict__.keys()
#                            if not (key in ["m"] or key.startswith("_"))]
#         self.fill_dropdown()

#     def do_add_layer(self, wmslayer, layer):
#         getattr(self.m.add_wms.OpenStreetMap.add_layer, wmslayer)(layer=layer)


# class AddWMS_ESA_WorldCover(AddWMSBase):
#     layer_prefix = ""
#     name = "ESA WorldCover"

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.drop_items = [key for key in self.m.add_wms.ESA_WorldCover.layers
#                            if (key.startswith("WORLDCOVER") or key.startswith("COP"))
#                            ]
#         self.fill_dropdown()


#     def do_add_layer(self, wmslayer, layer):
#         getattr(self.m.add_wms.ESA_WorldCover.add_layer, wmslayer)(layer=layer)

# class AddWMS_S2_cloudless(AddWMSBase):
#     layer_prefix = "S2_"
#     name = "S2 cloudless"

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.drop_items = sorted(self.m.add_wms.S2_cloudless.layers)
#         self.fill_dropdown()


#     def do_add_layer(self, wmslayer, layer):
#         getattr(self.m.add_wms.S2_cloudless.add_layer, wmslayer)(layer=layer)






class WMS_OSM():
    layer_prefix = "OSM_"
    name = "OpenStreetMap"

    def __init__(self, m=None):
        self.m = m
        self.wmslayers = [key for key in self.m.add_wms.OpenStreetMap.add_layer.__dict__.keys()
                          if not (key in ["m"] or key.startswith("_"))]

    def do_add_layer(self, wmslayer, layer):
        getattr(self.m.add_wms.OpenStreetMap.add_layer, wmslayer)(layer=layer)

class WMS_S2_cloudless():
    layer_prefix = "S2_"
    name = "S2 cloudless"

    def __init__(self, m=None):
        self.m = m
        self.wmslayers = sorted(self.m.add_wms.S2_cloudless.layers)

    def do_add_layer(self, wmslayer, layer):
        getattr(self.m.add_wms.S2_cloudless.add_layer, wmslayer)(layer=layer)


class WMS_ESA_WorldCover():
    layer_prefix = ""
    name = "ESA WorldCover"

    def __init__(self, m=None):
        self.m = m
        self.wmslayers = [key for key in self.m.add_wms.ESA_WorldCover.layers
                          if (key.startswith("WORLDCOVER") or key.startswith("COP"))
                          ]

    def do_add_layer(self, wmslayer, layer):
        getattr(self.m.add_wms.ESA_WorldCover.add_layer, wmslayer)(layer=layer)


class WMS_S1GBM():
    layer_prefix = "S1GBM_"
    name = "S1GBM"

    def __init__(self, m=None):
        self.m = m
        self.wmslayers = ["vv", "vh"]

    def do_add_layer(self, wmslayer, layer):
        getattr(self.m.add_wms.S1GBM.add_layer, wmslayer)(layer=layer)


class AddWMSMenuButton(QtWidgets.QPushButton):
    def __init__(self, *args, m=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.m = m


        wms_dict = {"OpenStreetMap": WMS_OSM(m = self.m),
                    "S2 Cloudless": WMS_S2_cloudless(m=self.m),
                    "ESA WorldCover": WMS_ESA_WorldCover(m=self.m),
                    "S1GBM:": WMS_S1GBM(m=self.m)}


        self.setText("Add WMS")
        self.setMaximumWidth(200)

        feature_menu = QtWidgets.QMenu()
        feature_menu.setStyleSheet("QMenu { menu-scrollable: 1;}")

        for wmsname, wms in wms_dict.items():
            sub_menu = feature_menu.addMenu(wmsname)

            sub_features = wms.wmslayers
            for wmslayer in sub_features:
                action = sub_menu.addAction(wmslayer)
                action.triggered.connect(self.menu_callback_factory(wms, wmslayer))

        self.setMenu(feature_menu)
        self.clicked.connect(lambda:feature_menu.popup(self.mapToGlobal(self.menu_button.pos())))


    def menu_callback_factory(self, wms, wmslayer):

        def wms_cb():
            wms.do_add_layer(wmslayer, layer=self.m.BM.bg_layer)

        return wms_cb
        #return lambda: wms.do_add_layer(wmslayer, layer=self.m.BM.bg_layer)
