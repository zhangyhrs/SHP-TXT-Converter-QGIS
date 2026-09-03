# -*- coding: utf-8 -*-
"""QGIS plugin entry point for SHP TXT Coordinate Converter."""

import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon


def resource_path(relative_path: str) -> str:
    return os.path.join(os.path.dirname(__file__), relative_path)


class ShpTxtConverterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self):
        icon_path = resource_path("icons/icon.png")
        self.action = QAction(
            QIcon(icon_path),
            "SHP TXT Coordinate Converter",
            self.iface.mainWindow(),
        )
        self.action.setObjectName("shpTxtConverterAction")
        self.action.setStatusTip("Convert coordinates between Shapefile and TXT")
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("SHP TXT Coordinate Converter", self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu("SHP TXT Coordinate Converter", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.deleteLater()
            self.action = None

    def run(self):
        from .dialog import ShpTxtConverterDialog
        if self.dialog is None:
            self.dialog = ShpTxtConverterDialog(self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
