# -*- coding: utf-8 -*-
"""
SHP <-> TXT 坐标互转 QGIS 插件
"""


def classFactory(iface):
    from .plugin import ShpTxtConverterPlugin
    return ShpTxtConverterPlugin(iface)
