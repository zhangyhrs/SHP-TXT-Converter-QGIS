# SHP TXT Coordinate Converter for QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.22%2B-589632?logo=qgis&logoColor=white)](https://qgis.org/)
![Language](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)
[![License](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)](LICENSE)

**[English](README.md) | 简体中文**

<p align="center">
  <img src="shp_txt_converter/icons/icon_v103.png" alt="SHP TXT Coordinate Converter" width="128">
</p>

**SHP TXT Coordinate Converter** 是一款用于 **Shapefile 与结构化 TXT 坐标文件双向转换** 的 QGIS 插件，适用于测绘、地籍、自然资源调查、界址数据处理以及常规 GIS 坐标成果整理。

## 主要功能

- SHP → TXT：按要素导出坐标
- TXT → SHP：根据结构化坐标块恢复几何
- 支持 Point、LineString、Polygon
- 支持面要素外环、内环及多部件结构
- 一个 TXT 文件可保存多个要素，并通过 `feature_id` 分块
- 内置 CGCS2000 常用 3°带、6°带、WGS84、Web Mercator
- 支持自定义 EPSG 坐标系
- 支持输入、输出坐标系转换
- 针对 GDAL 3+/PROJ 采用传统 GIS X/Y 轴顺序
- 后台线程执行转换，避免阻塞 QGIS 主界面
- 无需额外安装第三方 Python 包

## 软件界面

<p align="center">
  <img src="https://raw.githubusercontent.com/zhangyhrs/SHP-TXT-Converter-QGIS/main/docs/plugin-interface.png" alt="SHP TXT Coordinate Converter 软件界面" width="900">
</p>

## TXT 格式示例

```text
# feature_id=1 geom_type=POLYGON part=outer
500000.000, 3300000.000
500100.000, 3300000.000
500100.000, 3300100.000
500000.000, 3300000.000
```

## 安装方法

### QGIS 官方插件库

插件通过审核发布后，可在 QGIS 中打开 **插件 → 管理并安装插件**，搜索 **SHP TXT Converter** 并直接安装。

### ZIP 离线安装

下载 QGIS 插件安装 ZIP，在 QGIS 中打开 **插件 → 管理并安装插件 → 从 ZIP 安装**，选择插件包即可。请保持安装包目录结构不变，ZIP 内唯一顶层目录应为 `shp_txt_converter`。

## 兼容性

- QGIS 3.22–3.99
- Windows / Linux / macOS，具体取决于 QGIS 自带的 GDAL/OGR 环境

## 使用说明

TXT 文件本身不保存 CRS 信息。如果需要将 TXT 坐标转换到另一个坐标系，应明确设置输入 EPSG；若输出坐标系留空，则保持输入坐标系。SHP 输入则可使用“自动识别/留空”读取文件自身 CRS。

## 项目入口

[源代码](https://github.com/zhangyhrs/SHP-TXT-Converter-QGIS) · [更新记录](CHANGELOG.md) · [问题反馈](https://github.com/zhangyhrs/SHP-TXT-Converter-QGIS/issues)

## 关注与交流

欢迎关注微信公众号 **测绘地信**，获取测绘、遥感、自然资源与 GIS 技术内容；也可加入知识星球 **测绘地理信息共享中心**，交流软件工具、专业资料和行业技术。

<table>
  <tr>
    <td align="center" width="50%"><strong>微信公众号：测绘地信</strong></td>
    <td align="center" width="50%"><strong>知识星球：测绘地理信息共享中心</strong></td>
  </tr>
  <tr>
    <td align="center"><img src="https://raw.githubusercontent.com/zhangyhrs/GeoStar-Selector-QGIS/main/assets/wechat-official-account.png" alt="微信公众号：测绘地信" width="100%"></td>
    <td align="center"><img src="https://raw.githubusercontent.com/zhangyhrs/GeoStar-Selector-QGIS/main/assets/knowledge-planet.jpg" alt="知识星球：测绘地理信息共享中心" width="64%"></td>
  </tr>
</table>

## 作者

**Zhang Y.H.** · GitHub [@zhangyhrs](https://github.com/zhangyhrs)

相关工具：[GeoStar Selector for QGIS](https://github.com/zhangyhrs/GeoStar-Selector-QGIS) · [SHP2KMZ Tool](https://github.com/zhangyhrs/SHP2KMZ_Tool) · [Map Tile Downloader](https://github.com/zhangyhrs/map_tile_downloader)

## 许可证

[GPL-2.0-or-later](LICENSE)
