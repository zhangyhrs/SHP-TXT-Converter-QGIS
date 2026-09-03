# SHP TXT Coordinate Converter for QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.22%2B-589632?logo=qgis&logoColor=white)](https://qgis.org/)
![Language](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)
[![License](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)](LICENSE)

**English | [简体中文](README_ZH.md)**

<p align="center">
  <img src="shp_txt_converter/icons/icon_v103.png" alt="SHP TXT Coordinate Converter" width="128">
</p>

A lightweight QGIS plugin for **bidirectional conversion between ESRI Shapefile and structured TXT coordinate files**. It is designed for surveying, cadastral, natural-resources and GIS workflows where coordinate lists need to be exported, edited, checked or restored as vector geometry.

## Features

- SHP → TXT coordinate export
- TXT → SHP geometry restoration
- Point, LineString and Polygon support
- Polygon outer/inner ring preservation
- Multiple features in one TXT file using `feature_id` blocks
- Common CGCS2000 3-degree and 6-degree zones, WGS84, Web Mercator and custom EPSG codes
- Optional CRS transformation using QGIS-bundled GDAL/OGR
- Traditional GIS X/Y axis order for GDAL 3+/PROJ compatibility
- Background conversion thread to keep the QGIS interface responsive
- No external Python package dependencies

## Interface

<p align="center">
  <img src="https://raw.githubusercontent.com/zhangyhrs/SHP-TXT-Converter-QGIS/main/docs/plugin-interface.png" alt="SHP TXT Coordinate Converter interface" width="900">
</p>

## TXT format

```text
# feature_id=1 geom_type=POLYGON part=outer
500000.000, 3300000.000
500100.000, 3300000.000
500100.000, 3300100.000
500000.000, 3300000.000
```

## Installation

### QGIS Official Plugin Repository

Open **Plugins → Manage and Install Plugins** in QGIS, search for **SHP TXT Converter**, and install it after the plugin is published in the official repository.

### Install from ZIP

Download the QGIS installation ZIP, then open **Plugins → Manage and Install Plugins → Install from ZIP** and select the package. Keep the package structure unchanged; the ZIP must contain the top-level directory `shp_txt_converter`.

## Compatibility

- QGIS 3.22–3.99
- Windows / Linux / macOS, subject to the GDAL/OGR build bundled with QGIS

## Project links

[Source code](https://github.com/zhangyhrs/SHP-TXT-Converter-QGIS) · [Changelog](CHANGELOG.md) · [Report a bug](https://github.com/zhangyhrs/SHP-TXT-Converter-QGIS/issues)

## Follow & Connect

Follow the **测绘地信** WeChat Official Account for surveying, remote sensing, natural-resources and GIS content. You can also join the **测绘地理信息共享中心** Knowledge Planet community for tools, resources and technical discussions.

<table>
  <tr>
    <td align="center" width="50%"><strong>WeChat Official Account: 测绘地信</strong></td>
    <td align="center" width="50%"><strong>Knowledge Planet: 测绘地理信息共享中心</strong></td>
  </tr>
  <tr>
    <td align="center"><img src="https://raw.githubusercontent.com/zhangyhrs/GeoStar-Selector-QGIS/main/assets/wechat-official-account.png" alt="WeChat Official Account: 测绘地信" width="100%"></td>
    <td align="center"><img src="https://raw.githubusercontent.com/zhangyhrs/GeoStar-Selector-QGIS/main/assets/knowledge-planet.jpg" alt="Knowledge Planet: 测绘地理信息共享中心" width="64%"></td>
  </tr>
</table>

## Author

**Zhang Y.H.** · GitHub [@zhangyhrs](https://github.com/zhangyhrs) · Email: `zhangyhcumt@163.com`

Related: [GeoStar Selector for QGIS](https://github.com/zhangyhrs/GeoStar-Selector-QGIS) · [SHP2KMZ Tool](https://github.com/zhangyhrs/SHP2KMZ_Tool) · [Map Tile Downloader](https://github.com/zhangyhrs/map_tile_downloader)

## License

[GPL-2.0-or-later](LICENSE)
