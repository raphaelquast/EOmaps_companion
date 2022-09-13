from PyQt5 import QtCore, QtWidgets
from .wms_utils import AddWMSMenuButton


class LayerEditor(QtWidgets.QWidget):
    def __init__(self, *args, m=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.m = m

        self.new_layer_name = QtWidgets.QLineEdit()
        self.new_layer_name.setPlaceholderText("A new layer")

        new_layer_button = QtWidgets.QPushButton("Create")
        new_layer_button.clicked.connect(self.new_layer)

        addfeature = AddFeaturesMenuButton(m=self.m)
        addwms = AddWMSMenuButton(m=self.m)

        from .utils import AutoUpdateLayerDropdown, CmapDropdown

        visiblelayer = AutoUpdateLayerDropdown(m=self.m, use_active=True, empty_ok=False)
        visiblelayer.activated[str].connect(self.set_layer_callback)

        newlayer = QtWidgets.QHBoxLayout()
        newlayer.addWidget(self.new_layer_name)
        newlayer.addWidget(new_layer_button)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(visiblelayer, 0, 0, 1, 2)
        layout.addLayout(newlayer, 0, 2, 1, 2)
        layout.addWidget(addfeature, 1, 0)
        layout.addWidget(addwms, 1, 1)


        self.setLayout(layout)


    def new_layer(self):
        layer = self.new_layer_name.text()
        if len(layer) == 0:
            layer = self.new_layer_name.placeholderText()

        m2 = self.m.new_layer(layer)
        self.m.show_layer(layer)

        return m2

    def set_layer_callback(self, l):
        if l == "":
            return

        try:
            self.m.show_layer(l)
        except Exception:
            print(f"showing the layer '{l}' did not work")



class AddFeaturesMenuButton(QtWidgets.QPushButton):
    def __init__(self, *args, m=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.m = m


        feature_types = [i for i in dir(self.m.add_feature) if not i.startswith("_")]
        self.setText("Add Feature")
        self.setMaximumWidth(200)

        feature_menu = QtWidgets.QMenu()
        feature_menu.setStyleSheet("QMenu { menu-scrollable: 1;}")

        for featuretype in feature_types:
            sub_menu = feature_menu.addMenu(featuretype)

            sub_features = [i for i in dir(getattr(self.m.add_feature, featuretype)) if not i.startswith("_")]
            for feature in sub_features:
                action = sub_menu.addAction(str(feature))
                action.triggered.connect(self.menu_callback_factory(featuretype, feature))

        self.setMenu(feature_menu)
        self.clicked.connect(lambda:feature_menu.popup(self.mapToGlobal(self.menu_button.pos())))


    def menu_callback_factory(self, featuretype, feature):
        return lambda: getattr(getattr(self.m.add_feature, featuretype), feature)(layer = self.m.BM.bg_layer)
