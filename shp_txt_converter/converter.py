# -*- coding: utf-8 -*-
"""
SHP <-> TXT 坐标互转核心逻辑
基于 OGR/GDAL（QGIS 内置）
"""

import os
import re

from osgeo import ogr, osr

# =========================================================
# 坐标系 / 坐标转换工具
# =========================================================

def force_traditional_gis_order(srs):
    if srs is None:
        return None
    try:
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    except (AttributeError, TypeError):
        # Older GDAL/OGR builds may not expose axis mapping strategy.
        return srs
    return srs


def clone_srs_with_gis_order(srs):
    if srs is None:
        return None
    try:
        srs2 = srs.Clone()
    except Exception:
        srs2 = srs
    return force_traditional_gis_order(srs2)


def get_srs_from_epsg(epsg):
    if epsg is None or str(epsg).strip() == "":
        return None
    srs = osr.SpatialReference()
    result = srs.ImportFromEPSG(int(epsg))
    if result != 0:
        raise ValueError(f"无效的 EPSG 代码: {epsg}")
    force_traditional_gis_order(srs)
    return srs


class SafeCoordinateTransformer:
    """稳定的坐标转换包装器，避免 osgeo SWIG 对象在部分环境下失效"""

    def __init__(self, src_srs, dst_srs):
        self.src_srs = clone_srs_with_gis_order(src_srs)
        self.dst_srs = clone_srs_with_gis_order(dst_srs)
        self.ct = osr.CoordinateTransformation(self.src_srs, self.dst_srs)

    def transform_xy(self, x, y):
        x = float(x)
        y = float(y)
        first_error = None
        try:
            pt = self.ct.TransformPoint(x, y, 0.0)
            return float(pt[0]), float(pt[1])
        except (RuntimeError, TypeError, ValueError) as exc:
            first_error = exc
        try:
            pt_geom = ogr.Geometry(ogr.wkbPoint)
            pt_geom.AddPoint(x, y, 0.0)
            pt_geom.Transform(self.ct)
            return float(pt_geom.GetX()), float(pt_geom.GetY())
        except (RuntimeError, TypeError, ValueError) as exc:
            detail = f"; TransformPoint error: {first_error}" if first_error else ""
            raise RuntimeError(f"坐标转换失败: ({x}, {y}) -> {exc}{detail}") from exc


def build_transform(src_srs, dst_srs):
    if src_srs is None or dst_srs is None:
        return None
    src_srs = clone_srs_with_gis_order(src_srs)
    dst_srs = clone_srs_with_gis_order(dst_srs)
    try:
        same_crs = bool(src_srs.IsSame(dst_srs))
    except (AttributeError, TypeError, RuntimeError):
        same_crs = False
    if same_crs:
        return None
    return SafeCoordinateTransformer(src_srs, dst_srs)


def transform_xy(x, y, transform):
    x = float(x)
    y = float(y)
    if transform is None:
        return x, y
    if not hasattr(transform, "transform_xy"):
        raise TypeError(f"无效的坐标转换对象: {type(transform)}")
    return transform.transform_xy(x, y)


# =========================================================
# 通用工具
# =========================================================

def safe_remove_shp(shp_path):
    base, _ = os.path.splitext(shp_path)
    for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg", ".qix"]:
        p = base + ext
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError as exc:
                raise OSError(f"无法删除已有 Shapefile 组件: {p}: {exc}") from exc


# =========================================================
# SHP -> TXT
# =========================================================

def geometry_to_txt_records(geom, feature_id, coord_transform=None, precision=3):
    records = []
    geom_type = ogr.GT_Flatten(geom.GetGeometryType())

    def fmt_xy(x, y):
        x, y = transform_xy(x, y, coord_transform)
        return f"{x:.{precision}f}, {y:.{precision}f}"

    if geom_type == ogr.wkbPoint:
        x = float(geom.GetX())
        y = float(geom.GetY())
        block = [f"# feature_id={feature_id} geom_type=POINT"]
        block.append(fmt_xy(x, y))
        records.append("\n".join(block))

    elif geom_type == ogr.wkbLineString:
        block = [f"# feature_id={feature_id} geom_type=LINESTRING"]
        for i in range(geom.GetPointCount()):
            x, y, *_ = geom.GetPoint(i)
            block.append(fmt_xy(float(x), float(y)))
        records.append("\n".join(block))

    elif geom_type == ogr.wkbPolygon:
        ring_count = geom.GetGeometryCount()
        for i in range(ring_count):
            ring = geom.GetGeometryRef(i)
            part_name = "outer" if i == 0 else "inner"
            block = [f"# feature_id={feature_id} geom_type=POLYGON part={part_name}"]
            for j in range(ring.GetPointCount()):
                x, y, *_ = ring.GetPoint(j)
                block.append(fmt_xy(float(x), float(y)))
            records.append("\n".join(block))

    elif geom_type in (ogr.wkbMultiPoint, ogr.wkbMultiLineString, ogr.wkbMultiPolygon):
        sub_count = geom.GetGeometryCount()
        for i in range(sub_count):
            sub_geom = geom.GetGeometryRef(i)
            sub_records = geometry_to_txt_records(
                geom=sub_geom,
                feature_id=f"{feature_id}_{i + 1}",
                coord_transform=coord_transform,
                precision=precision
            )
            records.extend(sub_records)
    else:
        raise NotImplementedError(f"暂不支持几何类型: {ogr.GeometryTypeToName(geom_type)}")

    return records


def shp_to_txt(shp_path, txt_path, src_epsg=None, dst_epsg=None, precision=3,
               progress_callback=None):
    """
    SHP -> TXT 转换
    progress_callback(current, total) 可选进度回调
    """
    if not os.path.isfile(shp_path):
        raise FileNotFoundError(f"输入 SHP 不存在: {shp_path}")
    out_dir = os.path.dirname(os.path.abspath(txt_path))
    if out_dir and not os.path.isdir(out_dir):
        raise FileNotFoundError(f"输出目录不存在: {out_dir}")

    ds = ogr.Open(shp_path, 0)
    if ds is None:
        raise RuntimeError(f"无法打开 SHP: {shp_path}")

    layer = ds.GetLayer(0)
    if layer is None:
        raise RuntimeError("SHP 中未找到有效图层")
    layer_srs = clone_srs_with_gis_order(layer.GetSpatialRef())

    src_srs = get_srs_from_epsg(src_epsg) if src_epsg else layer_srs
    dst_srs = get_srs_from_epsg(dst_epsg) if dst_epsg else src_srs
    if dst_epsg and src_srs is None:
        raise ValueError("输入 SHP 未定义坐标系；如需坐标转换，请先指定输入 EPSG。")
    coord_transform = build_transform(src_srs, dst_srs)

    total = layer.GetFeatureCount()
    all_blocks = []

    for idx, feat in enumerate(layer, start=1):
        geom = feat.GetGeometryRef()
        if geom is None:
            continue
        geom = geom.Clone()
        blocks = geometry_to_txt_records(
            geom=geom,
            feature_id=idx,
            coord_transform=coord_transform,
            precision=precision
        )
        all_blocks.extend(blocks)

        if progress_callback:
            progress_callback(idx, total)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_blocks))

    ds = None
    return len(all_blocks)


# =========================================================
# TXT -> SHP
# =========================================================

HEADER_RE = re.compile(
    r"^\s*#\s*feature_id=(?P<fid>[^\s]+)\s+geom_type=(?P<gtype>[^\s]+)(?:\s+part=(?P<part>[^\s]+))?\s*$",
    re.IGNORECASE
)


def parse_txt_blocks(txt_path):
    blocks = []
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        m = HEADER_RE.match(line)
        if m:
            if current is not None:
                blocks.append(current)
            current = {
                "feature_id": m.group("fid"),
                "geom_type": m.group("gtype").upper(),
                "part": m.group("part").lower() if m.group("part") else None,
                "coords": []
            }
            continue

        if current is None:
            raise ValueError(f"坐标行出现在头信息之前: {line}")

        parts = re.split(r"[, \t]+", line)
        if len(parts) < 2:
            raise ValueError(f"无法解析坐标行: {line}")

        x = float(parts[0])
        y = float(parts[1])
        current["coords"].append((x, y))

    if current is not None:
        blocks.append(current)

    return blocks


def txt_blocks_to_feature_map(blocks, coord_transform=None):
    feature_map = {}
    for blk in blocks:
        fid = blk["feature_id"]
        if fid not in feature_map:
            feature_map[fid] = []
        coords_new = []
        for x, y in blk["coords"]:
            x, y = transform_xy(float(x), float(y), coord_transform)
            coords_new.append((float(x), float(y)))
        blk2 = dict(blk)
        blk2["coords"] = coords_new
        feature_map[fid].append(blk2)
    return feature_map


def create_geometry_from_blocks(block_group, geom_type_hint=None):
    if not block_group:
        return None

    gtype = (geom_type_hint or block_group[0]["geom_type"]).upper()

    if gtype == "POINT":
        blk = block_group[0]
        if not blk["coords"]:
            return None
        x, y = blk["coords"][0]
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint(float(x), float(y))
        return geom

    elif gtype == "LINESTRING":
        geom = ogr.Geometry(ogr.wkbLineString)
        for blk in block_group:
            for x, y in blk["coords"]:
                geom.AddPoint(float(x), float(y))
        return geom

    elif gtype == "POLYGON":
        poly = ogr.Geometry(ogr.wkbPolygon)
        outers = [b for b in block_group if (b.get("part") or "").lower() == "outer"]
        inners = [b for b in block_group if (b.get("part") or "").lower() == "inner"]
        if not outers:
            outers = [block_group[0]]
            inners = block_group[1:]

        for blk in outers + inners:
            ring = ogr.Geometry(ogr.wkbLinearRing)
            for x, y in blk["coords"]:
                ring.AddPoint(float(x), float(y))
            if blk["coords"]:
                x0, y0 = blk["coords"][0]
                xN, yN = blk["coords"][-1]
                if abs(float(x0) - float(xN)) > 1e-8 or abs(float(y0) - float(yN)) > 1e-8:
                    ring.AddPoint(float(x0), float(y0))
            poly.AddGeometry(ring)
        return poly

    else:
        raise NotImplementedError(f"暂不支持几何类型: {gtype}")


def txt_to_shp(txt_path, shp_path, shp_geom_type="AUTO", src_epsg=None, dst_epsg=None,
               progress_callback=None):
    """
    TXT -> SHP 转换
    progress_callback(current, total) 可选进度回调
    """
    if not os.path.isfile(txt_path):
        raise FileNotFoundError(f"输入 TXT 不存在: {txt_path}")
    out_dir = os.path.dirname(os.path.abspath(shp_path))
    if out_dir and not os.path.isdir(out_dir):
        raise FileNotFoundError(f"输出目录不存在: {out_dir}")

    blocks = parse_txt_blocks(txt_path)
    if not blocks:
        raise RuntimeError("TXT 中没有有效坐标数据")

    src_srs = get_srs_from_epsg(src_epsg)

    if dst_epsg is None or str(dst_epsg).strip() == "":
        dst_srs = clone_srs_with_gis_order(src_srs)
    else:
        dst_srs = get_srs_from_epsg(dst_epsg)
    if dst_epsg and src_srs is None:
        raise ValueError("TXT 本身不包含坐标系信息；如需转换到其他坐标系，请指定输入 EPSG。")

    coord_transform = build_transform(src_srs, dst_srs)
    feature_map = txt_blocks_to_feature_map(blocks=blocks, coord_transform=coord_transform)

    if shp_geom_type is None or str(shp_geom_type).strip().upper() == "AUTO":
        shp_geom_type = blocks[0]["geom_type"].upper()
    else:
        shp_geom_type = shp_geom_type.upper()

    geom_type_map = {
        "POINT": ogr.wkbPoint,
        "LINESTRING": ogr.wkbLineString,
        "POLYGON": ogr.wkbPolygon,
    }

    ogr_geom_type = geom_type_map.get(shp_geom_type)
    if ogr_geom_type is None:
        raise ValueError("输出几何类型仅支持 AUTO / POINT / LINESTRING / POLYGON")

    drv = ogr.GetDriverByName("ESRI Shapefile")
    if drv is None:
        raise RuntimeError("未找到 ESRI Shapefile 驱动")

    safe_remove_shp(shp_path)
    ds = drv.CreateDataSource(shp_path)
    if ds is None:
        raise RuntimeError(f"无法创建 SHP: {shp_path}")

    layer_name = os.path.splitext(os.path.basename(shp_path))[0]
    layer = ds.CreateLayer(
        layer_name,
        srs=clone_srs_with_gis_order(dst_srs),
        geom_type=ogr_geom_type
    )
    if layer is None:
        ds = None
        raise RuntimeError(f"无法创建 SHP 图层: {shp_path}")

    field_id = ogr.FieldDefn("fid_txt", ogr.OFTString)
    field_id.SetWidth(64)
    layer.CreateField(field_id)

    field_gtype = ogr.FieldDefn("gtype", ogr.OFTString)
    field_gtype.SetWidth(20)
    layer.CreateField(field_gtype)

    defn = layer.GetLayerDefn()
    total = len(feature_map)

    written = 0
    for i, (fid_txt, group) in enumerate(feature_map.items(), start=1):
        geom_hint = None if shp_geom_type == "AUTO" else shp_geom_type
        geom = create_geometry_from_blocks(group, geom_type_hint=geom_hint)
        if geom is None:
            continue
        feat = ogr.Feature(defn)
        feat.SetField("fid_txt", str(fid_txt))
        feat.SetField("gtype", group[0]["geom_type"].upper())
        feat.SetGeometry(geom)
        if layer.CreateFeature(feat) != 0:
            raise RuntimeError(f"写入要素失败: feature_id={fid_txt}")
        written += 1
        feat = None

        if progress_callback:
            progress_callback(i, total)

    ds = None
    return written
