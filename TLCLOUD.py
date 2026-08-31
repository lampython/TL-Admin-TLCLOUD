# -*- coding: utf-8 -*-
import os
import sys
import sqlite3
import shutil
import subprocess
import json
import ctypes
import string
import webbrowser
import requests
from playwright.sync_api import sync_playwright
from typing import List
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor, QIcon, QAction, QShortcut, QKeySequence, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QMessageBox, QProgressBar, QFileDialog, QFrame,
    QDialog, QFormLayout, QDialogButtonBox, QTabWidget, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QComboBox, QCheckBox,
    QCompleter
)
import pandas as pd
import qrcode

# --- HÀM XÁC ĐỊNH THƯ MỤC GỐC (PORTABLE) ---
def get_app_root():
    if getattr(sys, "frozen", False):
        # Đường dẫn thư mục chứa file .exe
        return os.path.dirname(sys.executable)
    # Đường dẫn thư mục chứa file .py
    return os.path.dirname(os.path.abspath(__file__))

APP_ROOT = get_app_root()
CURRENT_VERSION = "1.3"

# Style giao diện (Khai báo sớm để các Dialog sử dụng được)
STYLESHEET = """
    QMainWindow { background-color: #f0f2f5; }
    QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #1c1e21; }
    
    QFrame#Card { background-color: #ffffff; border-radius: 10px; border: 1px solid #ddd; }
    
    QLineEdit { border: 1px solid #ccc; border-radius: 6px; padding: 8px; background: #fff; }
    QLineEdit:focus { border: 2px solid #005a9e; }
    
    QListWidget { border: none; background: transparent; }
    QListWidget::item { padding: 8px; border-bottom: 1px solid #eee; }
    QListWidget::item:selected { background-color: #e5f1fb; color: #005a9e; font-weight: bold; border-radius: 6px; }

    QPushButton { padding: 10px 20px; border-radius: 6px; font-weight: bold; border: none; }
    
    /* Nút chính nổi bật */
    QPushButton#CleanBtn { background-color: #d83b01; color: white; font-size: 15px; }
    QPushButton#CleanBtn#CleanBtn:hover { background-color: #ea4a1f; }
    QPushButton#CleanBtn:disabled { background-color: #f1704e; color: #ffffff; }

    QPushButton#SyncBtn { background-color: #1890ff; color: white; font-size: 15px; }
    QPushButton#SyncBtn:hover { background-color: #40a9ff; }
    QPushButton#SyncBtn:disabled { background-color: #bae7ff; color: #ffffff; }

    QPushButton#SyncAllBtn { background-color: #096dd9; color: white; font-size: 15px; }
    QPushButton#SyncAllBtn:hover { background-color: #1890ff; }
    QPushButton#SyncAllBtn:disabled { background-color: #bae7ff; color: #ffffff; }

    QPushButton#USBBtn { background-color: #52c41a; color: white; font-size: 15px; }
    QPushButton#USBBtn:hover { background-color: #73d13d; }
    QPushButton#USBBtn:disabled { background-color: #b7eb8f; color: #ffffff; }

    QPushButton#BrowseBtn { background-color: #e1dfdd; color: #333; }
    QPushButton#BrowseBtn:hover { background-color: #d2d0ce; }
    
    QProgressBar { border: none; background-color: #e0e0e0; border-radius: 4px; height: 10px; text-align: center; }
    QProgressBar::chunk { background-color: #107c10; border-radius: 4px; }
    
    /* LOG NHẬT KÝ: NỀN TRẮNG - CHỮ ĐEN */
    QTextEdit { 
        background-color: #ffffff; 
        color: #333333; 
        font-family: 'Consolas', monospace; 
        font-size: 13px; 
        border: 1px solid #ccc;
        border-radius: 6px; 
    }

    QPushButton#SideBtn { 
        background-color: transparent; 
        color: #595959; 
        border-radius: 0px; 
        font-size: 13px; 
        border-bottom: 1px solid #f0f0f0;
    }
    QPushButton#SideBtn:hover { background-color: #f5f5f5; }
    QPushButton#SideBtn[active="true"] { 
        background-color: #e6f7ff; 
        color: #1890ff; 
        font-weight: bold;
        border-right: 3px solid #1890ff;
    }
    
    QTableWidget { border: 1px solid #ccc; border-radius: 6px; background-color: white; gridline-color: #f0f0f0; selection-background-color: #e6f7ff; selection-color: #1890ff; }
    QHeaderView::section { background-color: #fafafa; font-weight: bold; padding: 8px; border: 1px solid #f0f0f0; color: #333; }
    
    QComboBox { 
        border: 1px solid #ccc; 
        border-radius: 6px; 
        padding: 4px 8px; 
        background-color: #ffffff; 
    }
    QComboBox:focus {
        border: 2px solid #005a9e;
    }
    QComboBox QAbstractItemView {
        border: 1px solid #ccc;
        border-radius: 6px;
        background-color: #ffffff;
        selection-background-color: #e6f7ff;
        selection-color: #1890ff;
        outline: none;
        padding: 4px 0px;
    }
"""
CONFIG_FILE = os.path.join(APP_ROOT, "config.json")

DEFAULT_CONFIG = {
    "YEAR_CONFIGS": {
        "2024": {
            "SRC_ROOT": r"\\nastl\TL",
            "DEST_ROOT": r"\\nastl\DULIEUCONGTY\TLCloud_2024",
            "DATABASE_PATH": "database"
        },
        "2025": {
            "SRC_ROOT": r"\\nastl\TL",
            "DEST_ROOT": r"\\nastl\DULIEUCONGTY\TLCloud_2025",
            "DATABASE_PATH": "database"
        }
    },
    "ACTIVE_YEAR": "2025",
    "SUBFOLDERS": ["1. CHUNG TU", "2. SO SACH"],
    "APP_NAME": "Tool TL - CLOUD",
    # Các key đệm cho tương thích ngược và truy cập nhanh
    "YEAR": "2024",
    "SRC_ROOT": r"\\nastl\TL",
    "DEST_ROOT": r"\\nastl\DULIEUCONGTY\TLCloud_2024"
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                conf = json.load(f)
                
                # Di chuyển cấu hình cũ sang định dạng multi-year nếu chưa có
                if "YEAR_CONFIGS" not in conf:
                    old_year = conf.get("YEAR", "2024")
                    conf["YEAR_CONFIGS"] = {
                        old_year: {
                            "SRC_ROOT": conf.get("SRC_ROOT", r"\\nastl\TL"),
                            "DEST_ROOT": conf.get("DEST_ROOT", f"\\\\nastl\\DULIEUCONGTY\\TLCloud_{old_year}"),
                            "DATABASE_PATH": os.path.join(APP_ROOT, "database")
                        }
                    }
                    conf["ACTIVE_YEAR"] = old_year
                
                # Đảm bảo các key mặc định khác tồn tại
                for k in DEFAULT_CONFIG:
                    if k not in conf:
                        conf[k] = DEFAULT_CONFIG[k]
                
                # Đồng bộ key top-level với năm active
                active_year = conf.get("ACTIVE_YEAR", "2024")
                if active_year in conf["YEAR_CONFIGS"]:
                    y_cfg = conf["YEAR_CONFIGS"][active_year]
                    conf["YEAR"] = active_year
                    conf["SRC_ROOT"] = y_cfg.get("SRC_ROOT", "")
                    conf["DEST_ROOT"] = y_cfg.get("DEST_ROOT", "")
                    
                # Tự động sửa đường dẫn DATABASE_PATH & UPDATE_PATH (Portability)
                # 1. Xử lý DATABASE_PATH trong từng năm
                for yr, y_cfg in conf.get("YEAR_CONFIGS", {}).items():
                    db_p = y_cfg.get("DATABASE_PATH", "")
                    
                    # Nếu đường dẫn tuyệt đối nhưng không tồn tại, hoặc không có đường dẫn, đưa về mặc định "database"
                    if db_p and os.path.isabs(db_p):
                        if not os.path.exists(db_p):
                            y_cfg["DATABASE_PATH"] = "database"
                    elif not db_p:
                        y_cfg["DATABASE_PATH"] = "database"
                    # Lưu ý: Không convert sang absolute tại đây để khi lưu file config vẫn giữ được tính portable
                
                return conf
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(conf):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(conf, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu cấu hình: {e}")

CONFIG = load_config()

def get_valid_usb_drives():
    drives = []
    for letter in string.ascii_uppercase[3:]:
        drive = f"{letter}:\\"
        try:
            if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2:
                usage = shutil.disk_usage(drive)
                if usage.total > 0 and usage.total <= 34359738368:
                    drives.append((drive, usage.total))
        except Exception:
            pass
    return drives

# Cấu hình file rác
IGNORE_NAMES = {"Thumbs.db", "desktop.ini", ".DS_Store"}
JUNK_EXTS = {".db", ".tmp", ".log", ".bak", ".old", ".lnk", ".part", ".crdownload", ".ini"}
TEMP_PREFIXES = ("~$",)

def version_tuple(v):
    return tuple(map(int, (v.split("."))))

# =================================================================================
# 📥 HỘP THOẠI CẬP NHẬT (UPDATE DIALOG)
# =================================================================================

# =================================================================================
# ⚙️ HỘP THOẠI CẤU HÌNH CHECK
# =================================================================================
class CheckConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 Cấu hình Double Check")
        self.resize(350, 200)
        self.setStyleSheet(STYLESHEET)
        
        layout = QVBoxLayout(self)
        
        icon_lbl = QLabel("🌐")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 30px;")
        layout.addWidget(icon_lbl)

        msg = QLabel("<b>Bạn muốn thực hiện double check link Onedriver không?</b>")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        
        # Nút gạt Headless (Mặc định được tích chọn - chạy ẩn)
        self.chk_headless = QCheckBox(" Chế độ chạy ẩn (Headless)")
        self.chk_headless.setChecked(True)
        self.chk_headless.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_headless.setStyleSheet("margin: 15px; font-weight: bold; color: #1890ff; font-size: 15px;")
        layout.addWidget(self.chk_headless, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("🚀 Bắt đầu")
        self.btn_start.setObjectName("SyncBtn")
        self.btn_start.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setObjectName("BrowseBtn")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def is_headless(self):
        return self.chk_headless.isChecked()


# =================================================================================
# 📊 VIEW CƠ SỞ DỮ LIỆU
# =================================================================================
class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except (ValueError, TypeError):
            return super().__lt__(other)

class DatabaseView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("📊 QUẢN LÝ CƠ SỞ DỮ LIỆU (EXCEL)")
        header.setStyleSheet("font-weight: bold; font-size: 20px; color: #0078d4;")
        
        # Dropdown chọn năm
        self.cbo_year = QComboBox()
        self.cbo_year.setFixedWidth(100)
        self.cbo_year.setStyleSheet("padding: 5px; font-weight: bold; color: #0078d4;")
        self.cbo_year.currentTextChanged.connect(self.on_year_dropdown_changed)

        self.btn_import_excel = QPushButton("📥 Nhập từ Excel")
        self.btn_import_excel.setFixedWidth(150)
        self.btn_import_excel.setStyleSheet("background-color: #fa8c16; color: white; padding: 8px;")
        self.btn_import_excel.clicked.connect(self.import_excel_to_db)
        
        self.btn_delete_rows = QPushButton("🗑️ Xóa dòng")
        self.btn_delete_rows.setFixedWidth(120)
        self.btn_delete_rows.setStyleSheet("background-color: #ff4d4f; color: white; padding: 8px;")
        self.btn_delete_rows.clicked.connect(self.delete_selected_rows)

        self.btn_add_row = QPushButton("➕ Thêm dòng")
        self.btn_add_row.setFixedWidth(120)
        self.btn_add_row.setStyleSheet("background-color: #1890ff; color: white; padding: 8px;")
        self.btn_add_row.clicked.connect(self.add_new_row)

        self.btn_export_excel = QPushButton("🚀 Xuất Excel")
        self.btn_export_excel.setFixedWidth(120)
        self.btn_export_excel.setStyleSheet("background-color: #52c41a; color: white; padding: 8px;")
        self.btn_export_excel.clicked.connect(self.export_to_excel)

        self.btn_double_check_all = QPushButton("🌐 Double Check All")
        self.btn_double_check_all.setFixedWidth(160)
        self.btn_double_check_all.setStyleSheet("background-color: #722ed1; color: white; padding: 8px;")
        self.btn_double_check_all.clicked.connect(self.start_onedrive_check)

        header_layout.addWidget(header)
        header_layout.addWidget(QLabel("Năm:"))
        header_layout.addWidget(self.cbo_year)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add_row)
        header_layout.addWidget(self.btn_delete_rows)
        header_layout.addWidget(self.btn_import_excel)
        header_layout.addWidget(self.btn_export_excel)
        header_layout.addWidget(self.btn_double_check_all)
        
        # Thêm Tìm kiếm
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("🔍 Lọc dữ liệu trong bảng...")
        self.txt_filter.setFixedWidth(250)
        self.txt_filter.textChanged.connect(self.filter_table)
        header_layout.addWidget(self.txt_filter)
        layout.addLayout(header_layout)
        
        # Thêm ghi chú path
        self.lbl_path = QLabel("Đường dẫn: ...")
        self.lbl_path.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(self.lbl_path)
        
        # Table
        self.table = QTableWidget()
        # Cho phép chỉnh sửa (Double click hoặc nhấn phím)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.EditKeyPressed)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Tự động lưu khi sửa đổi
        self.table.itemChanged.connect(self.on_item_changed)
        
        # Mở link Web khi nhấp đúp
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        # Sắp xếp
        self.table.setSortingEnabled(True)
        
        # Tăng chiều cao hàng để "dễ thở" hơn
        self.table.verticalHeader().setDefaultSectionSize(38)
        
        layout.addWidget(self.table)
        
        # Shortcut Ctrl+C
        self.copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        self.copy_shortcut.activated.connect(self.copy_selection)
        
        # Shortcut Ctrl+F
        self.find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.find_shortcut.activated.connect(self.txt_filter.setFocus)
        
        self.load_data()

    def on_year_dropdown_changed(self, selected_year):
        if not selected_year:
            return
        # Delay update to next event loop iteration to avoid QComboBox popup C++ crash
        QTimer.singleShot(0, lambda: self._process_year_change(selected_year))

    def _process_year_change(self, selected_year):
        p = self.parent()
        while p:
            if hasattr(p, 'inp_active_year') and hasattr(p, 'on_year_changed'):
                if isinstance(p.inp_active_year, QComboBox):
                    p.inp_active_year.blockSignals(True)
                    p.inp_active_year.setCurrentText(selected_year)
                    p.inp_active_year.blockSignals(False)
                    p.on_year_changed(selected_year)
                else:
                    p.inp_active_year.setText(selected_year)
                break
            p = p.parent()

    def start_onedrive_check(self):
        dlg = CheckConfigDialog(self)
        if dlg.exec():
            headless = dlg.is_headless()
            self.run_double_check_all(headless)

    def run_double_check_all(self, headless=True):
        self.btn_double_check_all.setEnabled(False)
        
        # Find indices of columns
        col_link = -1
        col_mst = -1
        col_bangiao = -1
        col_doublecheck = -1
        
        for j in range(self.table.columnCount()):
            hdr = self.table.horizontalHeaderItem(j).text().upper()
            if "LINK1" in hdr: col_link = j
            elif "MST" in hdr: col_mst = j
            elif "BÀN GIAO" in hdr and "NGÀY" not in hdr: col_bangiao = j
            elif "DOUBLE CHECK" in hdr: col_doublecheck = j
            
        if col_link == -1 or col_mst == -1 or col_doublecheck == -1:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy đủ các cột cần thiết (Link1, MST, Double Check).")
            self.btn_double_check_all.setEnabled(True)
            return

        tasks_priority = []
        tasks_normal = []
        
        for i in range(self.table.rowCount()):
            # Skip if already "OK" for batch check
            dc_item = self.table.item(i, col_doublecheck)
            if dc_item and dc_item.text().strip().upper() == "OK":
                continue
                
            url_item = self.table.item(i, col_link)
            mst_item = self.table.item(i, col_mst)
            
            url = url_item.text().strip() if url_item else ""
            mst = mst_item.text().strip() if mst_item else ""
            
            if not url.startswith("http"):
                continue
                
            bg_item = self.table.item(i, col_bangiao) if col_bangiao != -1 else None
            is_delivered = bg_item and bg_item.text().strip() in ["1", "1.0"]
            
            task = (i, url, mst)
            if is_delivered:
                tasks_priority.append(task)
            else:
                tasks_normal.append(task)
                
        all_tasks = tasks_priority + tasks_normal
        
        if not all_tasks:
            QMessageBox.information(self, "Thông báo", "Không có dòng nào cần kiểm tra (tất cả đã OK hoặc không có link hợp lệ).")
            self.btn_double_check_all.setEnabled(True)
            return

        # Start WebValidationWorker
        self.batch_worker = WebValidationWorker(all_tasks, headless=headless)
        self.batch_worker.progress_sig.connect(self.on_check_progress)
        self.batch_worker.done_sig.connect(self.on_batch_check_finished)
        self.batch_worker.done_sig.connect(self.save_to_sqlite)
        self.batch_worker.start()
        
    def on_batch_check_finished(self):
        self.btn_double_check_all.setEnabled(True)
        QMessageBox.information(self, "Hoàn tất", "Đã hoàn tất quá trình Double Check All và lưu dữ liệu!")

    def init_sqlite_db(self):
        """Khởi tạo cấu trúc bảng SQLite nếu chưa có"""
        try:
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()
            # Tạo bảng với các cột tương ứng headers (Sử dụng nháy kép cho tên bảng)
            cols_def = ", ".join([f'"{h}" TEXT' for h in self.headers])
            cursor.execute(f'CREATE TABLE IF NOT EXISTS "database" ({cols_def})')
            try:
                cursor.execute('ALTER TABLE "database" ADD COLUMN "Ngày Bàn Giao" TEXT')
            except Exception:
                pass
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Lỗi khởi tạo SQLite: {e}")

    def import_excel_to_db(self):
        """Chọn file Excel và nhập vào database"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel để nhập", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.perform_import(file_path)

    def perform_import(self, file_path, quiet=False):
        """Thực hiện nhập dữ liệu từ Excel vào SQLite"""
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Đồng bộ cột: Chỉ lấy các cột có trong headers chuẩn
            available_cols = [c for c in df.columns if c in self.headers]
            df_to_import = df[available_cols].copy()
            
            # Thêm các cột thiếu nếu cần
            for h in self.headers:
                if h not in df_to_import.columns:
                    df_to_import[h] = ""
            
            # Sắp xếp lại cột theo đúng thứ tự headers
            df_to_import = df_to_import[self.headers]

            conn = sqlite3.connect(self.current_db_path)
            # Xóa dữ liệu cũ và chép dữ liệu mới vào
            df_to_import.to_sql("database", conn, if_exists="replace", index=False)
            conn.close()
            
            if not quiet:
                QMessageBox.information(self, "Thành công", f"Đã nhập {len(df_to_import)} dòng từ Excel vào Database SQLite!")
            
            self.load_data()
        except Exception as e:
            if not quiet:
                QMessageBox.critical(self, "Lỗi", f"Không thể nhập file Excel:\n{e}")
            else:
                print(f"Lỗi tự động migrate: {e}")

    def load_data(self):
        # Lấy cấu hình năm hiện tại
        active_year = CONFIG.get("ACTIVE_YEAR", "2024")
        year_cfg = CONFIG.get("YEAR_CONFIGS", {}).get(active_year, {})
        
        # Ưu tiên lấy từ config, nếu không có thì mặc định tìm folder database tại root app
        db_p_raw = year_cfg.get("DATABASE_PATH", "database")
        if os.path.isabs(db_p_raw):
            db_path = db_p_raw
        else:
            db_path = os.path.normpath(os.path.join(APP_ROOT, db_p_raw))
        
        # Đảm bảo thư mục tồn tại
        if not os.path.exists(db_path):
            try:
                os.makedirs(db_path, exist_ok=True)
            except:
                pass

        # Xây dựng tên file SQLite theo năm
        target_db = f"DANH SACH THE {active_year}.db"
        self.current_db_path = os.path.join(db_path, target_db)

        # Cập nhật danh sách năm trong Combobox
        if hasattr(self, 'cbo_year'):
            self.cbo_year.blockSignals(True)
            self.cbo_year.clear()
            years = []
            if os.path.exists(db_path):
                for file in os.listdir(db_path):
                    if file.startswith("DANH SACH THE ") and file.endswith(".db"):
                        parts = file.replace("DANH SACH THE ", "").replace(".db", "").strip()
                        if parts.isdigit():
                            years.append(parts)
            config_years = list(CONFIG.get("YEAR_CONFIGS", {}).keys())
            all_years = sorted(list(set(years + config_years + [active_year])), reverse=True)
            self.cbo_year.addItems(all_years)
            self.cbo_year.setCurrentText(active_year)
            self.cbo_year.blockSignals(False)
        
        # Cập nhật hiển thị đường dẫn lên giao diện
        rel_display_path = os.path.join("database", target_db)
        self.lbl_path.setText(f"Đường dẫn (SQLite): {rel_display_path}")
        
        # Tiêu đề chuẩn cho Database (Không bao gồm cột nút bấm)
        self.headers = ["STT", "MTC", "Link1", "MST", "Tên Công Ty", "Phòng", "User", "Bàn Giao", "Ngày Bàn Giao", "Ghi chú", "link onedrive", "Double Check"]

        # Tự động khởi tạo DB nếu chưa có
        self.init_sqlite_db()

        try:
            conn = sqlite3.connect(self.current_db_path)
            # Kiểm tra xem có dữ liệu không, nếu không thử import từ file Excel cũ (Migration)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM "database"')
            count = cursor.fetchone()[0]
            conn.close()

            if count == 0:
                # Thử tìm file Excel cũ để tự động chuyển đổi
                old_excel = os.path.join(db_path, f"DANH SACH THE {active_year}.xlsx")
                if os.path.exists(old_excel):
                    print(f"DEBUG: Found old Excel {old_excel}, migrating to SQLite...")
                    self.perform_import(old_excel, quiet=True)

            # Đọc dữ liệu từ SQLite
            conn = sqlite3.connect(self.current_db_path)
            df = pd.read_sql_query('SELECT * FROM "database"', conn)
            conn.close()
            
            # --- LỌC CỘT DƯ THỪA (QUAN TRỌNG) ---
            # Chỉ giữ lại các cột nằm trong danh sách headers chuẩn
            valid_cols = [c for c in df.columns if c in self.headers and c != ""]
            df = df[valid_cols]

            # Đảm bảo có đầy đủ cột Double Check nếu file cũ chưa có
            if "Double Check" not in df.columns:
                df["Double Check"] = ""
            if "Ngày Bàn Giao" not in df.columns:
                df["Ngày Bàn Giao"] = ""
                
            # Giới hạn load 1000 dòng để tránh lag nếu file quá lớn
            display_df = df.head(1000)
            
            # Tạm tắt sắp xếp và tín hiệu khi load để tránh lỗi và tăng tốc
            self.table.blockSignals(True)
            self.table.setSortingEnabled(False)
            self.table.setRowCount(display_df.shape[0])
            self.table.setColumnCount(display_df.shape[1] + 1)
            # Headers hiển thị trên bảng: Tên cột từ DF + 1 ô trống cho nút Check
            headers_list = display_df.columns.astype(str).tolist() + [""]
            self.table.setHorizontalHeaderLabels(headers_list)
            
            # Tìm chỉ số cột quan trọng
            col_idx_stt = -1
            col_idx_bangiao = -1
            col_idx_ngaybangiao = -1
            col_idx_link1 = -1
            col_idx_mst = -1
            col_idx_doublecheck = -1
            col_idx_ghichu = -1

            for idx, h in enumerate(headers_list):
                h_upper = h.upper()
                if "STT" in h_upper: col_idx_stt = idx
                if "NGÀY BÀN GIAO" in h_upper: col_idx_ngaybangiao = idx
                elif "BÀN GIAO" in h_upper: col_idx_bangiao = idx
                if "LINK1" in h_upper: col_idx_link1 = idx
                if "MST" in h_upper: col_idx_mst = idx
                if "DOUBLE CHECK" in h_upper: col_idx_doublecheck = idx
                if "GHI CHÚ" in h_upper: col_idx_ghichu = idx

            for i in range(display_df.shape[0]):
                is_delivered = False
                if col_idx_bangiao != -1:
                    bg_val = display_df.iloc[i, col_idx_bangiao]
                    if str(bg_val) in ["1", "1.0", 1, 1.0]:
                        is_delivered = True

                for j in range(display_df.shape[1]):
                    val = display_df.iloc[i, j]
                    
                    # Định dạng số (1.0 -> 1)
                    if pd.notnull(val):
                        if isinstance(val, (float, int)):
                            if float(val).is_integer():
                                text = str(int(val))
                            else:
                                text = str(val)
                        else:
                            text = str(val)
                    else:
                        text = ""

                    # Sử dụng NumericItem cho cột số để sắp xếp chuẩn
                    if j == col_idx_stt or j == col_idx_bangiao:
                        item = NumericTableWidgetItem(text)
                    else:
                        item = QTableWidgetItem(text)

                    # Kiểm tra ghi chú "KHÔNG LÀM THẺ"
                    is_no_card = False
                    if col_idx_ghichu != -1:
                        gc_val = str(display_df.iloc[i, col_idx_ghichu]).upper()
                        if "KHÔNG LÀM THẺ" in gc_val:
                            is_no_card = True

                    # Tô màu nếu đã bàn giao (Xanh) hoặc không làm thẻ (Đỏ)
                    if is_no_card:
                        item.setBackground(QColor("#fff1f0")) # Đỏ nhạt
                    elif is_delivered:
                        item.setBackground(QColor("#d4edda")) # Xanh lá nhạt

                    self.table.setItem(i, j, item)
                
                btn_check = QPushButton("🔍 Check")
                btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_check.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Ngăn nút chiếm focus gây nhảy bảng
                btn_check.setStyleSheet("""
                    QPushButton { background-color: #f0f0f0; border: 1px solid #ccc; font-size: 11px; padding: 2px; border-radius: 3px; }
                    QPushButton:hover { background-color: #e0e0e0; border-color: #999; }
                """)
                
                # Lấy link và mst để truyền vào lambda
                r_url = str(display_df.iloc[i, col_idx_link1]) if col_idx_link1 != -1 else ""
                r_mst = str(display_df.iloc[i, col_idx_mst]) if col_idx_mst != -1 else ""
                
                self.add_check_button_to_row(i, r_url, r_mst)
            
            # Căn chỉnh độ rộng tự động theo nội dung
            self.table.resizeColumnsToContents()
            
            # Thêm khoảng đệm (padding) để tránh bị mất chữ do margin/padding của widget
            for c in range(self.table.columnCount()):
                # Tăng thêm 25px so với kích thước tính toán được
                new_width = self.table.columnWidth(c) + 25
                # Giới hạn độ rộng tối đa cho cột link để không quá choán chỗ (ví dụ 400px)
                header_text = self.table.horizontalHeaderItem(c).text().lower()
                if "link" in header_text:
                    new_width = min(new_width, 400)
                self.table.setColumnWidth(c, new_width)

            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.table.setSortingEnabled(True)
            self.table.blockSignals(False)
            
            # Lưu lại index các cột cho việc check tự động
            self.col_indices = {
                "mst": col_idx_mst,
                "link1": col_idx_link1,
                "doublecheck": col_idx_doublecheck
            }
            
            # Reset lọc
            self.txt_filter.clear()
            
            # Cập nhật completer ở MainApp
            p = self.parent()
            while p:
                if hasattr(p, 'update_mtc_completer'):
                    p.update_mtc_completer()
                if hasattr(p, 'update_dept_user_completers'):
                    p.update_dept_user_completers()
                p = p.parent()
                
            # (Đã tắt tự động check khi khởi chạy để tránh xung đột giao diện)
            # QTimer.singleShot(1000, self.start_onedrive_check)
        except Exception as e:
            self.table.blockSignals(False)
            QMessageBox.critical(self, "Lỗi", f"Không thể đọc cơ sở dữ liệu SQLite:\n{e}")

    def start_single_check(self, row_idx, url, mst):
        """Kiểm tra link OneDrive cho một dòng duy nhất"""
        if not url or not str(url).startswith('http'):
            self.on_check_progress(row_idx, "Skip")
            return

        # Vô hiệu hóa nút để tránh spam
        sender = self.sender()
        if sender: sender.setEnabled(False)

        # Chạy worker cho 1 task
        self.single_worker = WebValidationWorker([(row_idx, url, mst)], headless=True)
        self.single_worker.progress_sig.connect(self.on_check_progress)
        self.single_worker.done_sig.connect(lambda: sender.setEnabled(True) if sender else None)
        self.single_worker.done_sig.connect(self.save_to_sqlite)
        self.single_worker.start()

    def on_check_progress(self, row, result):
        if self.col_indices["doublecheck"] != -1:
            # Khóa tín hiệu để tránh gọi các hàm lưu/xử lý trung gian gây lag/nhảy
            self.table.blockSignals(True)
            
            # Tắt sắp xếp tạm thời
            sorting_enabled = self.table.isSortingEnabled()
            self.table.setSortingEnabled(False)
            
            # Ghi nhớ vị trí cuộn (Scroll) hiện tại
            v_scroll = self.table.verticalScrollBar().value()
            h_scroll = self.table.horizontalScrollBar().value()
            
            item = QTableWidgetItem(result)
            if result == "OK":
                item.setForeground(QColor("#52c41a")) # Xanh lá
            else:
                item.setForeground(QColor("#f5222d")) # Đỏ
            
            self.table.setItem(row, self.col_indices["doublecheck"], item)
            
            # Khôi phục trạng thái sắp xếp và vị trí cuộn ngay lập tức
            self.table.setSortingEnabled(sorting_enabled)
            self.table.verticalScrollBar().setValue(v_scroll)
            self.table.horizontalScrollBar().setValue(h_scroll)
            
            self.table.blockSignals(False)
            # Ép giao diện vẽ lại
            self.table.viewport().update()

    def on_check_done(self):
        # Thông báo hoàn tất sau khi check đơn lẻ (nếu cần)
        pass


    def on_cell_double_clicked(self, row, column):
        """Mở trình duyệt khi nhấp đúp vào cột link"""
        header_item = self.table.horizontalHeaderItem(column)
        if not header_item:
            return
            
        col_name = header_item.text().lower()
        if "link1" in col_name or "link onedrive" in col_name:
            item = self.table.item(row, column)
            if item:
                url = item.text().strip()
                if url.startswith("http"):
                    try:
                        webbrowser.open(url)
                    except Exception as e:
                        print(f"Không thể mở link: {e}")

    def on_item_changed(self, item):
        """Xử lý khi người dùng sửa nội dung ô trực tiếp"""
        # Nếu cột sửa là "Bàn giao", cần cập nhật lại màu sắc hàng
        col_idx_bangiao = -1
        for j in range(self.table.columnCount()):
            hdr = self.table.horizontalHeaderItem(j).text().upper()
            if "BÀN GIAO" in hdr and "NGÀY" not in hdr:
                col_idx_bangiao = j
                break
        
        if item.column() == col_idx_bangiao:
            is_delivered = str(item.text()) in ["1", "1.0", 1, 1.0]
            row = item.row()
            for k in range(self.table.columnCount()):
                cell_item = self.table.item(row, k)
                if cell_item:
                    if is_delivered:
                        cell_item.setBackground(QColor("#d4edda"))
                    else:
                        cell_item.setBackground(QColor("#ffffff")) # Trả về trắng
        
        # Tự động lưu vào SQLite
        self.save_to_sqlite()

    def filter_table(self):
        filter_text = self.txt_filter.text().lower()
        for i in range(self.table.rowCount()):
            match = False
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item and filter_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(i, not match)

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return

        menu = QMenu()
        
        # Chỉ sao chép nội dung ô đang trỏ chuột tới (theo yêu cầu người dùng)
        content = item.text()
        copy_action = QAction("📋 Sao chép (Copy)", self)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(content))

        export_action = QAction("🚀 Xuất Excel (Export view)", self)
        export_action.triggered.connect(self.export_to_excel)
        
        delete_action = QAction("🗑️ Xóa dòng đã chọn", self)
        delete_action.triggered.connect(self.delete_selected_rows)

        menu.addAction(copy_action)
        menu.addSeparator()
        menu.addAction(export_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def delete_selected_rows(self):
        """Xóa các dòng đang được chọn khỏi bảng và cơ sở dữ liệu"""
        selection = self.table.selectedRanges()
        if not selection:
            return
            
        rows_to_delete = sorted(set(index for s in selection for index in range(s.topRow(), s.bottomRow() + 1)), reverse=True)
        
        if not rows_to_delete:
            return
            
        reply = QMessageBox.question(
            self, 
            "Xác nhận xóa", 
            f"Bạn có chắc chắn muốn xóa {len(rows_to_delete)} dòng đã chọn không?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Tắt tín hiệu để tránh trigger lưu liên tục trong vòng lặp
            self.table.blockSignals(True)
            for r in rows_to_delete:
                self.table.removeRow(r)
            self.table.blockSignals(False)
            
            # Lưu lại vào SQLite
            self.save_to_sqlite()
            QMessageBox.information(self, "Thành công", f"Đã xóa {len(rows_to_delete)} dòng thành công!")

    def add_new_row(self):
        """Thêm một dòng trống mới vào cuối bảng"""
        self.table.blockSignals(True)
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        # Khởi tạo các ô trống để người dùng gõ
        for j in range(self.table.columnCount() - 1):
            item = QTableWidgetItem("")
            self.table.setItem(row_idx, j, item)
            
        # Thêm nút Check cho dòng mới
        self.add_check_button_to_row(row_idx, "", "")
        
        self.table.blockSignals(False)
        self.table.scrollToBottom()
        self.table.selectRow(row_idx)

    def add_check_button_to_row(self, row_idx, url, mst):
        """Tạo và gắn nút Check vào một hàng cụ thể"""
        btn_check = QPushButton("🔍 Check")
        btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_check.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_check.setStyleSheet("""
            QPushButton { background-color: #f0f0f0; border: 1px solid #ccc; font-size: 11px; padding: 2px; border-radius: 3px; }
            QPushButton:hover { background-color: #e0e0e0; border-color: #999; }
        """)
        
        # Sử dụng lambda với tham số mặc định để bắt giá trị hiện tại
        btn_check.clicked.connect(lambda checked, r=row_idx: self.on_check_button_clicked(r))
        self.table.setCellWidget(row_idx, self.table.columnCount() - 1, btn_check)

    def on_check_button_clicked(self, row_idx):
        """Xử lý khi bấm nút Check (lấy dữ liệu mới nhất từ hàng)"""
        # Cần tìm lại index cột vì có thể người dùng đã thay đổi thứ tự
        col_link = -1
        col_mst = -1
        for j in range(self.table.columnCount()):
            hdr = self.table.horizontalHeaderItem(j).text().lower()
            if "link1" in hdr: col_link = j
            if "mst" in hdr: col_mst = j
            
        url = self.table.item(row_idx, col_link).text() if col_link != -1 and self.table.item(row_idx, col_link) else ""
        mst = self.table.item(row_idx, col_mst).text() if col_mst != -1 and self.table.item(row_idx, col_mst) else ""
        
        self.start_single_check(row_idx, url, mst)

    def mark_as_delivered(self, company_name, phong="", user=""):
        """Tự động đánh dấu bàn giao dựa trên MST tìm thấy trong tên đơn vị"""
        if not company_name: return False
        
        col_idx_mst = -1
        col_idx_phong = -1
        col_idx_user = -1
        col_idx_bangiao = -1
        col_idx_ngaybangiao = -1
        for j in range(self.table.columnCount()):
            hdr = self.table.horizontalHeaderItem(j)
            if not hdr: continue
            h = hdr.text().upper()
            if "MST" in h: col_idx_mst = j
            elif "PHÒNG" in h or "PHONG" in h: col_idx_phong = j
            elif "USER" in h: col_idx_user = j
            elif "NGÀY BÀN GIAO" in h: col_idx_ngaybangiao = j
            elif "BÀN GIAO" in h: col_idx_bangiao = j
            
        if col_idx_mst == -1 or col_idx_bangiao == -1: return False

        current_date_str = datetime.now().strftime("%d/%m/%Y")
        changed = False
        for i in range(self.table.rowCount()):
            mst_item = self.table.item(i, col_idx_mst)
            if mst_item and mst_item.text().strip() and mst_item.text().strip() in company_name:
                # Đã tìm thấy MST khớp
                # Cập nhật Phòng
                if col_idx_phong != -1 and phong:
                    p_item = self.table.item(i, col_idx_phong)
                    if p_item:
                        if p_item.text().strip() != phong.strip():
                            p_item.setText(phong.strip())
                            changed = True
                    else:
                        self.table.setItem(i, col_idx_phong, QTableWidgetItem(phong.strip()))
                        changed = True

                # Cập nhật User
                if col_idx_user != -1 and user:
                    u_item = self.table.item(i, col_idx_user)
                    if u_item:
                        if u_item.text().strip() != user.strip():
                            u_item.setText(user.strip())
                            changed = True
                    else:
                        self.table.setItem(i, col_idx_user, QTableWidgetItem(user.strip()))
                        changed = True

                bg_item = self.table.item(i, col_idx_bangiao)
                if bg_item and bg_item.text() != "1":
                    bg_item.setText("1")
                    changed = True
                
                if col_idx_ngaybangiao != -1:
                    nbg_item = self.table.item(i, col_idx_ngaybangiao)
                    if nbg_item:
                        nbg_item.setText(current_date_str)
                        changed = True

                # Tô màu lại dòng
                for k in range(self.table.columnCount()):
                    cell = self.table.item(i, k)
                    if cell:
                        cell.setBackground(QColor("#d4edda"))
        
        if changed:
            self.save_to_sqlite()
            return True
        return False

    def mark_as_delivered_by_mtc(self, mtc):
        """Tự động đánh dấu bàn giao dựa trên MTC"""
        if not mtc: return False
        
        col_idx_mtc = -1
        col_idx_bangiao = -1
        col_idx_ngaybangiao = -1
        for j in range(self.table.columnCount()):
            h = self.table.horizontalHeaderItem(j).text().upper()
            if "MTC" in h: col_idx_mtc = j
            if "NGÀY BÀN GIAO" in h: col_idx_ngaybangiao = j
            elif "BÀN GIAO" in h: col_idx_bangiao = j
            
        if col_idx_mtc == -1 or col_idx_bangiao == -1: return False

        current_date_str = datetime.now().strftime("%d/%m/%Y")
        changed = False
        for i in range(self.table.rowCount()):
            mtc_item = self.table.item(i, col_idx_mtc)
            if mtc_item and mtc_item.text().strip() == mtc.strip():
                bg_item = self.table.item(i, col_idx_bangiao)
                if bg_item and bg_item.text() != "1":
                    bg_item.setText("1")
                    changed = True

                if col_idx_ngaybangiao != -1:
                    nbg_item = self.table.item(i, col_idx_ngaybangiao)
                    if nbg_item:
                        nbg_item.setText(current_date_str)
                        changed = True

                # Tô màu lại dòng
                for k in range(self.table.columnCount()):
                    cell = self.table.item(i, k)
                    if cell:
                        cell.setBackground(QColor("#d4edda"))
                    changed = True
        
    def assign_company_and_mark_delivered(self, mtc, company_name, phong="", user=""):
        """Gán thông tin công ty và tự động đánh dấu bàn giao dựa trên MTC"""
        if not mtc or not company_name: return False
        
        mst = company_name.split("_")[0] if "_" in company_name else company_name
        comp_name = company_name.split("_")[1] if "_" in company_name else ""
        
        col_idx_mtc = -1
        col_idx_mst = -1
        col_idx_name = -1
        col_idx_phong = -1
        col_idx_user = -1
        col_idx_bangiao = -1
        col_idx_ngaybangiao = -1
        
        for j in range(self.table.columnCount()):
            hdr = self.table.horizontalHeaderItem(j)
            if not hdr: continue
            h = hdr.text().upper()
            if "MTC" in h: col_idx_mtc = j
            elif "MST" in h: col_idx_mst = j
            elif "TÊN CÔNG TY" in h: col_idx_name = j
            elif "PHÒNG" in h or "PHONG" in h: col_idx_phong = j
            elif "USER" in h: col_idx_user = j
            elif "NGÀY BÀN GIAO" in h: col_idx_ngaybangiao = j
            elif "BÀN GIAO" in h: col_idx_bangiao = j
            
        if col_idx_mtc == -1 or col_idx_bangiao == -1: return False

        current_date_str = datetime.now().strftime("%d/%m/%Y")
        changed = False
        for i in range(self.table.rowCount()):
            mtc_item = self.table.item(i, col_idx_mtc)
            if mtc_item and mtc_item.text().strip() == mtc.strip():
                # Cập nhật MST
                if col_idx_mst != -1:
                    mst_item = self.table.item(i, col_idx_mst)
                    if mst_item:
                        old_mst = mst_item.text().strip()
                        if old_mst != mst:
                            mst_item.setText(mst)
                            changed = True
                
                # Cập nhật Tên Công Ty
                if col_idx_name != -1:
                    name_item = self.table.item(i, col_idx_name)
                    if name_item:
                        old_name = name_item.text().strip()
                        if old_name != comp_name:
                            name_item.setText(comp_name)
                            changed = True
                        
                # Cập nhật Phòng
                if col_idx_phong != -1 and phong:
                    p_item = self.table.item(i, col_idx_phong)
                    if p_item:
                        if p_item.text().strip() != phong.strip():
                            p_item.setText(phong.strip())
                            changed = True
                    else:
                        self.table.setItem(i, col_idx_phong, QTableWidgetItem(phong.strip()))
                        changed = True

                # Cập nhật User
                if col_idx_user != -1 and user:
                    u_item = self.table.item(i, col_idx_user)
                    if u_item:
                        if u_item.text().strip() != user.strip():
                            u_item.setText(user.strip())
                            changed = True
                    else:
                        self.table.setItem(i, col_idx_user, QTableWidgetItem(user.strip()))
                        changed = True

                # Cập nhật Bàn Giao
                bg_item = self.table.item(i, col_idx_bangiao)
                if bg_item:
                    old_bg = bg_item.text().strip()
                    if old_bg != "1":
                        bg_item.setText("1")
                        changed = True

                # Cập nhật Ngày Bàn Giao
                if col_idx_ngaybangiao != -1:
                    nbg_item = self.table.item(i, col_idx_ngaybangiao)
                    if nbg_item:
                        nbg_item.setText(current_date_str)
                        changed = True
                
                # Tô màu lại dòng thành xanh lá nhạt
                for k in range(self.table.columnCount()):
                    cell = self.table.item(i, k)
                    if cell:
                        cell.setBackground(QColor("#d4edda"))
                        
        if changed:
            self.save_to_sqlite()
            return True
        return False

    def save_to_sqlite(self):
        """Ghi dữ liệu hiện tại từ bảng vào file SQLite gốc (Persistence)"""
        if not hasattr(self, 'current_db_path') or not self.current_db_path:
            return
            
        try:
            data = []
            header = []
            # Chỉ lấy đến columnCount - 1 để loại bỏ cột nút bấm Check ở cuối
            for j in range(self.table.columnCount() - 1):
                header.append(self.table.horizontalHeaderItem(j).text())
            
            for i in range(self.table.rowCount()):
                row_data = []
                for j in range(self.table.columnCount() - 1):
                    item = self.table.item(i, j)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            df = pd.DataFrame(data, columns=header)
            conn = sqlite3.connect(self.current_db_path)
            df.to_sql("database", conn, if_exists="replace", index=False)
            conn.close()
            
            # Cập nhật completer ở MainApp
            p = self.parent()
            while p:
                if hasattr(p, 'update_mtc_completer'):
                    p.update_mtc_completer()
                if hasattr(p, 'update_dept_user_completers'):
                    p.update_dept_user_completers()
                p = p.parent()
        except Exception as e:
            print(f"Lỗi tự động lưu SQLite: {e}")

    def copy_selection(self):
        selection = self.table.selectedRanges()
        if not selection:
            return
            
        rows = sorted(set(index for s in selection for index in range(s.topRow(), s.bottomRow() + 1)))
        cols = sorted(set(index for s in selection for index in range(s.leftColumn(), s.rightColumn() + 1)))
        
        output = ""
        for r in rows:
            row_data = []
            for c in cols:
                item = self.table.item(r, c)
                row_data.append(item.text() if item else "")
            output += "\t".join(row_data) + "\n"
            
        QApplication.clipboard().setText(output)

    def export_to_excel(self):
        active_year = CONFIG.get("ACTIVE_YEAR", "2024")
        default_name = f"database_{active_year}.xlsx"
        save_path, _ = QFileDialog.getSaveFileName(self, "Lưu file Excel", default_name, "Excel Files (*.xlsx)")
        if not save_path:
            return
            
        try:
            # Thu thập dữ liệu từ SQLite thay vì từ view bảng (hoặc từ view bảng nếu muốn xuất đúng filter)
            # Ở đây ta xuất từ view bảng để giữ nguyên bộ lọc (Filter) của người dùng
            data = []
            header = []
            # Bỏ cột nút bấm ở cuối
            for j in range(self.table.columnCount() - 1):
                header.append(self.table.horizontalHeaderItem(j).text())
            
            for i in range(self.table.rowCount()):
                if not self.table.isRowHidden(i):
                    row_data = []
                    for j in range(self.table.columnCount() - 1):
                        item = self.table.item(i, j)
                        row_data.append(item.text() if item else "")
                    data.append(row_data)
            
            df = pd.DataFrame(data, columns=header)
            df.to_excel(save_path, index=False, engine='openpyxl')
            QMessageBox.information(self, "Thành công", f"Đã xuất dữ liệu ra file:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {e}")

class QRGeneratorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Main Card
        self.card = QFrame()
        self.card.setObjectName("Card")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        # --- HEADER ---
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        
        title = QLabel("🔳 QUẢN LÝ & TẠO MÃ QR")
        title.setStyleSheet("font-weight: bold; font-size: 22px; color: #722ed1;")
        
        subtitle = QLabel("ℹ️ Tự động tạo mã QR từ Link1 và MTC trong Database (Offline)")
        subtitle.setStyleSheet("color: #8c8c8c; font-size: 13px; font-style: italic;")
        
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        
        # --- ACTIONS ---
        btn_layout = QHBoxLayout()
        
        self.btn_export = QPushButton("📊 Xuất Excel")
        self.btn_export.setFixedWidth(140)
        self.btn_export.setFixedHeight(45)
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton { background-color: #52c41a; color: white; border-radius: 8px; font-weight: bold; font-size: 15px; }
            QPushButton:hover { background-color: #73d13d; }
        """)
        self.btn_export.clicked.connect(self.export_to_excel)

        self.btn_generate = QPushButton("🚀 Tạo Mã QR")
        self.btn_generate.setFixedWidth(160)
        self.btn_generate.setFixedHeight(45)
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setStyleSheet("""
            QPushButton { background-color: #722ed1; color: white; border-radius: 8px; font-weight: bold; font-size: 15px; }
            QPushButton:hover { background-color: #9254de; }
            QPushButton:disabled { background-color: #d9d9d9; color: #8c8c8c; }
        """)
        self.btn_generate.clicked.connect(self.start_generation)
        
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_generate)
        header_layout.addLayout(btn_layout)
        
        card_layout.addLayout(header_layout)
        
        # --- INFO BOX ---
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #f9f0ff; border-left: 4px solid #722ed1; border-radius: 4px; padding: 10px;")
        info_layout = QVBoxLayout(info_frame)
        
        self.lbl_qr_path = QLabel(f"📂 <b>Thư mục lưu:</b> {os.path.join(APP_ROOT, 'QR')}")
        self.lbl_year_info = QLabel(f"📅 <b>Năm làm việc:</b> {CONFIG.get('ACTIVE_YEAR', '2024')}")
        
        info_layout.addWidget(self.lbl_qr_path)
        info_layout.addWidget(self.lbl_year_info)
        card_layout.addWidget(info_frame)
        
        # --- CONSOLE ---
        console_box = QVBoxLayout()
        console_box.setSpacing(5)
        console_box.addWidget(QLabel("📜 Nhật ký xử lý:"))
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit { 
                background-color: #fafafa; 
                border: 1px solid #e8e8e8; 
                border-radius: 8px; 
                padding: 10px;
                color: #595959;
            }
        """)
        self.console.setPlaceholderText("Nhật ký tạo mã QR sẽ hiển thị tại đây...")
        console_box.addWidget(self.console)
        
        self.progress = QProgressBar()
        self.progress.setFixedHeight(8)
        self.progress.setVisible(False)
        console_box.addWidget(self.progress)
        
        card_layout.addLayout(console_box)
        
        main_layout.addWidget(self.card)

    def start_generation(self):
        data_to_process = [] # List of (mtc, link)
        
        # Lấy dữ liệu từ SQLite
        active_year = CONFIG.get("ACTIVE_YEAR", "2024")
        year_cfg = CONFIG.get("YEAR_CONFIGS", {}).get(active_year, {})
        db_p_raw = year_cfg.get("DATABASE_PATH", "database")
        
        if os.path.isabs(db_p_raw):
            db_path = db_p_raw
        else:
            db_path = os.path.normpath(os.path.join(APP_ROOT, db_p_raw))
            
        target_db = f"DANH SACH THE {active_year}.db"
        db_file = os.path.join(db_path, target_db)
        
        if not os.path.exists(db_file):
            QMessageBox.critical(self, "Lỗi", f"Không tìm thấy database: {db_file}")
            return
            
        try:
            conn = sqlite3.connect(db_file)
            df = pd.read_sql_query('SELECT * FROM "database"', conn)
            conn.close()
            
            col_link = ""
            col_mtc = ""
            for c in df.columns:
                if "LINK1" in c.upper(): col_link = c
                if "MTC" in c.upper(): col_mtc = c
                
            if not col_link or not col_mtc:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy cột Link1 hoặc MTC trong database.")
                return
                
            for _, row in df.iterrows():
                l = str(row[col_link]).strip()
                m = str(row[col_mtc]).strip()
                if l and l != "None" and l.startswith("http"):
                    data_to_process.append((m, l))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi đọc database: {e}")
            return

        if not data_to_process:
            QMessageBox.warning(self, "Thông báo", "Không có dữ liệu hợp lệ (Link1) để tạo QR.")
            return

        # Tạo folder QR
        qr_dir = os.path.join(APP_ROOT, "QR")
        if not os.path.exists(qr_dir):
            os.makedirs(qr_dir, exist_ok=True)
            
        self.btn_generate.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(data_to_process))
        self.progress.setValue(0)
        self.console.clear()
        self.console.append(f"⏳ Bắt đầu xử lý {len(data_to_process)} mục...")
        
        # Chạy worker
        self.worker = QRWorker(data_to_process, qr_dir)
        self.worker.log_sig.connect(self.console.append)
        self.worker.progress_sig.connect(self.progress.setValue)
        self.worker.done_sig.connect(self.on_finished)
        self.worker.start()

    def on_finished(self):
        self.btn_generate.setEnabled(True)
        QMessageBox.information(self, "Hoàn tất", "Đã tạo mã QR xong! Kiểm tra thư mục 'QR'.")

    def export_to_excel(self):
        active_year = CONFIG.get("ACTIVE_YEAR", "2024")
        save_path, _ = QFileDialog.getSaveFileName(self, "Lưu file Excel", f"Danh_Sach_QR_{active_year}.xlsx", "Excel Files (*.xlsx)")
        if not save_path:
            return
            
        try:
            # Lấy dữ liệu từ SQLite
            year_cfg = CONFIG.get("YEAR_CONFIGS", {}).get(active_year, {})
            db_p_raw = year_cfg.get("DATABASE_PATH", "database")
            db_path = db_p_raw if os.path.isabs(db_p_raw) else os.path.normpath(os.path.join(APP_ROOT, db_p_raw))
            db_file = os.path.join(db_path, f"DANH SACH THE {active_year}.db")
            
            if not os.path.exists(db_file):
                QMessageBox.critical(self, "Lỗi", f"Không tìm thấy database: {db_file}")
                return
                
            conn = sqlite3.connect(db_file)
            df = pd.read_sql_query('SELECT * FROM "database"', conn)
            conn.close()
            
            # Xuất toàn bộ data
            df.to_excel(save_path, index=False, engine='openpyxl')
            QMessageBox.information(self, "Thành công", f"Đã xuất dữ liệu ra file:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {e}")

class QRWorker(QThread):
    log_sig = pyqtSignal(str)
    progress_sig = pyqtSignal(int)
    done_sig = pyqtSignal()

    def __init__(self, data_list, qr_dir):
        super().__init__()
        self.data_list = data_list # List of (mtc, link)
        self.qr_dir = qr_dir

    def run(self):
        success_count = 0
        error_count = 0
        
        for i, (mtc, link) in enumerate(self.data_list):
            mtc = mtc.strip()
            link = link.strip()
            
            if not link or not link.startswith("http"):
                self.log_sig.emit(f"⚠️ Dòng {i+1}: Link không hợp lệ, bỏ qua.")
                self.progress_sig.emit(i + 1)
                continue
                
            if not mtc or mtc == "None":
                mtc = f"QR_{i+1}"
                
            try:
                # Sử dụng thư viện qrcode nội bộ (Vĩnh viễn/Offline)
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(link)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                
                filename = f"{mtc}.png"
                # Làm sạch filename
                filename = "".join([c for c in filename if c.isalnum() or c in "._- "])
                filepath = os.path.join(self.qr_dir, filename)
                
                img.save(filepath)
                success_count += 1
            except Exception as e:
                self.log_sig.emit(f"❌ Dòng {i+1} ({mtc}): Lỗi - {e}")
                error_count += 1
            
            self.progress_sig.emit(i + 1)
            
        self.log_sig.emit(f"\n🎯 HOÀN TẤT: Thành công {success_count}, Thất bại {error_count}.")
        self.done_sig.emit()

# =================================================================================
# 🛠️ CÁC WORKER XỬ LÝ
# =================================================================================

# --- 1. WORKER QUÉT & XÓA RÁC ---
class CleanerWorker(QThread):
    log_sig = pyqtSignal(str)
    done_sig = pyqtSignal()

    def __init__(self, companies):
        super().__init__()
        self.companies = companies if isinstance(companies, list) else [companies]

    def is_junk(self, filename):
        if filename in IGNORE_NAMES: return True
        if any(filename.startswith(pfx) for pfx in TEMP_PREFIXES): return True
        ext = os.path.splitext(filename)[1].lower()
        return ext in JUNK_EXTS

    def run(self):
        self.log_sig.emit("🧹 [BƯỚC 1] BẮT ĐẦU DỌN RÁC")
        total_deleted = 0
        for company in self.companies:
            self.log_sig.emit(f"🧹 Đang dọn rác: {company}")
            base_path = os.path.join(CONFIG["SRC_ROOT"], company, CONFIG["YEAR"])
            
            if not os.path.exists(base_path):
                self.log_sig.emit(f"⚠️ Không tìm thấy nguồn: {base_path}")
                continue

            company_deleted = 0
            for sub in CONFIG["SUBFOLDERS"]:
                sub_path = os.path.join(base_path, sub)
                if not os.path.exists(sub_path): continue
                
                for root, _, files in os.walk(sub_path):
                    for f in files:
                        if self.is_junk(f):
                            full_path = os.path.join(root, f)
                            try:
                                os.remove(full_path)
                                self.log_sig.emit(f"   🗑️ Đã xóa rác: {f}")
                                company_deleted += 1
                                total_deleted += 1
                            except Exception as e:
                                self.log_sig.emit(f"   ❌ Lỗi xóa {f}: {e}")
            if company_deleted == 0:
                self.log_sig.emit("   ✅ Không phát hiện file rác.")
            else:
                self.log_sig.emit(f"   ✅ Đã dọn sạch {company_deleted} file rác.")
        
        self.log_sig.emit(f"✅ Hoàn tất dọn rác. Tổng số file rác đã xóa: {total_deleted}")
        self.done_sig.emit()


# --- 2. WORKER ĐỒNG BỘ (SYNC) ---
class SyncWorker(QThread):
    log_sig = pyqtSignal(str)
    done_sig = pyqtSignal()

    def __init__(self, companies):
        super().__init__()
        self.companies = companies if isinstance(companies, list) else [companies]
        self.copied_count = 0
        self.deleted_count = 0
        self.total_copied = 0
        self.total_deleted = 0

    def is_ignored(self, name):
        return (name in IGNORE_NAMES) or name.startswith("~$")

    def delete_extra(self, dest_dir, src_dir):
        if not os.path.exists(dest_dir): return
        if not os.path.exists(src_dir):
            try:
                # Count files inside before deleting
                del_files = 0
                for root, dirs, files in os.walk(dest_dir):
                    del_files += len(files)
                shutil.rmtree(dest_dir)
                self.deleted_count += del_files
                self.log_sig.emit(f"   ➖ Xóa folder thừa: {os.path.basename(dest_dir)} (gồm {del_files} file)")
            except Exception as e:
                self.log_sig.emit(f"   ❌ Lỗi xóa folder: {e}")
            return

        for item in os.listdir(dest_dir):
            if self.is_ignored(item): continue
            d_item = os.path.join(dest_dir, item)
            s_item = os.path.join(src_dir, item)
            
            if not os.path.exists(s_item):
                try:
                    if os.path.isdir(d_item):
                        del_files = 0
                        for root, dirs, files in os.walk(d_item):
                            del_files += len(files)
                        shutil.rmtree(d_item)
                        self.deleted_count += del_files
                        self.log_sig.emit(f"   ➖ Xóa folder thừa: {item} (gồm {del_files} file)")
                    else:
                        os.remove(d_item)
                        self.deleted_count += 1
                        self.log_sig.emit(f"   ➖ Xóa thừa: {item}")
                except Exception as e:
                    self.log_sig.emit(f"   ❌ Lỗi xóa {item}: {e}")
            elif os.path.isdir(d_item) and os.path.isdir(s_item):
                self.delete_extra(d_item, s_item)

    def copy_missing(self, src_dir, dest_dir):
        if not os.path.exists(src_dir): return
        os.makedirs(dest_dir, exist_ok=True)
        
        for item in os.listdir(src_dir):
            if self.is_ignored(item): continue
            s_item = os.path.join(src_dir, item)
            d_item = os.path.join(dest_dir, item)

            if os.path.isdir(s_item):
                self.copy_missing(s_item, d_item)
            else:
                if not os.path.exists(d_item) or os.path.getsize(s_item) != os.path.getsize(d_item):
                    try:
                        shutil.copy2(s_item, d_item)
                        self.log_sig.emit(f"   ➕ Sync: {s_item} ➔ {d_item}")
                        self.copied_count += 1
                    except Exception as e:
                        self.log_sig.emit(f"   ❌ Lỗi copy: {e}")

    def run(self):
        self.log_sig.emit(f"\n☁️ [BƯỚC 2] ĐỒNG BỘ CLOUD (Server)")
        self.total_copied = 0
        self.total_deleted = 0
        
        for company in self.companies:
            self.copied_count = 0
            self.deleted_count = 0
            self.log_sig.emit(f"\n🚀 ĐANG ĐỒNG BỘ: {company}\n" + "-"*30)
            src_root = os.path.join(CONFIG["SRC_ROOT"], company, CONFIG["YEAR"])
            dest_root = os.path.join(CONFIG["DEST_ROOT"], f"{company}_{CONFIG['YEAR']}")

            self.log_sig.emit(f"   📁 Nguồn (Source): {src_root}")
            self.log_sig.emit(f"   📁 Đích (Destination): {dest_root}")

            if not os.path.exists(src_root):
                self.log_sig.emit(f"⚠️ Không tìm thấy nguồn dữ liệu cho {company}!")
                continue

            for sub in CONFIG["SUBFOLDERS"]:
                s_sub = os.path.join(src_root, sub)
                d_sub = os.path.join(dest_root, sub)
                
                if not os.path.exists(d_sub):
                    os.makedirs(d_sub, exist_ok=True)
                    self.log_sig.emit(f"   🔧 Đã tạo mới folder đích trơn: {sub}")

                self.delete_extra(d_sub, s_sub)
                self.copy_missing(s_sub, d_sub)
            
            total_dest_files = 0
            if os.path.exists(dest_root):
                for root_dir, _, files in os.walk(dest_root):
                    total_dest_files += len(files)

            self.log_sig.emit(f"✅ Đồng bộ {company} hoàn tất. (Đã sao chép/cập nhật: {self.copied_count} file, đã xóa: {self.deleted_count} file | Hiện có: {total_dest_files} file ở đích)")
            self.total_copied += self.copied_count
            self.total_deleted += self.deleted_count
        
        total_all_dest_files = 0
        for company in self.companies:
            dest_root = os.path.join(CONFIG["DEST_ROOT"], f"{company}_{CONFIG['YEAR']}")
            if os.path.exists(dest_root):
                for root_dir, _, files in os.walk(dest_root):
                    total_all_dest_files += len(files)

        self.log_sig.emit(f"\n🎯 TẤT CẢ QUÁ TRÌNH ĐỒNG BỘ ĐÃ HOÀN TẤT. (Tổng cộng đã sao chép/cập nhật: {self.total_copied} file, đã xóa: {self.total_deleted} file | Tổng số file ở đích: {total_all_dest_files} file)")
        self.done_sig.emit()


# --- 3. WORKER COPY USB ---
class CopyUSBWorker(QThread):
    log_sig = pyqtSignal(str)
    progress_sig = pyqtSignal(int, int) # cur, total
    done_sig = pyqtSignal()

    def __init__(self, company, usb_path):
        super().__init__()
        self.company = company
        self.usb_path = usb_path

    def run(self):
        self.log_sig.emit(f"\n💾 [BƯỚC 3] FORMAT VÀ COPY RA USB: {self.usb_path}")
        
        # Folder nguồn trên Cloud (sau khi đã sync)
        src_cloud = os.path.join(CONFIG["DEST_ROOT"], f"{self.company}_{CONFIG['YEAR']}")
        
        # Đặt tên folder đích trên USB (Giữ nguyên logic cũ)
        dest_usb = os.path.join(self.usb_path, f"{self.company}_{CONFIG['YEAR']}")

        if not os.path.exists(src_cloud):
            self.log_sig.emit(f"⚠️ Không tìm thấy dữ liệu trên Cloud để copy!")
            self.done_sig.emit()
            return

        # Format USB (Label)
        try:
            drive_letter = os.path.splitdrive(self.usb_path)[0] # "E:"
            label_name = self.company.split('_')[0] if '_' in self.company else self.company
            label_name = label_name[:11] # Giới hạn 11 ký tự
            self.log_sig.emit(f"   ⚠️ Lệnh chuẩn bị xóa toàn bộ thiết bị. Đang kích hoạt phương thức Format đĩa bởi PowerShell...")
            
            # Sử dụng PowerShell
            drive_char = drive_letter[0]
            ps_cmd = ["powershell.exe", "-NoProfile", "-Command", f"Format-Volume -DriveLetter {drive_char} -FileSystem FAT32 -NewFileSystemLabel '{label_name}' -Confirm:$false"]
            
            # Chạy ẩn (Không hiện cửa sổ cmd)
            CREATE_NO_WINDOW = 0x08000000
            res = subprocess.run(ps_cmd, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
            
            if res.returncode != 0:
                self.log_sig.emit(f"   ❌ Lỗi Format USB: {res.stderr.strip()[:100]}")
                self.log_sig.emit(f"   ⛔ QUÁ TRÌNH COPY BỊ HỦY (Yêu cầu USB trống và Format thành công).")
                self.done_sig.emit()
                return
            else:
                self.log_sig.emit(f"   ✅ Format USB chuẩn FAT32 và đổi tên thành '{label_name}' thành công!")
        except Exception as e:
            self.log_sig.emit(f"   ❌ Lỗi hệ thống khi Format USB: {e}")
            self.done_sig.emit()
            return

        # Đếm file
        files_to_copy = []
        for r, _, fs in os.walk(src_cloud):
            for f in fs:
                files_to_copy.append(os.path.join(r, f))
        
        total = len(files_to_copy)
        self.log_sig.emit(f"   📦 Tổng số file cần copy: {total}")

        current = 0
        for s_path in files_to_copy:
            rel = os.path.relpath(s_path, src_cloud)
            d_path = os.path.join(dest_usb, rel)
            
            os.makedirs(os.path.dirname(d_path), exist_ok=True)
            try:
                shutil.copy2(s_path, d_path)
            except Exception as e:
                self.log_sig.emit(f"   ❌ Lỗi copy file {rel}: {e}")
            
            current += 1
            self.progress_sig.emit(current, total)

        self.log_sig.emit("   ✅ Copy ra USB hoàn tất!")
        self.done_sig.emit()

# --- 4. WORKER WEB VALIDATION (PLAYWRIGHT) ---
class WebValidationWorker(QThread):
    progress_sig = pyqtSignal(int, str) # row_index, result_text
    done_sig = pyqtSignal()

    def __init__(self, tasks, headless=True):
        super().__init__()
        self.tasks = tasks # List of (row_idx, url, mst)
        self.headless = headless

    def run(self):
        no_count = 0
        with sync_playwright() as p:
            # Khởi tạo trình duyệt dùng chung cho toàn bộ batch
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()
            
            for row_idx, url, mst in self.tasks:
                if not url or not str(url).startswith('http'):
                    self.progress_sig.emit(row_idx, "Skip")
                    continue
                
                result = "NO"
                try:
                    # Truy cập trang web (Playwright tự xử lý redirect và JS)
                    # Chờ tối đa 20s hoặc đến khi load giao diện xong (networkidle)
                    page.goto(url, wait_until="networkidle", timeout=20000)
                    
                    # Lấy toàn bộ nội dung text của trang
                    content = page.content()
                    
                    if str(mst) in content:
                        result = "OK"
                    else:
                        result = "NO"
                except Exception:
                    result = "NO"
                
                self.progress_sig.emit(row_idx, result)
                
                if result == "NO":
                    no_count += 1
                    if no_count >= 2:
                        # Dừng quét do phát hiện bị chặn/spam
                        break
            
            browser.close()
        
        self.done_sig.emit()

# =================================================================================
# ⚙️ CỬA SỔ CÀI ĐẶT
# =================================================================================
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Cấu hình hệ thống")
        self.resize(550, 350)
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        
        # --- TAB 1: HỆ THỐNG (Path & Year) ---
        tab_system = QWidget()
        sys_layout = QFormLayout(tab_system)
        
        self.inp_src = QLineEdit(CONFIG.get("SRC_ROOT", ""))
        self.inp_dest = QLineEdit(CONFIG.get("DEST_ROOT", ""))
        
        
        # Database setup với nút Browse
        db_layout = QHBoxLayout()
        self.inp_db = QLineEdit("") # Sẽ nạp động theo năm
        self.inp_db.setMaximumWidth(250)
        self.btn_browse_db = QPushButton("📁 Duyệt")
        self.btn_browse_db.setFixedWidth(110)
        self.btn_browse_db.clicked.connect(self.browse_database_folder)
        db_layout.addWidget(self.inp_db)
        db_layout.addWidget(self.btn_browse_db)
        db_layout.addStretch()
        
        active_year = CONFIG.get("ACTIVE_YEAR", "2024")
        y_cfg = CONFIG.get("YEAR_CONFIGS", {}).get(active_year, {})
        db_val = y_cfg.get("DATABASE_PATH", "")
        if os.path.isabs(db_val) and APP_ROOT.lower() in db_val.lower():
            try:
                rel = os.path.relpath(db_val, APP_ROOT)
                if not rel.startswith(".."): db_val = rel
            except: pass
        self.inp_db.setText(db_val)

        self.inp_year = QLineEdit(CONFIG.get("YEAR", ""))
        self.inp_year.textChanged.connect(self.on_year_field_changed)
        
        self.inp_sub = QLineEdit(", ".join(CONFIG.get("SUBFOLDERS", [])))

        sys_layout.addRow("Thư mục Nguồn (SRC_ROOT):", self.inp_src)
        sys_layout.addRow("Thư mục Đích (DEST_ROOT):", self.inp_dest)
        sys_layout.addRow("Thư mục Database:", db_layout)
        sys_layout.addRow("Năm làm việc (YEAR):", self.inp_year)
        sys_layout.addRow("Thư mục con (Dấu phẩy):", self.inp_sub)
        
        self.tabs.addTab(tab_system, "📁 Hệ thống")

        # --- TAB 2: GIAO DIỆN ---
        tab_ui = QWidget()
        ui_layout = QFormLayout(tab_ui)
        
        self.inp_app_name = QLineEdit(CONFIG.get("APP_NAME", "Tool TL - CLOUD"))
        ui_layout.addRow("Tên phần mềm (Title):", self.inp_app_name)
        
        self.tabs.addTab(tab_ui, "🎨 Giao diện")

        layout.addWidget(self.tabs)

        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.btns.accepted.connect(self.save_settings)
        self.btns.rejected.connect(self.reject)
        layout.addWidget(self.btns)

    def on_year_field_changed(self, new_year):
        """Tự động cập nhật đường dẫn khi gõ năm mới trong Settings"""
        old_year = CONFIG.get("YEAR", "2024")
        if not new_year.strip() or new_year == old_year: return
        
        # Cập nhật DEST_ROOT và DB_PATH bằng cách thay thế chuỗi năm
        dest = self.inp_dest.text()
        db = self.inp_db.text()
        
        if old_year in dest:
            self.inp_dest.setText(dest.replace(old_year, new_year))
        if old_year in db:
            self.inp_db.setText(db.replace(old_year, new_year))

    def browse_database_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục Database", self.inp_db.text())
        if d:
            self.inp_db.setText(os.path.normpath(d))


    def save_settings(self):
        global CONFIG
        year_text = self.inp_year.text().strip()
        src_text = self.inp_src.text().strip()
        dest_text = self.inp_dest.text().strip()
        db_text = self.inp_db.text().strip()
        
        # Tự động tối ưu hóa đường dẫn (Portability)
        try:
            # Cho Database
            if os.path.isabs(db_text) and APP_ROOT.lower() in db_text.lower():
                rel_db = os.path.relpath(db_text, APP_ROOT)
                if not rel_db.startswith(".."):
                    db_text = rel_db
        except:
            pass

        CONFIG["SRC_ROOT"] = src_text
        CONFIG["DEST_ROOT"] = dest_text
        CONFIG["YEAR"] = year_text
        
        # Cập nhật vào YEAR_CONFIGS
        if "YEAR_CONFIGS" not in CONFIG: CONFIG["YEAR_CONFIGS"] = {}
        CONFIG["YEAR_CONFIGS"][year_text] = {
            "SRC_ROOT": src_text,
            "DEST_ROOT": dest_text,
            "DATABASE_PATH": db_text
        }
        CONFIG["ACTIVE_YEAR"] = year_text

        subs = [s.strip() for s in self.inp_sub.text().split(",") if s.strip()]
        CONFIG["SUBFOLDERS"] = subs
        CONFIG["APP_NAME"] = self.inp_app_name.text().strip() or "Tool TL - CLOUD"
        
        save_config(CONFIG)
        self.accept()

# =================================================================================
# 🏠 GIAO DIỆN CHÍNH (ALL-IN-ONE)
# =================================================================================
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        app_title = f"{CONFIG.get('APP_NAME', 'Tool TL - CLOUD')} v{CURRENT_VERSION}"
        self.setWindowTitle(app_title)
        self.resize(1100, 700)
        
        # Thiết lập Icon cho cửa sổ
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_path, "icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_path, "icon.png")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.setStyleSheet(STYLESHEET)

        # Main Widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- STACKED WIDGET (CHUYỂN ĐỔI VIEW) ---
        self.stack = QStackedWidget()
        
        # 1. VIEW CHÍNH (Dashboard)
        self.view_main = QWidget()
        view_main_layout = QHBoxLayout(self.view_main)
        view_main_layout.setContentsMargins(10, 10, 10, 10)
        view_main_layout.setSpacing(10)
        
        # Cấu trúc cũ được đưa vào đây
        
        # --- CỘT TRÁI: DANH SÁCH & CẤU HÌNH ---
        left_panel = QFrame()
        left_panel.setObjectName("Card")
        left_panel.setFixedWidth(350)
        left_layout = QVBoxLayout(left_panel)

        # Header Danh sách
        header_layout = QHBoxLayout()
        self.lbl_list = QLabel(f"📂 DANH SÁCH ({CONFIG['YEAR']})")
        self.lbl_list.setStyleSheet("font-weight: bold; font-size: 16px; color: #0078d4;")
        
        btn_settings = QPushButton("⚙️ Cấu hình")
        btn_settings.setStyleSheet("padding: 5px 10px; font-weight: normal; background-color: #f0f0f0; border: 1px solid #ccc; color: #333;")
        btn_settings.clicked.connect(self.open_settings)
        
        header_layout.addWidget(self.lbl_list)
        header_layout.addStretch()
        header_layout.addWidget(btn_settings)

        left_layout.addLayout(header_layout)
        
        # --- CHỌN NĂM LÀM VIỆC ---
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("📅 Năm làm việc:"))
        self.inp_active_year = QComboBox()
        self.inp_active_year.setFixedWidth(100)
        self.inp_active_year.setStyleSheet("padding: 3px; font-weight: bold; color: #0078d4;")
        self.inp_active_year.currentTextChanged.connect(self.on_year_changed)
        year_layout.addWidget(self.inp_active_year)
        year_layout.addStretch()
        left_layout.addLayout(year_layout)

        # --- CHỌN PHÒNG VÀ USER ---
        dept_user_group = QFrame()
        dept_user_group.setStyleSheet("background: #fdfdfd; border-radius: 6px; padding: 4px; border: 1px solid #e1dfdd;")
        dept_user_layout = QFormLayout(dept_user_group)
        dept_user_layout.setContentsMargins(6, 4, 6, 4)
        dept_user_layout.setHorizontalSpacing(8)
        dept_user_layout.setVerticalSpacing(4)

        lbl_phong = QLabel("🏢 Phòng:")
        lbl_phong.setStyleSheet("font-weight: bold; color: #333; font-size: 13px;")
        self.combo_phong = QComboBox()
        self.combo_phong.setEditable(True)
        self.combo_phong.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo_phong.lineEdit().setPlaceholderText("Chọn hoặc nhập Phòng...")
        self.combo_phong.setStyleSheet("background: #fff; padding: 4px; border-radius: 4px; border: 1px solid #ccc; font-size: 13px;")

        lbl_user = QLabel("👤 User:")
        lbl_user.setStyleSheet("font-weight: bold; color: #333; font-size: 13px;")
        self.combo_user = QComboBox()
        self.combo_user.setEditable(True)
        self.combo_user.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo_user.lineEdit().setPlaceholderText("Chọn hoặc nhập User...")
        self.combo_user.setStyleSheet("background: #fff; padding: 4px; border-radius: 4px; border: 1px solid #ccc; font-size: 13px;")

        dept_user_layout.addRow(lbl_phong, self.combo_phong)
        dept_user_layout.addRow(lbl_user, self.combo_user)
        left_layout.addWidget(dept_user_group)
        
        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Tìm Mã số thuế / Tên...")
        self.search_box.textChanged.connect(self.filter_list)
        left_layout.addWidget(self.search_box)

        # List Widget
        self.company_list = QListWidget()
        self.company_list.itemClicked.connect(self.on_company_select)
        left_layout.addWidget(self.company_list)

        # (Đã dời xuống dưới các nút Sync)


        # KHU VỰC NÚT XỬ LÝ (TÁCH BIỆT)
        actions_layout = QVBoxLayout()
        
        # Hàng nút Sync và Sync All
        sync_layout = QHBoxLayout()
        self.btn_sync = QPushButton("☁️ SYNC")
        self.btn_sync.setObjectName("SyncBtn")
        self.btn_sync.setFixedHeight(40)
        self.btn_sync.setEnabled(False)
        self.btn_sync.clicked.connect(self.run_sync)

        self.btn_sync_all = QPushButton("☁️ SYNC ALL")
        self.btn_sync_all.setObjectName("SyncAllBtn")
        self.btn_sync_all.setFixedHeight(40)
        self.btn_sync_all.setEnabled(False)
        self.btn_sync_all.clicked.connect(self.run_sync_all)
        
        sync_layout.addWidget(self.btn_sync)
        sync_layout.addWidget(self.btn_sync_all)

        # Chọn USB Area (Dời xuống từ phía trên)
        usb_group = QFrame()
        usb_group.setStyleSheet("background: #f9f9f9; border-radius: 6px; padding: 5px;")
        usb_layout = QVBoxLayout(usb_group)
        usb_layout.addWidget(QLabel("💾 Chọn Ổ USB Đích:"))
        
        h_usb = QHBoxLayout()
        self.usb_path_input = QLineEdit()
        self.usb_path_input.setPlaceholderText("Chưa chọn USB...")
        self.usb_path_input.setReadOnly(True)
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setObjectName("BrowseBtn")
        self.btn_browse.clicked.connect(self.browse_usb)
        
        h_usb.addWidget(self.usb_path_input)
        h_usb.addWidget(self.btn_browse)
        usb_layout.addLayout(h_usb)

        # Ô nhập MTC
        mtc_group = QFrame()
        mtc_group.setStyleSheet("background: #f9f9f9; border-radius: 6px; padding: 5px;")
        mtc_layout = QVBoxLayout(mtc_group)
        lbl_mtc = QLabel("🔑 MTC:")
        lbl_mtc.setStyleSheet("font-weight: bold;")
        self.mtc_input = QLineEdit()
        self.mtc_input.setPlaceholderText("Nhập MTC...")
        self.mtc_input.textChanged.connect(self.on_mtc_changed)
        mtc_layout.addWidget(lbl_mtc)
        mtc_layout.addWidget(self.mtc_input)

        self.btn_usb = QPushButton("💾 SAO CHÉP USB")
        self.btn_usb.setObjectName("USBBtn")
        self.btn_usb.setFixedHeight(40)
        self.btn_usb.setEnabled(False)
        self.btn_usb.clicked.connect(self.run_copy_usb)

        actions_layout.addLayout(sync_layout)
        actions_layout.addWidget(mtc_group)
        actions_layout.addWidget(usb_group)
        actions_layout.addWidget(self.btn_usb)

        left_layout.addLayout(actions_layout)
        
        # Status footer
        self.lbl_status = QLabel("Sẵn sàng.")
        self.lbl_status.setStyleSheet("color: #666; font-style: italic;")
        left_layout.addWidget(self.lbl_status)

        # --- CỘT PHẢI: LOG & PROGRESS ---
        right_panel = QFrame()
        right_panel.setObjectName("Card")
        right_layout = QVBoxLayout(right_panel)

        # Header Log Area
        log_header_layout = QHBoxLayout()
        log_header_layout.addWidget(QLabel("📜 Nhật ký xử lý (Log Realtime):"))
        log_header_layout.addStretch()

        self.btn_open_src = QPushButton("📂 Nguồn")
        self.btn_open_src.setStyleSheet("padding: 4px 8px; font-size: 12px; font-weight: normal; background-color: #f0f0f0; border: 1px solid #ccc; color: #333; border-radius: 4px;")
        self.btn_open_src.setToolTip("Mở thư mục nguồn")
        self.btn_open_src.setEnabled(False)
        self.btn_open_src.clicked.connect(self.open_source_folder)

        self.btn_open_dest = QPushButton("📁 Đích")
        self.btn_open_dest.setStyleSheet("padding: 4px 8px; font-size: 12px; font-weight: normal; background-color: #f0f0f0; border: 1px solid #ccc; color: #333; border-radius: 4px;")
        self.btn_open_dest.setToolTip("Mở thư mục đích")
        self.btn_open_dest.setEnabled(False)
        self.btn_open_dest.clicked.connect(self.open_dest_folder)

        log_header_layout.addWidget(self.btn_open_src)
        log_header_layout.addWidget(self.btn_open_dest)
        right_layout.addLayout(log_header_layout)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        right_layout.addWidget(self.console)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        # Add panels to main view layout
        view_main_layout.addWidget(left_panel)
        view_main_layout.addWidget(right_panel)

        # 2. VIEW DATA (Database)
        self.view_db = DatabaseView()

        # 3. VIEW QR
        self.view_qr = QRGeneratorView()

        # Thêm vào stack
        self.stack.addWidget(self.view_main)
        self.stack.addWidget(self.view_db)
        self.stack.addWidget(self.view_qr)

        # --- THANH NAVIGATION BÊN TRÁI (SIDEBAR) ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(70)
        self.sidebar.setStyleSheet("background-color: #ffffff; border-right: 1px solid #f0f0f0;")
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)
        side_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_nav_main = QPushButton("🏠\nMain")
        self.btn_nav_main.setObjectName("SideBtn")
        self.btn_nav_main.setFixedHeight(80)
        self.btn_nav_main.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_main.setProperty("active", "true")
        self.btn_nav_main.clicked.connect(lambda: self.switch_view(0))

        self.btn_nav_db = QPushButton("📊\nData")
        self.btn_nav_db.setObjectName("SideBtn")
        self.btn_nav_db.setFixedHeight(80)
        self.btn_nav_db.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_db.setProperty("active", "false")
        self.btn_nav_db.clicked.connect(lambda: self.switch_view(1))

        self.btn_nav_qr = QPushButton("🔳\nQR")
        self.btn_nav_qr.setObjectName("SideBtn")
        self.btn_nav_qr.setFixedHeight(80)
        self.btn_nav_qr.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_qr.setProperty("active", "false")
        self.btn_nav_qr.clicked.connect(lambda: self.switch_view(2))

        side_layout.addWidget(self.btn_nav_main)
        side_layout.addWidget(self.btn_nav_db)
        side_layout.addWidget(self.btn_nav_qr)

        # Gắn vào Main Layout (Sidebar bên TRÁI)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

        # Load Data
        self.all_companies = []
        self.selected_company = None
        self.selected_usb = None
        self._is_syncing_mtc_and_company = False
        
        # Đầu tiên load danh sách
        self.update_main_year_combobox()
        self.load_companies_from_src()
        self.update_mtc_completer()
        self.update_dept_user_completers()

        # Cài đặt Auto-detect USB
        self.usb_timer = QTimer(self)
        self.usb_timer.timeout.connect(self.auto_detect_usb)
        self.usb_timer.start(2000)


    def switch_view(self, index):
        self.stack.setCurrentIndex(index)
        self.btn_nav_main.setProperty("active", "true" if index == 0 else "false")
        self.btn_nav_db.setProperty("active", "true" if index == 1 else "false")
        self.btn_nav_qr.setProperty("active", "true" if index == 2 else "false")
        # Refresh style
        self.btn_nav_main.style().unpolish(self.btn_nav_main)
        self.btn_nav_main.style().polish(self.btn_nav_main)
        self.btn_nav_db.style().unpolish(self.btn_nav_db)
        self.btn_nav_db.style().polish(self.btn_nav_db)
        self.btn_nav_qr.style().unpolish(self.btn_nav_qr)
        self.btn_nav_qr.style().polish(self.btn_nav_qr)


    def load_companies_from_src(self):
        self.lbl_list.setText(f"📂 DANH SÁCH ({CONFIG['YEAR']})")
        self.console.append(f"⏳ Đang tải danh sách công ty từ: {CONFIG['SRC_ROOT']} (YEAR={CONFIG['YEAR']})...")
        QApplication.processEvents()
        
        if not os.path.exists(CONFIG['SRC_ROOT']):
            self.console.append(f"❌ Lỗi: Không tìm thấy đường dẫn {CONFIG['SRC_ROOT']}")
            return

        self.all_companies = []
        try:
            for name in sorted(os.listdir(CONFIG['SRC_ROOT'])):
                p = os.path.join(CONFIG['SRC_ROOT'], name)
                if os.path.isdir(p) and os.path.exists(os.path.join(p, CONFIG['YEAR'])):
                    self.all_companies.append(name)
        except Exception:
            pass

        self.filter_list("")

    def filter_list(self, text):
        search_text = self.search_box.text().lower()
        self.company_list.clear()
        for c in self.all_companies:
            if search_text in c.lower():
                self.company_list.addItem(QListWidgetItem(c))

    def on_company_select(self, item):
        self.selected_company = item.text()
        self.check_ready()
        
        if hasattr(self, '_is_syncing_mtc_and_company') and self._is_syncing_mtc_and_company:
            return
            
        self._is_syncing_mtc_and_company = True
        try:
            company_name = self.selected_company
            mst = company_name.split("_")[0] if "_" in company_name else company_name
            
            # Tìm trong self.view_db.table
            col_idx_mtc = -1
            col_idx_mst = -1
            col_idx_phong = -1
            col_idx_user = -1
            for j in range(self.view_db.table.columnCount()):
                hdr_item = self.view_db.table.horizontalHeaderItem(j)
                if hdr_item:
                    hdr_text = hdr_item.text().upper()
                    if "MTC" == hdr_text or "MTC" in hdr_text:
                        col_idx_mtc = j
                    elif "MST" == hdr_text or "MST" in hdr_text:
                        col_idx_mst = j
                    elif "PHÒNG" in hdr_text or "PHONG" in hdr_text:
                        col_idx_phong = j
                    elif "USER" in hdr_text:
                        col_idx_user = j
                        
            if col_idx_mst != -1:
                found = False
                for i in range(self.view_db.table.rowCount()):
                    mst_item = self.view_db.table.item(i, col_idx_mst)
                    if mst_item and mst_item.text().strip() == mst:
                        if col_idx_mtc != -1:
                            mtc_item = self.view_db.table.item(i, col_idx_mtc)
                            if mtc_item:
                                self.mtc_input.setText(mtc_item.text().strip())
                        if hasattr(self, 'combo_phong') and col_idx_phong != -1:
                            p_item = self.view_db.table.item(i, col_idx_phong)
                            if p_item and p_item.text().strip():
                                self.combo_phong.setCurrentText(p_item.text().strip())
                            else:
                                self.combo_phong.setCurrentText("")
                        if hasattr(self, 'combo_user') and col_idx_user != -1:
                            u_item = self.view_db.table.item(i, col_idx_user)
                            if u_item and u_item.text().strip():
                                self.combo_user.setCurrentText(u_item.text().strip())
                            else:
                                self.combo_user.setCurrentText("")
                        found = True
                        break
                if not found:
                    self.mtc_input.clear()
                    if hasattr(self, 'combo_phong'): self.combo_phong.setCurrentText("")
                    if hasattr(self, 'combo_user'): self.combo_user.setCurrentText("")
            else:
                self.mtc_input.clear()
                if hasattr(self, 'combo_phong'): self.combo_phong.setCurrentText("")
                if hasattr(self, 'combo_user'): self.combo_user.setCurrentText("")
        finally:
            self._is_syncing_mtc_and_company = False

    def on_mtc_changed(self, text):
        if hasattr(self, '_is_syncing_mtc_and_company') and self._is_syncing_mtc_and_company:
            return
            
        self._is_syncing_mtc_and_company = True
        try:
            mtc_text = text.strip()
            if not mtc_text:
                self._is_syncing_mtc_and_company = False
                return

            col_idx_mtc = -1
            col_idx_mst = -1
            col_idx_phong = -1
            col_idx_user = -1
            for j in range(self.view_db.table.columnCount()):
                hdr_item = self.view_db.table.horizontalHeaderItem(j)
                if hdr_item:
                    hdr_text = hdr_item.text().upper()
                    if "MTC" == hdr_text or "MTC" in hdr_text:
                        col_idx_mtc = j
                    elif "MST" == hdr_text or "MST" in hdr_text:
                        col_idx_mst = j
                    elif "PHÒNG" in hdr_text or "PHONG" in hdr_text:
                        col_idx_phong = j
                    elif "USER" in hdr_text:
                        col_idx_user = j

            if col_idx_mtc != -1 and col_idx_mst != -1:
                for i in range(self.view_db.table.rowCount()):
                    mtc_item = self.view_db.table.item(i, col_idx_mtc)
                    if mtc_item and mtc_item.text().strip() == mtc_text:
                        if hasattr(self, 'combo_phong') and col_idx_phong != -1:
                            p_item = self.view_db.table.item(i, col_idx_phong)
                            if p_item and p_item.text().strip():
                                self.combo_phong.setCurrentText(p_item.text().strip())
                        if hasattr(self, 'combo_user') and col_idx_user != -1:
                            u_item = self.view_db.table.item(i, col_idx_user)
                            if u_item and u_item.text().strip():
                                self.combo_user.setCurrentText(u_item.text().strip())
                        mst_item = self.view_db.table.item(i, col_idx_mst)
                        if mst_item:
                            mst_val = mst_item.text().strip()
                            if mst_val:
                                # Tìm công ty tương ứng trong self.all_companies
                                for company in self.all_companies:
                                    if mst_val in company:
                                        # Chọn dòng trong list
                                        items = self.company_list.findItems(company, Qt.MatchFlag.MatchExactly)
                                        if items:
                                            self.company_list.setCurrentItem(items[0])
                                            self.selected_company = company
                                            self.check_ready()
                                            break
                                break
        finally:
            self._is_syncing_mtc_and_company = False

    def update_mtc_completer(self):
        # Lấy tất cả MTC từ self.view_db.table
        mtc_list = []
        if not hasattr(self, 'view_db') or not hasattr(self.view_db, 'table'):
            return
            
        col_idx_mtc = -1
        for j in range(self.view_db.table.columnCount()):
            hdr = self.view_db.table.horizontalHeaderItem(j)
            if hdr and "MTC" in hdr.text().upper():
                col_idx_mtc = j
                break
        
        if col_idx_mtc != -1:
            for i in range(self.view_db.table.rowCount()):
                item = self.view_db.table.item(i, col_idx_mtc)
                if item:
                    text_val = item.text().strip()
                    if text_val:
                        mtc_list.append(text_val)
        
        # Loại bỏ trùng lặp và rỗng
        mtc_list = sorted(list(set(filter(None, mtc_list))))
        
        if not mtc_list:
            return
            
        completer = QCompleter(mtc_list, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.mtc_input.setCompleter(completer)

    def update_dept_user_completers(self):
        phong_list = []
        user_list = []
        
        # 1. Lấy từ self.view_db.table nếu đã load
        if hasattr(self, 'view_db') and hasattr(self.view_db, 'table') and self.view_db.table.rowCount() > 0:
            col_idx_phong = -1
            col_idx_user = -1
            for j in range(self.view_db.table.columnCount()):
                hdr = self.view_db.table.horizontalHeaderItem(j)
                if hdr:
                    h = hdr.text().upper()
                    if "PHÒNG" in h or "PHONG" in h: col_idx_phong = j
                    elif "USER" in h: col_idx_user = j
            
            if col_idx_phong != -1:
                for i in range(self.view_db.table.rowCount()):
                    item = self.view_db.table.item(i, col_idx_phong)
                    if item:
                        val = item.text().strip()
                        if val: phong_list.append(val)
                        
            if col_idx_user != -1:
                for i in range(self.view_db.table.rowCount()):
                    item = self.view_db.table.item(i, col_idx_user)
                    if item:
                        val = item.text().strip()
                        if val: user_list.append(val)
                        
        # 2. Nếu table chưa có dữ liệu hoặc rỗng, đọc trực tiếp từ SQLite hiện tại
        if not phong_list or not user_list:
            try:
                active_year = CONFIG.get("ACTIVE_YEAR", "2024")
                year_cfg = CONFIG.get("YEAR_CONFIGS", {}).get(active_year, {})
                db_p_raw = year_cfg.get("DATABASE_PATH", "database")
                db_path = db_p_raw if os.path.isabs(db_p_raw) else os.path.normpath(os.path.join(APP_ROOT, db_p_raw))
                db_file = os.path.join(db_path, f"DANH SACH THE {active_year}.db")
                if os.path.exists(db_file):
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute('PRAGMA table_info("database")')
                    cols = [c[1] for c in cursor.fetchall()]
                    col_p = next((c for c in cols if "PHÒNG" in c.upper() or "PHONG" in c.upper()), None)
                    col_u = next((c for c in cols if "USER" in c.upper()), None)
                    
                    if col_p:
                        cursor.execute(f'SELECT DISTINCT "{col_p}" FROM "database" WHERE "{col_p}" IS NOT NULL AND "{col_p}" != ""')
                        phong_list.extend([r[0].strip() for r in cursor.fetchall() if r[0] and r[0].strip()])
                    if col_u:
                        cursor.execute(f'SELECT DISTINCT "{col_u}" FROM "database" WHERE "{col_u}" IS NOT NULL AND "{col_u}" != ""')
                        user_list.extend([r[0].strip() for r in cursor.fetchall() if r[0] and r[0].strip()])
                    conn.close()
            except Exception as e:
                print(f"Lỗi đọc Phòng/User từ SQLite: {e}")

        # Loại bỏ trùng lặp và sắp xếp
        phong_list = sorted(list(set(filter(None, phong_list))))
        user_list = sorted(list(set(filter(None, user_list))))

        if hasattr(self, 'combo_phong'):
            current_phong = self.combo_phong.currentText()
            self.combo_phong.blockSignals(True)
            self.combo_phong.clear()
            self.combo_phong.addItem("")
            for p in phong_list:
                self.combo_phong.addItem(p)
            self.combo_phong.setCurrentText(current_phong)
            self.combo_phong.blockSignals(False)

            if phong_list:
                comp_phong = QCompleter(phong_list, self)
                comp_phong.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                comp_phong.setFilterMode(Qt.MatchFlag.MatchContains)
                self.combo_phong.setCompleter(comp_phong)

        if hasattr(self, 'combo_user'):
            current_user = self.combo_user.currentText()
            self.combo_user.blockSignals(True)
            self.combo_user.clear()
            self.combo_user.addItem("")
            for u in user_list:
                self.combo_user.addItem(u)
            self.combo_user.setCurrentText(current_user)
            self.combo_user.blockSignals(False)

            if user_list:
                comp_user = QCompleter(user_list, self)
                comp_user.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                comp_user.setFilterMode(Qt.MatchFlag.MatchContains)
                self.combo_user.setCompleter(comp_user)

    def browse_usb(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn ổ đĩa USB")
        if d:
            self.selected_usb = d
            self.usb_path_input.setText(d)
            self.check_ready()

    def check_ready(self):
        # Nút Sync All phụ thuộc vào việc có danh sách công ty không
        self.btn_sync_all.setEnabled(len(self.all_companies) > 0)

        if self.selected_company:
            self.btn_sync.setEnabled(True)
            self.btn_open_src.setEnabled(True)
            self.btn_open_dest.setEnabled(True)
        else:
            self.btn_sync.setEnabled(False)
            self.btn_open_src.setEnabled(False)
            self.btn_open_dest.setEnabled(False)

        if self.selected_company and self.selected_usb:
            self.btn_usb.setEnabled(True)
            self.lbl_status.setText(f"Đã chọn: {self.selected_company} -> USB: {self.selected_usb}")
        elif self.selected_company:
            self.btn_usb.setEnabled(False)
            self.lbl_status.setText(f"Đã chọn: {self.selected_company} (Chưa chọn USB)")
        else:
            self.btn_usb.setEnabled(False)
            self.lbl_status.setText("Sẵn sàng.")

    def auto_detect_usb(self):
        drives = get_valid_usb_drives()
        
        # Xóa chọn USB nếu nó ko còn tồn tại
        if self.selected_usb and not os.path.exists(self.selected_usb):
            self.selected_usb = None
            self.usb_path_input.setText("")
            self.check_ready()

        if drives and not self.selected_usb:
            first_drv = drives[0][0]
            self.selected_usb = first_drv
            self.usb_path_input.setText(first_drv)
            self.check_ready()

    def log(self, text):
        self.console.append(text)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def update_main_year_combobox(self):
        self.inp_active_year.blockSignals(True)
        self.inp_active_year.clear()
        
        active_year = CONFIG.get("ACTIVE_YEAR", "2024")
        year_cfg = CONFIG.get("YEAR_CONFIGS", {}).get(active_year, {})
        db_p_raw = year_cfg.get("DATABASE_PATH", "database")
        db_path = db_p_raw if os.path.isabs(db_p_raw) else os.path.normpath(os.path.join(APP_ROOT, db_p_raw))
        
        years = []
        if os.path.exists(db_path):
            for file in os.listdir(db_path):
                if file.startswith("DANH SACH THE ") and file.endswith(".db"):
                    parts = file.replace("DANH SACH THE ", "").replace(".db", "").strip()
                    if parts.isdigit():
                        years.append(parts)
        config_years = list(CONFIG.get("YEAR_CONFIGS", {}).keys())
        all_years = sorted(list(set(years + config_years + [active_year])), reverse=True)
        
        self.inp_active_year.addItems(all_years)
        self.inp_active_year.setCurrentText(active_year)
        self.inp_active_year.blockSignals(False)

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            # Cập nhật năm trong Combobox
            self.update_main_year_combobox()
            
            self.load_companies_from_src()
            self.view_db.load_data()
            app_title = f"{CONFIG.get('APP_NAME', 'Tool TL - CLOUD')} v{CURRENT_VERSION}"
            self.setWindowTitle(app_title)

    def smart_replace_paths(self, old_cfg, old_year, new_year):
        """Thay thế thông minh năm cũ bằng năm mới trong các đường dẫn"""
        new_cfg = {}
        for key, value in old_cfg.items():
            if isinstance(value, str):
                new_cfg[key] = value.replace(str(old_year), str(new_year))
            else:
                new_cfg[key] = value
        return new_cfg

    def on_year_changed(self, year_text):
        """Xử lý khi thay đổi năm làm việc (phải đủ 4 chữ số)"""
        global CONFIG
        year_text = year_text.strip()
        
        # Yêu cầu tối thiểu 4 chữ số để tránh load liên tục khi đang gõ
        if len(year_text) < 4:
            return
            
        old_year = CONFIG.get("ACTIVE_YEAR", "2024")
        if year_text == old_year:
            return

        # Nếu là năm mới hoàn toàn
        if year_text not in CONFIG["YEAR_CONFIGS"]:
            # Lấy cấu hình của năm hiện tại để làm mẫu
            current_cfg = CONFIG["YEAR_CONFIGS"].get(old_year, DEFAULT_CONFIG["YEAR_CONFIGS"]["2024"])
            new_cfg = self.smart_replace_paths(current_cfg, old_year, year_text)
            
            CONFIG["YEAR_CONFIGS"][year_text] = new_cfg

        # Cập nhật cấu hình hiện tại
        cfg = CONFIG["YEAR_CONFIGS"][year_text]
        CONFIG["ACTIVE_YEAR"] = year_text
        CONFIG["YEAR"] = year_text
        CONFIG["SRC_ROOT"] = cfg.get("SRC_ROOT", "")
        CONFIG["DEST_ROOT"] = cfg.get("DEST_ROOT", "")
        
        # Lưu cấu hình mới
        save_config(CONFIG)
        
        # Làm mới giao diện
        self.load_companies_from_src()
        self.view_db.load_data()
        self.update_dept_user_completers()

    def toggle_ui(self, enabled):
        self.search_box.setEnabled(enabled)
        self.company_list.setEnabled(enabled)
        self.btn_browse.setEnabled(enabled)
        if hasattr(self, 'combo_phong'):
            self.combo_phong.setEnabled(enabled)
        if hasattr(self, 'combo_user'):
            self.combo_user.setEnabled(enabled)
        if enabled:
            self.check_ready()
        else:
            self.btn_sync.setEnabled(False)
            self.btn_sync_all.setEnabled(False)
            self.btn_usb.setEnabled(False)
            self.btn_open_src.setEnabled(False)
            self.btn_open_dest.setEnabled(False)

    def get_delivery_status(self, company_name):
        if not company_name:
            return "Chưa Bàn Giao"
        mst = company_name.split("_")[0] if "_" in company_name else company_name
        
        active_year = CONFIG.get("ACTIVE_YEAR", "2024")
        year_cfg = CONFIG.get("YEAR_CONFIGS", {}).get(active_year, {})
        db_p_raw = year_cfg.get("DATABASE_PATH", "database")
        db_path = db_p_raw if os.path.isabs(db_p_raw) else os.path.normpath(os.path.join(APP_ROOT, db_p_raw))
        target_db = f"DANH SACH THE {active_year}.db"
        db_file = os.path.join(db_path, target_db)
        
        if not os.path.exists(db_file):
            return "Chưa Bàn Giao"
            
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute('PRAGMA table_info("database")')
            columns = [col[1] for col in cursor.fetchall()]
            
            mst_col = next((c for c in columns if "MST" in c.upper()), None)
            bg_col = next((c for c in columns if "BÀN GIAO" in c.upper() and "NGÀY" not in c.upper()), None)
            
            if mst_col and bg_col:
                cursor.execute(f'SELECT "{bg_col}" FROM "database" WHERE "{mst_col}" = ?', (mst,))
                row = cursor.fetchone()
                if row:
                    val = str(row[0]).strip()
                    if val in ["1", "1.0", "Đã Bàn Giao", "Đã bàn giao"]:
                        return "Đã Bàn Giao"
            conn.close()
        except Exception as e:
            print(f"Lỗi kiểm tra trạng thái bàn giao: {e}")
            
        return "Chưa Bàn Giao"

    def on_worker_done(self, task_name):
        self.progress_bar.setVisible(False)
        
        # Hiển thị trạng thái Bàn Giao nếu đồng bộ đơn vị hoàn tất
        if "Sync (đơn vị)" in task_name or "Dọn rác & Sync (đơn vị)" in task_name:
            status = self.get_delivery_status(self.selected_company)
            if status == "Đã Bàn Giao":
                self.log(f'<br><span style="font-size: 22px; color: #52c41a; font-weight: bold;">🟢 TRẠNG THÁI: ĐÃ BÀN GIAO</span><br>')
            else:
                self.log(f'<br><span style="font-size: 22px; color: #f5222d; font-weight: bold;">🔴 TRẠNG THÁI: CHƯA BÀN GIAO</span><br>')

        self.log(f"\n✅ HOÀN TẤT: {task_name}\n" + "="*50)
        QMessageBox.information(self, "Hoàn tất", f"Đã hoàn tất quá trình: {task_name}!")
        self.toggle_ui(True)

    # --- CÁC HÀM XỬ LÝ ---
    def run_sync(self):
        if not self.selected_company: return
        self.console.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.toggle_ui(False)

        self.log(f"🚀 BẮT ĐẦU QUÁ TRÌNH DỌN RÁC & ĐỒNG BỘ: {self.selected_company}\n" + "="*50)
        self.worker_clean = CleanerWorker([self.selected_company])
        self.worker_clean.log_sig.connect(self.log)
        
        def start_sync_after_clean():
            self.worker_sync = SyncWorker([self.selected_company])
            self.worker_sync.log_sig.connect(self.log)
            self.worker_sync.done_sig.connect(lambda: self.on_worker_done("Dọn rác & Sync (đơn vị)"))
            self.worker_sync.start()

        self.worker_clean.done_sig.connect(start_sync_after_clean)
        self.worker_clean.start()

    def run_sync_all(self):
        if not self.all_companies: return
        
        reply = QMessageBox.question(
            self, 
            "Xác nhận", 
            f"Bạn có chắc chắn muốn dọn rác và đồng bộ TOÀN BỘ {len(self.all_companies)} đơn vị không?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.console.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.toggle_ui(False)

        self.log(f"🚀 BẮT ĐẦU DỌN RÁC TOÀN BỘ ({len(self.all_companies)} đơn vị)\n" + "="*50)
        self.worker_clean_all = CleanerWorker(self.all_companies)
        self.worker_clean_all.log_sig.connect(self.log)

        def start_sync_all_after_clean():
            self.worker_sync_all = SyncWorker(self.all_companies)
            self.worker_sync_all.log_sig.connect(self.log)
            self.worker_sync_all.done_sig.connect(lambda: self.on_worker_done("Dọn rác & Sync All (tất cả)"))
            self.worker_sync_all.start()

        self.worker_clean_all.done_sig.connect(start_sync_all_after_clean)
        self.worker_clean_all.start()

    def run_copy_usb(self):
        if not self.selected_company or not self.selected_usb: return
        
        # Bắt buộc phải chọn hoặc nhập Phòng và User
        phong_val = self.combo_phong.currentText().strip() if hasattr(self, 'combo_phong') else ""
        user_val = self.combo_user.currentText().strip() if hasattr(self, 'combo_user') else ""
        
        if not phong_val or not user_val:
            QMessageBox.warning(self, "Bắt buộc chọn Phòng và User", "Vui lòng chọn hoặc nhập đầy đủ thông tin 'Phòng' và 'User' trước khi sao chép USB!")
            return

        msg = f"CẢNH BÁO ĐỎ: Toàn bộ dữ liệu trên USB ({self.selected_usb}) sẽ bị FORAMT (XÓA SẠCH) trước khi chép!\n\nBạn có HIỂU RÕ nguy hiểm và CHẮC CHẮN muốn chạy chức năng này không?"
        reply = QMessageBox.warning(self, "Xác nhận Format USB", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.console.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.toggle_ui(False)

        self.log(f"🚀 BẮT ĐẦU COPY DỮ LIỆU USB CHO: {self.selected_company}\n" + "="*50)
        self.worker_copy = CopyUSBWorker(self.selected_company, self.selected_usb)
        self.worker_copy.log_sig.connect(self.log)
        self.worker_copy.progress_sig.connect(self.update_progress)
        
        # Kết nối sự kiện hoàn tất
        def on_copy_finished():
            self.on_worker_done("Copy ra USB")
            # Tự động đánh dấu trong Tab Data
            mtc_val = self.mtc_input.text().strip()
            marked = False
            if mtc_val:
                marked = self.view_db.assign_company_and_mark_delivered(mtc_val, self.selected_company, phong=phong_val, user=user_val)
            if not marked:
                self.view_db.mark_as_delivered(self.selected_company, phong=phong_val, user=user_val)
            self.update_dept_user_completers()

        self.worker_copy.done_sig.connect(on_copy_finished)
        self.worker_copy.start()

    def update_progress(self, cur, total):
        if total > 0:
            self.progress_bar.setValue(int(cur * 100 / total))
            self.progress_bar.setFormat(f"Đang xử lý... %p% ({cur}/{total})")

    def open_source_folder(self):
        if not self.selected_company: return
        src_root = os.path.join(CONFIG["SRC_ROOT"], self.selected_company, CONFIG["YEAR"])
        if os.path.exists(src_root):
            os.startfile(src_root)
        else:
            QMessageBox.warning(self, "Lỗi", f"Không tìm thấy thư mục nguồn:\n{src_root}")

    def open_dest_folder(self):
        if not self.selected_company: return
        dest_root = os.path.join(CONFIG["DEST_ROOT"], f"{self.selected_company}_{CONFIG['YEAR']}")
        if os.path.exists(dest_root):
            os.startfile(dest_root)
        else:
            QMessageBox.warning(self, "Lỗi", f"Không tìm thấy thư mục đích:\n{dest_root}")

import traceback

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"CRITICAL ERROR:\n{err_msg}")
    try:
        crash_log_file = os.path.join(APP_ROOT, "crash.log")
        with open(crash_log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n{err_msg}\n")
    except Exception as e:
        print(f"Lỗi ghi crash.log: {e}")
    try:
        QMessageBox.critical(None, "Lỗi phần mềm", f"Đã xảy ra lỗi không mong muốn:\n\n{exc_value}\n\n(Chi tiết đã được lưu vào file crash.log)")
    except:
        pass

sys.excepthook = handle_exception

if __name__ == "__main__":
    print("DEBUG: Starting QApplication...")
    app = QApplication(sys.argv)
    try:
        print("DEBUG: Initializing MainApp...")
        window = MainApp()
        print("DEBUG: Showing Window...")
        window.show()
        print("DEBUG: Entering Event Loop...")
        sys.exit(app.exec())
    except Exception as e:
        print(f"DEBUG: CRASH in main: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")