# -*- coding: utf-8 -*-
"""Native-style QGIS dialog for SHP TXT Coordinate Converter."""

import os
import traceback

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QRadioButton, QTextEdit, QFileDialog,
    QProgressBar, QSpinBox, QMessageBox, QButtonGroup, QWidget,
    QTabWidget, QGroupBox, QSizePolicy
)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtGui import QFont, QIcon

from .crs_options import CRS_OPTIONS
from .converter import shp_to_txt, txt_to_shp

PLUGIN_VERSION = "1.0.0"


class ConvertWorker(QThread):
    progress = pyqtSignal(int, int)
    log_msg = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, mode, in_path, out_path, src_epsg, dst_epsg,
                 precision, geom_type, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.in_path = in_path
        self.out_path = out_path
        self.src_epsg = src_epsg
        self.dst_epsg = dst_epsg
        self.precision = precision
        self.geom_type = geom_type

    def run(self):
        try:
            def prog(cur, tot):
                self.progress.emit(cur, tot)

            if self.mode == "shp2txt":
                count = shp_to_txt(
                    shp_path=self.in_path,
                    txt_path=self.out_path,
                    src_epsg=self.src_epsg,
                    dst_epsg=self.dst_epsg,
                    precision=self.precision,
                    progress_callback=prog,
                )
                self.finished.emit(True, f"Completed. Exported {count} coordinate block(s).")
            else:
                count = txt_to_shp(
                    txt_path=self.in_path,
                    shp_path=self.out_path,
                    shp_geom_type=self.geom_type,
                    src_epsg=self.src_epsg,
                    dst_epsg=self.dst_epsg,
                    progress_callback=prog,
                )
                self.finished.emit(True, f"Completed. Wrote {count} feature(s).")
        except Exception as exc:
            self.finished.emit(False, f"{exc}\n{traceback.format_exc()}")


class ShpTxtConverterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ShpTxtConverterDialog")
        self.setWindowTitle("SHP TXT Coordinate Converter")
        self.setMinimumSize(760, 520)
        self.resize(820, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.plugin_dir = os.path.dirname(__file__)
        self.icon_path = os.path.join(self.plugin_dir, "icons", "icon_v103.png")
        if not os.path.exists(self.icon_path):
            self.icon_path = os.path.join(self.plugin_dir, "icons", "icon.png")
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))

        self.crs_name_to_epsg = {name: epsg for name, epsg in CRS_OPTIONS}
        self.worker = None

        self._build_ui()
        self._on_src_crs_changed(self.src_crs_combo.currentText())
        self._on_dst_crs_changed(self.dst_crs_combo.currentText())
        self._on_mode_changed(initial=True)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        root.addWidget(self.tabs, 1)

        self.params_tab = QWidget()
        self.log_tab = QWidget()
        self.tabs.addTab(self.params_tab, "Parameters")
        self.tabs.addTab(self.log_tab, "Log")

        self._build_params_tab()
        self._build_log_tab()
        self._build_footer(root)

    def _build_params_tab(self):
        layout = QVBoxLayout(self.params_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        desc = QLabel(
            "Convert coordinates between Shapefile and TXT with geometry restoration and optional CRS transformation."
        )
        desc.setWordWrap(True)
        desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(desc)

        mode_group = QGroupBox("Conversion")
        mode_layout = QHBoxLayout(mode_group)
        self.rb_shp2txt = QRadioButton("SHP → TXT")
        self.rb_txt2shp = QRadioButton("TXT → SHP")
        self.rb_shp2txt.setChecked(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.rb_shp2txt, 0)
        self.mode_group.addButton(self.rb_txt2shp, 1)
        self.rb_shp2txt.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.rb_shp2txt)
        mode_layout.addWidget(self.rb_txt2shp)
        mode_layout.addStretch(1)
        layout.addWidget(mode_group)

        file_group = QGroupBox("Input and output")
        file_grid = QGridLayout(file_group)
        file_grid.setColumnStretch(1, 1)
        file_grid.addWidget(QLabel("Input file"), 0, 0)
        self.input_edit = QLineEdit()
        file_grid.addWidget(self.input_edit, 0, 1)
        self.btn_input = QPushButton("Browse…")
        self.btn_input.clicked.connect(self._browse_input)
        file_grid.addWidget(self.btn_input, 0, 2)

        file_grid.addWidget(QLabel("Output file"), 1, 0)
        self.output_edit = QLineEdit()
        file_grid.addWidget(self.output_edit, 1, 1)
        self.btn_output = QPushButton("Browse…")
        self.btn_output.clicked.connect(self._browse_output)
        file_grid.addWidget(self.btn_output, 1, 2)
        layout.addWidget(file_group)

        crs_group = QGroupBox("Coordinate reference systems")
        crs_grid = QGridLayout(crs_group)
        crs_grid.setColumnStretch(1, 1)
        crs_grid.setColumnStretch(4, 1)

        crs_grid.addWidget(QLabel("Source CRS"), 0, 0)
        self.src_crs_combo = QComboBox()
        self.src_crs_combo.addItems([name for name, _ in CRS_OPTIONS])
        self.src_crs_combo.currentTextChanged.connect(self._on_src_crs_changed)
        crs_grid.addWidget(self.src_crs_combo, 0, 1, 1, 3)
        crs_grid.addWidget(QLabel("EPSG"), 0, 4)
        self.src_epsg_edit = QLineEdit()
        self.src_epsg_edit.setPlaceholderText("e.g. 4326")
        self.src_epsg_edit.setMaximumWidth(140)
        crs_grid.addWidget(self.src_epsg_edit, 0, 5)

        crs_grid.addWidget(QLabel("Target CRS"), 1, 0)
        self.dst_crs_combo = QComboBox()
        self.dst_crs_combo.addItems([name for name, _ in CRS_OPTIONS])
        self.dst_crs_combo.currentTextChanged.connect(self._on_dst_crs_changed)
        crs_grid.addWidget(self.dst_crs_combo, 1, 1, 1, 3)
        crs_grid.addWidget(QLabel("EPSG"), 1, 4)
        self.dst_epsg_edit = QLineEdit()
        self.dst_epsg_edit.setPlaceholderText("e.g. 4490")
        self.dst_epsg_edit.setMaximumWidth(140)
        crs_grid.addWidget(self.dst_epsg_edit, 1, 5)

        note = QLabel(
            "Tip: use 'Auto detect / leave blank' to read the CRS from a Shapefile. "
            "Set a target CRS only when reprojection is needed."
        )
        note.setWordWrap(True)
        crs_grid.addWidget(note, 2, 0, 1, 6)
        layout.addWidget(crs_group)

        opt_group = QGroupBox("Options")
        opt_grid = QGridLayout(opt_group)
        opt_grid.addWidget(QLabel("TXT decimals"), 0, 0)
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(0, 15)
        self.precision_spin.setValue(3)
        opt_grid.addWidget(self.precision_spin, 0, 1)

        opt_grid.addWidget(QLabel("TXT → SHP geometry"), 0, 2)
        self.geom_combo = QComboBox()
        self.geom_combo.addItems(["AUTO", "POINT", "LINESTRING", "POLYGON"])
        opt_grid.addWidget(self.geom_combo, 0, 3)
        opt_grid.setColumnStretch(4, 1)
        layout.addWidget(opt_group)

        layout.addStretch(1)

    def _build_log_tab(self):
        layout = QVBoxLayout(self.log_tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_edit, 1)

        log_actions = QHBoxLayout()
        log_actions.addStretch(1)
        self.btn_clear = QPushButton("Clear log")
        self.btn_clear.clicked.connect(self._clear_log)
        log_actions.addWidget(self.btn_clear)
        layout.addLayout(log_actions)

    def _build_footer(self, root_layout):
        footer = QVBoxLayout()
        footer.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        footer.addWidget(self.progress_bar)

        actions = QHBoxLayout()
        self.btn_help = QPushButton("Help")
        self.btn_help.clicked.connect(self._show_help)
        actions.addWidget(self.btn_help)

        actions.addStretch(1)

        self.btn_run = QPushButton("Convert")
        self.btn_run.setDefault(True)
        self.btn_run.clicked.connect(self._run_convert)
        actions.addWidget(self.btn_run)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        actions.addWidget(self.btn_close)

        footer.addLayout(actions)
        root_layout.addLayout(footer)

    def _on_mode_changed(self, checked=None, initial=False):
        is_s2t = self.rb_shp2txt.isChecked()
        self.precision_spin.setEnabled(is_s2t)
        self.geom_combo.setEnabled(not is_s2t)
        if is_s2t:
            self.input_edit.setPlaceholderText("Choose a Shapefile (.shp)")
            self.output_edit.setPlaceholderText("Output TXT file")
        else:
            self.input_edit.setPlaceholderText("Choose a TXT coordinate file (.txt)")
            self.output_edit.setPlaceholderText("Output Shapefile (.shp)")
        if not initial:
            self.input_edit.clear()
            self.output_edit.clear()
            self._log(f"Mode: {'SHP → TXT' if is_s2t else 'TXT → SHP'}")

    def _on_src_crs_changed(self, name):
        epsg = self.crs_name_to_epsg.get(name, "")
        if epsg == "__custom__":
            self.src_epsg_edit.setReadOnly(False)
            self.src_epsg_edit.clear()
            self.src_epsg_edit.setFocus()
        else:
            self.src_epsg_edit.setText(epsg)
            self.src_epsg_edit.setReadOnly(bool(epsg))

    def _on_dst_crs_changed(self, name):
        epsg = self.crs_name_to_epsg.get(name, "")
        if epsg == "__custom__":
            self.dst_epsg_edit.setReadOnly(False)
            self.dst_epsg_edit.clear()
            self.dst_epsg_edit.setFocus()
        else:
            self.dst_epsg_edit.setText(epsg)
            self.dst_epsg_edit.setReadOnly(bool(epsg))

    def _get_epsg(self, combo, edit):
        epsg = self.crs_name_to_epsg.get(combo.currentText(), "")
        return edit.text().strip() if epsg == "__custom__" else epsg

    def _browse_input(self):
        is_s2t = self.rb_shp2txt.isChecked()
        caption = "Select input Shapefile" if is_s2t else "Select input TXT file"
        file_filter = "Shapefile (*.shp);;All files (*)" if is_s2t else "Text file (*.txt);;All files (*)"
        path, _ = QFileDialog.getOpenFileName(self, caption, "", file_filter)
        if path:
            self.input_edit.setText(path)
            self._auto_fill_output(path)

    def _browse_output(self):
        is_s2t = self.rb_shp2txt.isChecked()
        caption = "Save TXT file" if is_s2t else "Save Shapefile"
        file_filter = "Text file (*.txt);;All files (*)" if is_s2t else "Shapefile (*.shp);;All files (*)"
        path, _ = QFileDialog.getSaveFileName(self, caption, "", file_filter)
        if path:
            self.output_edit.setText(path)

    def _auto_fill_output(self, in_path):
        base, _ = os.path.splitext(in_path)
        self.output_edit.setText(base + (".txt" if self.rb_shp2txt.isChecked() else "_out.shp"))

    def _validate(self):
        in_path = self.input_edit.text().strip()
        out_path = self.output_edit.text().strip()
        if not in_path:
            raise ValueError("Select an input file.")
        if not os.path.exists(in_path):
            raise ValueError(f"Input file does not exist:\n{in_path}")
        if not out_path:
            raise ValueError("Select an output file.")
        src_epsg = self._get_epsg(self.src_crs_combo, self.src_epsg_edit)
        dst_epsg = self._get_epsg(self.dst_crs_combo, self.dst_epsg_edit)
        if src_epsg and not src_epsg.isdigit():
            raise ValueError(f"Source EPSG must be an integer: {src_epsg}")
        if dst_epsg and not dst_epsg.isdigit():
            raise ValueError(f"Target EPSG must be an integer: {dst_epsg}")

    def _run_convert(self):
        try:
            self._validate()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid parameters", str(exc))
            return

        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Working", "A conversion is already running.")
            return

        mode = "shp2txt" if self.rb_shp2txt.isChecked() else "txt2shp"
        in_path = self.input_edit.text().strip()
        out_path = self.output_edit.text().strip()
        src_epsg = self._get_epsg(self.src_crs_combo, self.src_epsg_edit) or None
        dst_epsg = self._get_epsg(self.dst_crs_combo, self.dst_epsg_edit) or None
        precision = self.precision_spin.value()
        geom_type = self.geom_combo.currentText().upper()

        self._log("-" * 60)
        self._log(f"Mode: {'SHP → TXT' if mode == 'shp2txt' else 'TXT → SHP'}")
        self._log(f"Input: {in_path}")
        self._log(f"Output: {out_path}")
        self._log(f"Source CRS: EPSG:{src_epsg}" if src_epsg else "Source CRS: from input / undefined")
        self._log(f"Target CRS: EPSG:{dst_epsg}" if dst_epsg else "Target CRS: same as source")
        self._log(f"Precision: {precision}" if mode == "shp2txt" else f"Geometry: {geom_type}")
        self.tabs.setCurrentWidget(self.log_tab)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Converting...")

        self.worker = ConvertWorker(
            mode, in_path, out_path, src_epsg, dst_epsg, precision, geom_type
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.log_msg.connect(self._log)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, cur, tot):
        if tot > 0:
            self.progress_bar.setMaximum(tot)
            self.progress_bar.setValue(cur)

    def _on_finished(self, success, msg):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("Convert")
        self.tabs.setCurrentWidget(self.log_tab)
        if success:
            self._log(msg)
            self.progress_bar.setValue(self.progress_bar.maximum())
            QMessageBox.information(self, "Conversion complete", msg)
        else:
            self._log("ERROR")
            self._log(msg)
            QMessageBox.critical(self, "Conversion failed", msg.split("\n")[0])

    def _log(self, msg):
        if not hasattr(self, "log_edit"):
            return
        self.log_edit.append(str(msg))
        sb = self.log_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear_log(self):
        self.log_edit.clear()

    def _show_help(self):
        text = (
            "SHP TXT Coordinate Converter\n\n"
            "SHP → TXT\nExports feature coordinates to structured TXT blocks.\n\n"
            "TXT → SHP\nRestores Point, LineString or Polygon geometry from TXT.\n\n"
            "CRS\nUse Auto detect to read a Shapefile CRS. Select a target CRS only when reprojection is needed. "
            "Custom EPSG codes are supported.\n\n"
            "Polygon rings and multipart geometries are supported. Conversion runs in a background thread.\n\n"
            "Author: Zhang Y.H.\n"
            "GitHub: github.com/zhangyhrs/SHP-TXT-Converter-QGIS"
        )
        QMessageBox.information(self, "Help", text)
