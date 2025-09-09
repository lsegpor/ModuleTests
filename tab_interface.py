from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QComboBox, QFrame, QDialog,
                           QTextEdit, QProgressBar, QPushButton, QCheckBox, QGridLayout,
                           QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QGroupBox)
from PyQt5.QtCore import Qt, QThread, QSize
from PyQt5.QtGui import QPixmap, QFont
import sys
import os
sys.path.append('../autogen/agwb/python/')
sys.path.append('../smx_tester/')
from utils.test_worker import TestWorker
from smx_tester import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolBar
from matplotlib.figure import Figure
import datetime
from utils.console_window import ConsoleManager
from utils.module_scanner import ModuleScanner

class TabInterface(QWidget):
    
    def __init__(self, parent, main_logic, root, tab_num):
        super().__init__(parent)
        self.main = main_logic
        self.root = root
        self.tab_num = tab_num
        self.test_running = False
        self.test_thread = None
        self.nside_datasets = []
        self.pside_datasets = []
        self.markers = ["o", "^", "s", "*"]
        self.last_vddm_update_time = 0
        self.temp_colors = ["red", "yellow", "green", "blue"]
        self.default_save_path = "/home/cbm/cbmsoft/emu_test_module_arr/python/module_files/"
        
        if not hasattr(root, 'console_manager'):
            root.console_manager = ConsoleManager()
        self.console_manager = root.console_manager
    
        main_layout = QGridLayout(self)
        
        main_container = QGroupBox("STS Module Testing")
        main_container.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 25px;
                font-family: Helvetica;
                font-size: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: lavender;
            }
        """)
        container_layout = QVBoxLayout(main_container)
        
        top_widget = QWidget()
        top_widget.setStyleSheet("background-color: lavender; border: none;")
        top_layout = QGridLayout(top_widget)
        
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: lavender; border: none;")
        left_widget.setFixedWidth(300)
        left_layout = QVBoxLayout(left_widget)
        
        try:
            route_image = "/home/cbm/lsegura/emu_ladder/python/module_tests/assets/dinosaur_icon.png"
            pixmap = QPixmap(route_image)
            scaled_pixmap = pixmap.scaled(100, 70, Qt.KeepAspectRatio)
            logo_label = QLabel()
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setFixedSize(scaled_pixmap.width(), scaled_pixmap.height())
            
            container = QWidget()
            container.setFixedHeight(scaled_pixmap.height() + 10)
            container_logo = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 20)
            container_logo.addWidget(logo_label, 0, Qt.AlignCenter)
            
            left_layout.addWidget(container)
            left_layout.addSpacing(15)
        except Exception as e:
            print(f"Error loading the image: {e}")
            logo_label = QLabel("(No Image)")
            logo_label.setStyleSheet("color: red; font-size: 11pt;")
        
        form_group = QGroupBox("MODULE FEATURES")
        form_group.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 15px;
                font-family: Helvetica;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: lavender;
                margin-bottom: 10px;
            }
        """)

        form_layout = QGridLayout(form_group)
        
        emu_options = ["EMU_236", "EMU_213", "EMU_234", "EMU_238"]
        self.sensorsize_options = ["22 mm", "42 mm", "62 mm", "124 mm"]
        self.sensorqgrade_options = ["A (500V)", "B (350V)", "C (250V)", "D (200V)"]
        
        module_label = QLabel("Module ID:")
        module_label.setFont(QFont("Helvetica", 10))
        self.module_entry = QLineEdit()
        
        sensor_label = QLabel("SUID:")
        sensor_label.setFont(QFont("Helvetica", 10))
        self.sensor_entry = QLineEdit()
        
        sensorsize_label = QLabel("Sensor size:")
        sensorsize_label.setFont(QFont("Helvetica", 10))
        self.sensorsize_combobox = QComboBox()
        self.sensorsize_combobox.addItems(self.sensorsize_options)
        
        sensorqgrade_label = QLabel("Sensor Qgrade:")
        sensorqgrade_label.setFont(QFont("Helvetica", 10))
        self.sensorqgrade_combobox = QComboBox()
        self.sensorqgrade_combobox.addItems(self.sensorqgrade_options)
        
        febnside_label = QLabel("FEB N-Side ID:")
        febnside_label.setFont(QFont("Helvetica", 10))
        self.febnside_entry = QLineEdit()
        
        febpside_label = QLabel("FEB P-Side ID:")
        febpside_label.setFont(QFont("Helvetica", 10))
        self.febpside_entry = QLineEdit()
        
        hv_nside_label = QLabel("HV N-Side (uA):")
        hv_nside_label.setFont(QFont("Helvetica", 10))
        self.hv_nside_entry = QLineEdit()
        
        hv_pside_label = QLabel("HV P-Side (uA):")
        hv_pside_label.setFont(QFont("Helvetica", 10))
        self.hv_pside_entry = QLineEdit()
        
        button_style = """
            QPushButton {
                background-color: #725d91;
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
            QPushButton:hover {
                background-color: #614f7d;
            }
            QPushButton:pressed {
                background-color: #4f4066;
            }
            QPushButton:disabled {
                background-color: #a486d1;
                color: #a0a0a0;
            }
        """
        
        scan_button = QPushButton("SCAN")
        scan_button.setStyleSheet(button_style)
        scan_button.setFont(QFont("Helvetica", 9))
        scan_button.setFixedWidth(250)
        scan_button.clicked.connect(self.open_module_scanner)
        
        row = 0
        for label, widget in [
            (module_label, self.module_entry),
            (sensor_label, self.sensor_entry),
            (sensorsize_label, self.sensorsize_combobox),
            (sensorqgrade_label, self.sensorqgrade_combobox),
            (febnside_label, self.febnside_entry),
            (febpside_label, self.febpside_entry),
            (hv_nside_label, self.hv_nside_entry),
            (hv_pside_label, self.hv_pside_entry),
        ]:
            form_layout.addWidget(label, row, 0, Qt.AlignLeft)
            form_layout.addWidget(widget, row, 1, Qt.AlignRight)
            
            widget.setStyleSheet("""
                background-color: white;
                border: 1px solid black;
                border-radius: 0px;
                padding: 2px;
                margin-top: 5px;
            """)
            
            widget.setFixedWidth(120)
            
            row += 1
            
        form_layout.addWidget(scan_button, row, 0, 1, 2, Qt.AlignCenter)
            
        emu_form = QGroupBox()
        emu_form.setFixedHeight(100)
        emu_form.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
            }
        """)
        emu_layout = QGridLayout(emu_form)
        
        emu_options = ["EMU_236", "EMU_238", "EMU_213", "EMU_234"]
        
        emu_label = QLabel("EMU ID:")
        emu_label.setFont(QFont("Helvetica", 10))
        self.emu_combobox = QComboBox()
        self.emu_combobox.addItems(emu_options)
        
        if hasattr(self, 'tab_num'):
            if self.tab_num == 0:
                self.emu_combobox.setCurrentIndex(1)
            elif self.tab_num == 1:
                self.emu_combobox.setCurrentIndex(2)
            elif self.tab_num == 2:
                self.emu_combobox.setCurrentIndex(3)
        
        emu_v_label = QLabel("EMU_V [V]:")
        emu_v_label.setFont(QFont("Helvetica", 10))
        self.emu_v_entry = QLineEdit()
        self.emu_v_entry.setReadOnly(True)
        
        emu_i_label = QLabel("EMU_I [A]:")
        emu_i_label.setFont(QFont("Helvetica", 10))
        self.emu_i_entry = QLineEdit()
        self.emu_i_entry.setReadOnly(True)
        
        row = 0
        for label, widget in [
            (emu_label, self.emu_combobox),
            (emu_v_label, self.emu_v_entry),
            (emu_i_label, self.emu_i_entry),
        ]:
            emu_layout.addWidget(label, row, 0, Qt.AlignLeft)
            emu_layout.addWidget(widget, row, 1, Qt.AlignRight)
            
            widget.setStyleSheet("""
                background-color: white;
                border: 1px solid black;
                border-radius: 0px;
                padding: 2px;
            """)
            
            widget.setFixedWidth(120)
            
            row += 1
        
        middle_widget = QWidget()
        middle_widget.setStyleSheet("background-color: lavender; border: none;")
        middle_layout = QGridLayout(middle_widget)
        
        left_layout.addWidget(form_group)
        left_layout.addWidget(emu_form)
        
        tests_group = QGroupBox("TEST_SEQUENCE")
        tests_group.setFixedHeight(180)
        tests_group.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                font-family: Helvetica;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: lavender;
            }
        """)
        tests_layout = QGridLayout(tests_group)
        
        test_names = ["Comm test", "Calib test", "Check test", "C-Check test", "Stress test"]
        self.checkbox_vars_tests = []
        
        for test_name in test_names:
            test_row = QWidget()
            test_row_layout = QHBoxLayout(test_row)
            test_row_layout.setContentsMargins(0, 0, 0, 0)
            
            checkbox = QCheckBox()
            checkbox.setStyleSheet("background-color: lavender; border: none")
            
            label = QLabel(test_name)
            label.setFont(QFont("Helvetica", 10))
            
            test_row_layout.addWidget(checkbox)
            test_row_layout.addStretch(1)
            test_row_layout.addWidget(label)
            
            tests_layout.addWidget(test_row)
            
            self.checkbox_vars_tests.append(checkbox)
        
        for i in range(1, len(self.checkbox_vars_tests)):
            self.checkbox_vars_tests[i].setEnabled(False)
            
        for checkbox in self.checkbox_vars_tests:
            checkbox.stateChanged.connect(self.update_checkboxes)
        
        left_layout.addWidget(tests_group)
        
        top_layout.addWidget(left_widget, 0, 0)
        top_layout.addWidget(middle_widget, 0, 1)
        
        label_directory = QLabel("Directory File:")
        label_directory.setFont(QFont("Helvetica", 11))
        self.entry_directory = QLineEdit()
        self.entry_directory.setStyleSheet("""
            background-color: white;
            padding: 3px;
            border: 1px solid black;
        """)
        
        select_button1 = QPushButton("Browse...")
        select_button1.setStyleSheet(button_style)
        select_button1.clicked.connect(self.select_directory)
        
        default_directory1 = os.path.expanduser("/home/cbm/cbmsoft/emu_test_module_arr/python/module_files/")
        self.entry_directory.setText(default_directory1)
        
        label_calibration = QLabel("Calibration Dir:")
        label_calibration.setFont(QFont("Helvetica", 11))
        self.entry_calibration = QLineEdit()
        self.entry_calibration.setStyleSheet("""
            background-color: white;
            padding: 3px;
            border: 1px solid black;
        """)
        select_button2 = QPushButton("Browse...")
        select_button2.setStyleSheet(button_style)
        select_button2.clicked.connect(self.select_calibration)
        
        default_directory2 = os.path.expanduser("calibration_path")
        self.entry_calibration.setText(default_directory2)
        
        middle_layout.addWidget(label_directory, 0, 0)
        middle_layout.addWidget(self.entry_directory, 0, 1)
        middle_layout.addWidget(select_button1, 0, 2)
        
        middle_layout.addWidget(label_calibration, 1, 0)
        middle_layout.addWidget(self.entry_calibration, 1, 1)
        middle_layout.addWidget(select_button2, 1, 2)
        
        asic_group = QGroupBox("SMX FOR TEST")
        asic_group.setFixedHeight(100)
        asic_group.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                font-family: Helvetica;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: lavender;
            }
        """)

        asic_layout = QGridLayout(asic_group)
        
        self.check_all_nside = QCheckBox()
        self.check_all_nside.setChecked(True)
        asic_layout.addWidget(self.check_all_nside, 0, 0)
        label_nside = QLabel("FEB N-Side:")
        label_nside.setFont(QFont("Helvetica", 11))
        asic_layout.addWidget(label_nside, 0, 1)
        
        checkbox_frame1 = QWidget()
        checkbox_frame1.setStyleSheet("background-color: lavender; border: none;")
        checkbox_layout1 = QHBoxLayout(checkbox_frame1)
        
        self.checkbox_vars1 = []
        for i in range(8):
            chk = QCheckBox(str(i))
            chk.setFont(QFont("Helvetica", 8))
            chk.setChecked(True)
            checkbox_layout1.addWidget(chk)
            self.checkbox_vars1.append(chk)
        
        asic_layout.addWidget(checkbox_frame1, 0, 2)
        
        self.check_all_nside.stateChanged.connect(self.toggle_all_nside)
        for chk in self.checkbox_vars1:
            chk.stateChanged.connect(self.update_check_all_nside)
        
        self.check_all_pside = QCheckBox()
        self.check_all_pside.setChecked(True)
        asic_layout.addWidget(self.check_all_pside, 1, 0)
        label_pside = QLabel("FEB P-Side:")
        label_pside.setFont(QFont("Helvetica", 11))
        asic_layout.addWidget(label_pside, 1, 1)
        
        checkbox_frame2 = QWidget()
        checkbox_frame2.setStyleSheet("background-color: lavender; border: none;")
        checkbox_layout2 = QHBoxLayout(checkbox_frame2)
        
        self.checkbox_vars2 = []
        for i in range(8):
            chk = QCheckBox(str(i))
            chk.setFont(QFont("Helvetica", 8))
            chk.setChecked(True)
            checkbox_layout2.addWidget(chk)
            self.checkbox_vars2.append(chk)
        
        asic_layout.addWidget(checkbox_frame2, 1, 2)
        
        self.check_all_pside.stateChanged.connect(self.toggle_all_pside)
        for chk in self.checkbox_vars2:
            chk.stateChanged.connect(self.update_check_all_pside)
        
        middle_layout.addWidget(asic_group, 2, 0, 1, 3)
        
        plot_group = QGroupBox("VDDM (mV)")
        plot_group.setFixedHeight(450)
        plot_group.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-bottom: 10px;
                font-family: Helvetica;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: lavender;
            }
        """)
        
        plot_layout = QGridLayout(plot_group)
        
        self.figure_nside = Figure(figsize=(4, 2), dpi=100)
        self.canvas_nside = FigureCanvas(self.figure_nside)
        self.canvas_nside.setFixedHeight(170)
        self.ax_nside = self.figure_nside.add_subplot(111)
        
        self.ax_nside.set_xlim(-0.5, 7.5)
        self.ax_nside.set_ylim(1000, 1400)
        self.ax_nside.set_xticks(range(8))
        self.ax_nside.set_xticklabels([str(i) for i in range(8)])
        self.ax_nside.set_title('N-side', fontsize=9)
        self.ax_nside.scatter([-1], [0], alpha=0)
        self.ax_nside.xaxis.label.set_fontsize(8)
        self.ax_nside.yaxis.label.set_fontsize(8)
        self.ax_nside.tick_params(axis='both', which='major', labelsize=7)
        self.ax_nside.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
        self.figure_nside.tight_layout()
        
        self.toolbar_nside = NavigationToolBar(self.canvas_nside, self, coordinates=False)
        self.toolbar_nside.setFixedHeight(20)
        self.toolbar_nside.setIconSize(QSize(15, 15))
        self.toolbar_nside.layout().setSpacing(1)
        self.toolbar_nside.setStyleSheet("""
            QToolBar {
                spacing: 10px;
                padding: 0px;
                background-color: lavender;
            }
            QToolButton {
                padding: 1px;
                margin-left: 9px;
                margin-right: 9px;
                background-color: white;
            }
        """)
        
        for action in self.toolbar_nside.actions():
            if action.text() == 'Save':
                action.triggered.disconnect()
                action.triggered.connect(lambda: self.save_figure_nside())
                break
        
        self.figure_pside = Figure(figsize=(4, 2), dpi=100)
        self.canvas_pside = FigureCanvas(self.figure_pside)
        self.canvas_pside.setFixedHeight(150)
        self.ax_pside = self.figure_pside.add_subplot(111)
        
        self.ax_pside.set_xlim(-0.5, 7.5)
        self.ax_pside.set_ylim(1000, 1400)
        self.ax_pside.set_xticks(range(8))
        self.ax_pside.set_xticklabels([str(i) for i in range(8)])
        self.ax_pside.set_title('P-side', fontsize=9)
        self.ax_pside.scatter([-1], [0], alpha=0)
        self.ax_pside.xaxis.label.set_fontsize(8)
        self.ax_pside.yaxis.label.set_fontsize(8) 
        self.ax_pside.tick_params(axis='both', which='major', labelsize=7)
        self.ax_pside.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
        self.figure_pside.tight_layout()
        
        self.toolbar_pside = NavigationToolBar(self.canvas_pside, self, coordinates=False)
        self.toolbar_pside.setFixedHeight(20)
        self.toolbar_pside.setIconSize(QSize(15, 15))
        self.toolbar_pside.layout().setSpacing(1)
        self.toolbar_pside.setStyleSheet("""
            QToolBar {
                spacing: 10px;
                padding: 0px;
                background-color: lavender;
            }
            QToolButton {
                padding: 1px;
                margin-left: 9px;
                margin-right: 9px;
                background-color: white;
            }
        """)
        
        for action in self.toolbar_pside.actions():
            if action.text() == 'Save':
                action.triggered.disconnect()
                action.triggered.connect(lambda: self.save_figure_pside())
                break
        
        plot_layout.addWidget(self.canvas_nside, 0, 0)
        plot_layout.addWidget(self.toolbar_nside, 1, 0, 1, 3)
        plot_layout.addWidget(self.canvas_pside, 2, 0)
        plot_layout.addWidget(self.toolbar_pside, 3, 0, 1, 3)
        
        middle_layout.addWidget(plot_group, 3, 0, 1, 3)
        
        text_group = QGroupBox("Comments")
        text_group.setFixedHeight(120)
        text_group.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                font-family: Helvetica;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: lavender;
            }
        """)
        
        text_layout = QGridLayout(text_group)
        text_layout.setSpacing(0)
        
        self.text_area = QTextEdit()
        self.text_area.setFont(QFont("Helvetica", 11))
        self.text_area.setFixedHeight(80)
        self.text_area.setStyleSheet("background-color: white;")
        
        text_layout.addWidget(self.text_area)
        
        middle_layout.addWidget(text_group, 4, 0, 1, 3)
        
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: lavender; border: none;")
        right_widget.setFixedWidth(400)
        right_layout = QGridLayout(right_widget)
        top_layout.addWidget(right_widget, 0, 2)
        
        temp_ref_group = QGroupBox("TEMP_REF")
        temp_ref_group.setFixedHeight(70)
        temp_ref_group.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                font-family: Helvetica;
                font-size: 14px;
                padding-top: 7px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: lavender;
            }
        """)

        temp_ref_layout = QGridLayout(temp_ref_group)

        colors = ["blue", "green", "yellow", "red"]
        ranges = ["<20°C", "20°C-40°C", "40°C-60°C", ">60°C"]

        column = 0

        for color in colors:
            color_frame = QFrame()
            color_frame.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
            temp_ref_layout.addWidget(color_frame, 0, column)
            column += 1


        column = 0

        for range_text in ranges:
            text_label = QLabel(range_text)
            text_label.setAlignment(Qt.AlignCenter)
            temp_ref_layout.addWidget(text_label, 1, column)
            column += 1

        right_layout.addWidget(temp_ref_group, 0, 0)
        
        feb_lv_group = QGroupBox("FEB_LV")
        feb_lv_group.setFixedHeight(220)
        feb_lv_group.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-top: 10px;
                font-family: Helvetica;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: lavender;
            }
        """)

        feb_lv_layout = QGridLayout(feb_lv_group)
        feb_lv_layout.setVerticalSpacing(10)
        feb_lv_layout.setHorizontalSpacing(15)
        
        sides = ["N-Side:", "P-Side:"]
        header_labels = ["LDO 1.2V", "LDO 1.8V"]
        self.nside_entries = []
        self.pside_entries = []
        self.lv_checkboxes = []
        self.lv_off_buttons = []
        self.lv_on_buttons = []
        
        for side_idx, side_name in enumerate(sides):
            for volt_idx, volt_name in enumerate(header_labels):
                voltage_group = QGroupBox(f"{side_name} {volt_name}")
                voltage_layout = QVBoxLayout(voltage_group)
                
                checkbox_layout = QHBoxLayout()
                checkbox = QCheckBox("ON")
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(self.update_checkbox_feb)
                
                lv_off_button = QPushButton("LV OFF")
                lv_off_button.setMaximumWidth(60)
                lv_off_button.setStyleSheet(button_style)
                
                lv_on_button = QPushButton("LV ON")
                lv_on_button.setMaximumWidth(60)
                lv_on_button.setStyleSheet(button_style)
                
                side_type = "N" if side_name == "N-Side:" else "P"
                volt_type = "1.2" if "1.2V" in volt_name else "1.8"
                
                lv_off_button.setProperty("side_type", side_type)
                lv_off_button.setProperty("volt_type", volt_type)
                lv_on_button.setProperty("side_type", side_type)
                lv_on_button.setProperty("volt_type", volt_type)
                
                lv_off_button.clicked.connect(self.lv_off_button_clicked)
                lv_on_button.clicked.connect(self.lv_on_button_clicked)
                
                checkbox_layout.addStretch()
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.addWidget(lv_off_button)
                checkbox_layout.addWidget(lv_on_button)
                checkbox_layout.addStretch()
                
                voltage_layout.addLayout(checkbox_layout)
                self.lv_checkboxes.append(checkbox)
                self.lv_off_buttons.append(lv_off_button)
                self.lv_on_buttons.append(lv_on_button)
                
                entry_layout = QHBoxLayout()
                
                voltage_entry = QLineEdit()
                voltage_entry.setMaximumWidth(70)
                voltage_entry.setAlignment(Qt.AlignCenter)
                voltage_entry.setReadOnly(True)
                voltage_entry.setStyleSheet("""
                    background-color: white;
                    border: 1px solid black;
                    border-radius: 0px;
                    padding: 2px;
                """)
                
                current_entry = QLineEdit()
                current_entry.setMaximumWidth(70)
                current_entry.setAlignment(Qt.AlignCenter)
                current_entry.setReadOnly(True)
                current_entry.setStyleSheet("""
                    background-color: white;
                    border: 1px solid black;
                    border-radius: 0px;
                    padding: 2px;
                """)
                
                entry_layout.addWidget(voltage_entry)
                entry_layout.addWidget(current_entry)
                
                voltage_layout.addLayout(entry_layout)
                
                feb_lv_layout.addWidget(voltage_group, side_idx, volt_idx)
                
                if side_name == "N-Side:":
                    if volt_name == "LDO 1.2V":
                        self.nside_entries.append(voltage_entry)
                        self.nside_entries.append(current_entry)
                        self.check_lv_nside_12 = checkbox
                    else:
                        self.nside_entries.append(voltage_entry)
                        self.nside_entries.append(current_entry)
                        self.check_lv_nside_18 = checkbox
                else:
                    if volt_name == "LDO 1.2V":
                        self.pside_entries.append(voltage_entry)
                        self.pside_entries.append(current_entry)
                        self.check_lv_pside_12 = checkbox
                    else:
                        self.pside_entries.append(voltage_entry)
                        self.pside_entries.append(current_entry)
                        self.check_lv_pside_18 = checkbox
        
        right_layout.addWidget(feb_lv_group, 1, 0)

        pscan_plot_group = QGroupBox("Pscan process results")
        pscan_plot_group.setFixedHeight(450)
        pscan_plot_group.setStyleSheet("""
            QGroupBox {
                background-color: lavender;
                border: 1px solid black;
                border-radius: 5px;
                margin-bottom: 10px;
                font-family: Helvetica;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: lavender;
            }
        """)
        
        pscan_plot_layout = QGridLayout(pscan_plot_group)
        
        self.figure_pscan = Figure(figsize=(3, 2), dpi=100)
        self.canvas_pscan = FigureCanvas(self.figure_nside)
        self.canvas_pscan.setFixedHeight(170)
        self.ax_pscan = self.figure_pscan.add_subplot(111)
        
        self.ax_pscan.set_xlim(-0.5, 7.5)
        self.ax_pscan.set_ylim(1000, 1400)
        self.ax_pscan.set_xticks(range(8))
        self.ax_pscan.set_xticklabels([str(i) for i in range(8)])
        self.ax_pscan.set_title('Pscan', fontsize=9)
        self.ax_pscan.scatter([-1], [0], alpha=0)
        self.ax_pscan.xaxis.label.set_fontsize(8)
        self.ax_pscan.yaxis.label.set_fontsize(8)
        self.ax_pscan.tick_params(axis='both', which='major', labelsize=7)
        self.ax_pscan.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
        self.figure_pscan.tight_layout()

        self.toolbar_pscan = NavigationToolBar(self.canvas_pscan, self, coordinates=False)
        self.toolbar_pscan.setFixedHeight(20)
        self.toolbar_pscan.setIconSize(QSize(15, 15))
        self.toolbar_pscan.layout().setSpacing(1)
        self.toolbar_pscan.setStyleSheet("""
            QToolBar {
                spacing: 10px;
                padding: 0px;
                background-color: lavender;
            }
            QToolButton {
                padding: 1px;
                margin-left: 9px;
                margin-right: 9px;
                background-color: white;
            }
        """)

        for action in self.toolbar_pscan.actions():
            if action.text() == 'Save':
                action.triggered.disconnect()
                action.triggered.connect(lambda: self.save_figure_pscan())
                break

        self.figure_pscan1 = Figure(figsize=(3, 2), dpi=100)
        self.canvas_pscan1 = FigureCanvas(self.figure_nside)
        self.canvas_pscan1.setFixedHeight(170)
        self.ax_pscan1 = self.figure_pscan1.add_subplot(111)
        
        self.ax_pscan1.set_xlim(-0.5, 7.5)
        self.ax_pscan1.set_ylim(1000, 1400)
        self.ax_pscan1.set_xticks(range(8))
        self.ax_pscan1.set_xticklabels([str(i) for i in range(8)])
        self.ax_pscan1.set_title('Pscan', fontsize=9)
        self.ax_pscan1.scatter([-1], [0], alpha=0)
        self.ax_pscan1.xaxis.label.set_fontsize(8)
        self.ax_pscan1.yaxis.label.set_fontsize(8)
        self.ax_pscan1.tick_params(axis='both', which='major', labelsize=7)
        self.ax_pscan1.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
        self.figure_pscan1.tight_layout()

        self.toolbar_pscan1 = NavigationToolBar(self.canvas_pscan1, self, coordinates=False)
        self.toolbar_pscan1.setFixedHeight(20)
        self.toolbar_pscan1.setIconSize(QSize(15, 15))
        self.toolbar_pscan1.layout().setSpacing(1)
        self.toolbar_pscan1.setStyleSheet("""
            QToolBar {
                spacing: 10px;
                padding: 0px;
                background-color: lavender;
            }
            QToolButton {
                padding: 1px;
                margin-left: 9px;
                margin-right: 9px;
                background-color: white;
            }
        """)

        for action in self.toolbar_pscan1.actions():
            if action.text() == 'Save':
                action.triggered.disconnect()
                action.triggered.connect(lambda: self.save_figure_pscan1())
                break

        self.figure_pscan2 = Figure(figsize=(3, 2), dpi=100)
        self.canvas_pscan2 = FigureCanvas(self.figure_nside)
        self.canvas_pscan2.setFixedHeight(170)
        self.ax_pscan2 = self.figure_pscan2.add_subplot(111)

        self.ax_pscan2.set_xlim(-0.5, 7.5)
        self.ax_pscan2.set_ylim(1000, 1400)
        self.ax_pscan2.set_xticks(range(8))
        self.ax_pscan2.set_xticklabels([str(i) for i in range(8)])
        self.ax_pscan2.set_title('Pscan', fontsize=9)
        self.ax_pscan2.scatter([-1], [0], alpha=0)
        self.ax_pscan2.xaxis.label.set_fontsize(8)
        self.ax_pscan2.yaxis.label.set_fontsize(8)
        self.ax_pscan2.tick_params(axis='both', which='major', labelsize=7)
        self.ax_pscan2.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
        self.figure_pscan2.tight_layout()

        self.toolbar_pscan2 = NavigationToolBar(self.canvas_pscan2, self, coordinates=False)
        self.toolbar_pscan2.setFixedHeight(20)
        self.toolbar_pscan2.setIconSize(QSize(15, 15))
        self.toolbar_pscan2.layout().setSpacing(1)
        self.toolbar_pscan2.setStyleSheet("""
            QToolBar {
                spacing: 10px;
                padding: 0px;
                background-color: lavender;
            }
            QToolButton {
                padding: 1px;
                margin-left: 9px;
                margin-right: 9px;
                background-color: white;
            }
        """)

        for action in self.toolbar_pscan2.actions():
            if action.text() == 'Save':
                action.triggered.disconnect()
                action.triggered.connect(lambda: self.save_figure_pscan2())
                break

        pscan_plot_layout.addWidget(self.canvas_pscan, 0, 0)
        pscan_plot_layout.addWidget(self.toolbar_pscan, 1, 0, 1, 3)
        pscan_plot_layout.addWidget(self.canvas_pscan1, 2, 0)
        pscan_plot_layout.addWidget(self.toolbar_pscan1, 3, 0, 1, 3)
        pscan_plot_layout.addWidget(self.canvas_pscan2, 4, 0)
        pscan_plot_layout.addWidget(self.toolbar_pscan2, 5, 0, 1, 3)

        right_layout.addWidget(pscan_plot_group, 2, 0, 1, 3)

        progress_widget = QWidget()
        progress_widget.setStyleSheet("background-color: lavender; border: none;")
        progress_layout = QVBoxLayout(progress_widget)
        
        self.info_label = QLabel("")
        self.info_label.setFont(QFont("Helvetica", 11))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: black;
                border: 1px solid black;
                border-radius: 5px;
                text-align: center;
                padding: 1px;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #725d91;
                border-radius: 4px;
            }
        """)
        
        progress_layout.addWidget(self.info_label)
        progress_layout.addWidget(self.progress_bar)
        
        container_layout.addWidget(top_widget)
        
        button_widget = QWidget()
        button_widget.setStyleSheet("background-color: lavender; border: none;")
        button_layout = QHBoxLayout(button_widget)
        
        self.run_button = QPushButton("RUN")
        self.run_button.setStyleSheet(button_style)
        self.run_button.setFont(QFont("Helvetica", 13))
        self.run_button.setFixedWidth(200)
        self.run_button.clicked.connect(self.run_tests)
        
        self.stop_button = QPushButton("STOP")
        self.stop_button.setStyleSheet(button_style)
        self.stop_button.setFont(QFont("Helvetica", 13))
        self.stop_button.setFixedWidth(200)
        self.stop_button.clicked.connect(self.stop_tests)
        self.stop_button.setEnabled(False)
        
        self.save_button = QPushButton("SAVE COMMENTS")
        self.save_button.setStyleSheet(button_style)
        self.save_button.setFont(QFont("Helvetica", 13))
        self.save_button.setFixedWidth(200)
        self.save_button.clicked.connect(self.save_observations)
        
        self.terminal_button = QPushButton("SHOW TERMINAL")
        self.terminal_button.setStyleSheet(button_style)
        self.terminal_button.setFont(QFont("Helvetica", 13))
        self.terminal_button.setFixedWidth(200)
        self.terminal_button.clicked.connect(self.show_console)
        
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.terminal_button)
        
        main_layout.addWidget(main_container, 0, 0)
        main_layout.addWidget(progress_widget, 1, 0)
        main_layout.addWidget(button_widget, 2, 0)
        
    def open_module_scanner(self):
        try:
            scanner = ModuleScanner()
            
            result = scanner.exec_()
            
            print(f"Scanner result: {result}")
            print(f"QDialog.Accepted = {QDialog.Accepted}")
                    
            if result == QDialog.Accepted:
                self.process_scanner_data(scanner)
            elif result == QDialog.Rejected:
                print("User cancelled scanner")
            else:
                print(f"Unexpected result: {result}")
                
        except Exception as e:
            print(f"Error opening scanner: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Error opening scanner:\n{str(e)}")
            
    def determine_feb_suffix(self, feb_sn, feb_type, module_id):
        try:
            if not feb_sn or feb_sn == '' or not module_id or module_id == '':
                return feb_sn
            
            clean_sn = feb_sn.strip()
            
            if len(clean_sn) > 4 and clean_sn[-1] in ['A', 'B']:
                clean_sn = clean_sn[:-1]
            
            if not (clean_sn.isdigit() and len(clean_sn) == 4):
                print(f"FEB number invalid: {clean_sn}")
                return feb_sn
            
            module_clean = module_id.strip()
            if len(module_clean) < 2:
                print(f"Module ID too short: {module_clean}")
                return feb_sn
            
            penultimate_char = module_clean[-2].upper()
            print(f"Module ID: {module_clean}, penultimate character: {penultimate_char}")
            
            last_digit = module_clean[-1]
            print(f"Module ID: {module_clean}, last digit: {last_digit}")
            
            if penultimate_char == 'A':
                if feb_type == 'A':
                    suffix = 'A'
                elif feb_type == 'B':
                    suffix = 'B'
                else:
                    return feb_sn
                    
            elif penultimate_char == 'B':
                if feb_type == 'A':
                    suffix = 'A'
                elif feb_type == 'B':
                    suffix = 'B'
                else:
                    return feb_sn
            else:
                return feb_sn
            
            result = f"{clean_sn}{suffix}{last_digit}"
            return result
            
        except Exception as e:
            return feb_sn

    def process_scanner_data(self, scanner):
        try:
            updated_fields = []
            
            # 1. MODULE ID
            if scanner.module and scanner.module not in ['Unknown', '']:
                self.module_entry.setText(scanner.module)
                updated_fields.append(f"Module ID: {scanner.module}")
            
            # 2. SENSOR ID (SUID)
            if scanner.sensor and scanner.sensor not in ['Unknown', '']:
                self.sensor_entry.setText(scanner.sensor)
                updated_fields.append(f"Sensor ID: {scanner.sensor}")
            
            # 3. SENSOR SIZE
            if scanner.size and scanner.size not in ['Unknown', '', None]:
                size_mapping = {
                    '62x22': '22 mm',
                    '62x42': '42 mm', 
                    '62x62': '62 mm',
                    '62x124': '124 mm',
                    # Alternative formats
                    '22': '22 mm',
                    '42': '42 mm',
                    '62': '62 mm', 
                    '124': '124 mm'
                }
                
                mapped_size = size_mapping.get(scanner.size)
                if mapped_size:
                    index = self.sensorsize_combobox.findText(mapped_size)
                    if index >= 0:
                        self.sensorsize_combobox.setCurrentIndex(index)
                        updated_fields.append(f"Sensor Size: {mapped_size}")
                    else:
                        print(f"Size not found: {mapped_size}")
                else:
                    print(f"Size not recognized: {scanner.size}")
            
            # 4. SENSOR QGRADE
            if scanner.grade and scanner.grade not in ['Unknown', '', None]:
                grade_mapping = {
                    'A': 'A (500V)',
                    'B': 'B (350V)',
                    'C': 'C (250V)',
                    'D': 'D (200V)'
                }
                
                mapped_grade = grade_mapping.get(scanner.grade.upper())
                if mapped_grade:
                    index = self.sensorqgrade_combobox.findText(mapped_grade)
                    if index >= 0:
                        self.sensorqgrade_combobox.setCurrentIndex(index)
                        updated_fields.append(f"Sensor Quality Grade: {mapped_grade}")
                    else:
                        print(f"Quality grade not found: {mapped_grade}")
                else:
                    print(f"Quality grade not recognized: {scanner.grade}")
            
            # 5. FEB N-SIDE ID
            if hasattr(scanner, 'feb_a_sn') and scanner.feb_a_sn and scanner.feb_a_sn != '':
                feb_a_with_suffix = self.determine_feb_suffix(scanner.feb_a_sn, 'A', scanner.module)
                
                # Determinar si es módulo tipo A o B
                module_clean = scanner.module.strip()
                if len(module_clean) >= 2:
                    penultimate_char = module_clean[-2].upper()
                    if penultimate_char == 'A':
                        # Módulo tipo A: FEB A va a P-Side
                        self.febpside_entry.setText(feb_a_with_suffix)
                        updated_fields.append(f"FEB P-Side: {feb_a_with_suffix}")
                    else:
                        # Módulo tipo B: FEB A va a N-Side
                        self.febnside_entry.setText(feb_a_with_suffix)
                        updated_fields.append(f"FEB N-Side: {feb_a_with_suffix}")
            
            # 6. FEB P-SIDE ID
            if hasattr(scanner, 'feb_b_sn') and scanner.feb_b_sn and scanner.feb_b_sn != '':
                feb_b_with_suffix = self.determine_feb_suffix(scanner.feb_b_sn, 'B', scanner.module)
                
                # Determinar si es módulo tipo A o B
                module_clean = scanner.module.strip()
                if len(module_clean) >= 2:
                    penultimate_char = module_clean[-2].upper()
                    if penultimate_char == 'A':
                        # Módulo tipo A: FEB B va a N-Side
                        self.febnside_entry.setText(feb_b_with_suffix)
                        updated_fields.append(f"FEB N-Side: {feb_b_with_suffix}")
                    else:
                        # Módulo tipo B: FEB B va a P-Side
                        self.febpside_entry.setText(feb_b_with_suffix)
                        updated_fields.append(f"FEB P-Side: {feb_b_with_suffix}")
            
        except Exception as e:
            print(f"Error procesing scanner data: {e}")
            import traceback
            traceback.print_exc()
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Error processing scanner data:\n{str(e)}")
        
    def lv_off_button_clicked(self):
        button = self.sender()
        
        if self.test_running:
            QMessageBox.warning(self, "Test in execution", 
                            "Wait for the test to finish before turning lv off.")
            return
        
        side_type = button.property("side_type")
        volt_type = button.property("volt_type")
        
        emu_channel = self.emu_combobox.currentText()
        
        try:
            if hasattr(self, 'main') and self.main:
                self.main.set_lv_off(side_type, volt_type, emu_channel)
                self.update_test_label(f"--> Turning off LV for {side_type}-Side {volt_type}V (EMU: {emu_channel})")
                QMessageBox.information(self, "LV OFF", 
                                    f"LV turned off correctly for {side_type}-Side {volt_type}V (EMU: {emu_channel})")
            else:
                QMessageBox.warning(self, "Error", "Principal logic not avaliable.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error turning off LV: {str(e)}")
            
    def lv_on_button_clicked(self):
        button = self.sender()
        
        if self.test_running:
            QMessageBox.warning(self, "Test in execution", 
                            "Wait for the test to finish before turning lv on.")
            return
        
        side_type = button.property("side_type")
        volt_type = button.property("volt_type")
        
        emu_channel = self.emu_combobox.currentText()
        
        try:
            if hasattr(self, 'main') and self.main:
                self.update_test_label(f"--> Turning on LV for {side_type}-Side {volt_type}V (EMU: {emu_channel})")
                
                lv_values = self.main.set_read_lv_on(side_type, volt_type, emu_channel)
                
                if lv_values is not None:
                    if side_type == 'N':
                        if volt_type == '1.2':
                            self.nside_entries[0].setText(f"{lv_values[0]:.2f}V")
                            self.nside_entries[1].setText(f"{lv_values[1]:.2f}A")
                            success = lv_values[0] > 0
                        else:
                            self.nside_entries[2].setText(f"{lv_values[0]:.2f}V")
                            self.nside_entries[3].setText(f"{lv_values[1]:.2f}A")
                            success = lv_values[0] > 0
                    else:
                        if volt_type == '1.2':
                            self.pside_entries[0].setText(f"{lv_values[0]:.2f}V")
                            self.pside_entries[1].setText(f"{lv_values[1]:.2f}A")
                            success = lv_values[0] > 0
                        else:
                            self.pside_entries[2].setText(f"{lv_values[0]:.2f}V")
                            self.pside_entries[3].setText(f"{lv_values[1]:.2f}A")
                            success = lv_values[0] > 0
                    
                    if success:
                        QMessageBox.information(self, "LV ON", 
                                    f"LV turned on correctly for {side_type}-Side {volt_type}V (EMU: {emu_channel})")
                    else:
                        QMessageBox.warning(self, "LV ON", 
                                    f"LV may not have turned on correctly for {side_type}-Side {volt_type}V (EMU: {emu_channel}). Please check readings.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to read LV values after turning on.")
            else:
                QMessageBox.warning(self, "Error", "Principal logic not available.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error turning on LV: {str(e)}")
            import traceback
            traceback.print_exc()
        
    def save_figure(self):
        if not hasattr(self, 'active_canvas') or not self.active_canvas:
            print("No active canvas to save.")
            return
            
        canvas = self.active_canvas
        current_datetime = datetime.datetime.now().strftime("%y%m%d_%H%M")
        
        title = canvas.figure.axes[0].get_title()
        
        if "N-side" in title:
            side = "N"
        elif "P-side" in title:
            side = "P"
        else:
            side = "unknown"
        
        module_text = ""
        if hasattr(self, 'module_entry') and self.module_entry:
            module_text = self.module_entry.text()
        
        default_filename = f"{module_text}_VDDM_{side}_{current_datetime}.png"
        
        if not hasattr(self, 'default_save_path') or not self.default_save_path:
            self.default_save_path = os.path.expanduser("~/cbmsoft/emu_test_module_arr/python/module_files/")
        
        os.makedirs(self.default_save_path, exist_ok=True)
        
        start_path = os.path.join(self.default_save_path, default_filename)
        
        print(f"Trying to save in: {start_path}")
        
        filters = "PNG (*.png);;All Files (*)"
        
        fname, _ = QFileDialog.getSaveFileName(
            self.parent(), 
            "Save figure", 
            start_path,
            filters)
            
        if fname:
            if not fname.lower().endswith('.png'):
                fname = fname + '.png'
            
            try:
                canvas.figure.savefig(fname)
                self.default_save_path = os.path.dirname(fname)
                print(f"Figure saved in: {fname}")
            except Exception as e:
                print(f"Error saving figure: {e}")
        else:
            print("Saving canceled by user.")
            
    def save_figure_nside(self):
        self.active_canvas = self.canvas_nside
        self.save_figure()

    def save_figure_pside(self):
        self.active_canvas = self.canvas_pside
        self.save_figure()

    def uplinks_length_warning(self, length):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Uplinks list length warning")
        msg.setText(f"The uplinks are not 16.")
        
        warning_text = f"Not enough or too much uplinks, length: {length}\n\n"
        warning_text += "\nPlease check in the data cables:\n"
        warning_text += "• Connection\n"
        warning_text += "• Conditions\n"
        warning_text += "• Status\n"
        warning_text += "Tests will continue, but this may cause issues.\n"
        warning_text += "Consider investigating further."
        
        msg.setInformativeText(warning_text)
        
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.ApplicationModal)
        msg.exec_()
        
    def uplinks_length_warning(self, length):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Uplinks list length warning")
        msg.setText(f"The uplinks are not 16.")
        
        warning_text = f"Not enough or too much uplinks, length: {length}\n\n"
        warning_text += "\nPlease check in the data cables:\n"
        warning_text += "• Connection\n"
        warning_text += "• Conditions\n"
        warning_text += "• Status\n"
        warning_text += "Tests will continue, but this may cause issues.\n"
        warning_text += "Consider investigating further."
        
        msg.setInformativeText(warning_text)
        
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.ApplicationModal)
        msg.exec_()
        
    def show_efuse_duplicate_warning(self, duplicate_str_details, duplicate_int_details, pol_str, feb_type):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("EFUSE ID Duplicate Warning")
        msg.setText(f"Duplicate EFUSE IDs Detected on {pol_str}")
        
        warning_text = f"Duplicate EFUSE IDs found on {feb_type} {pol_str}:\n\n"
        
        if duplicate_str_details:
            warning_text += "STRING ID DUPLICATES:\n"
            for dup in duplicate_str_details:
                warning_text += f"• ID '{dup['efuse_id']}' found on {dup['count']} ASICs (HW: {', '.join(dup['hw_addresses'])})\n"
            warning_text += "\n"
        
        if duplicate_int_details:
            warning_text += "INTEGER ID DUPLICATES:\n"
            for dup in duplicate_int_details:
                warning_text += f"• ID {dup['efuse_id']} found on {dup['count']} ASICs (HW: {', '.join(dup['hw_addresses'])})\n"
        
        warning_text += "\nThis may indicate:\n"
        warning_text += "• Manufacturing defect in ASIC EFUSE programming\n"
        warning_text += "• Incorrect ASIC installation\n"
        warning_text += "• Communication errors during ID reading\n"
        warning_text += "• Hardware malfunction\n\n"
        warning_text += "Tests will continue, but duplicated ASICs may cause issues.\n"
        warning_text += "Consider replacing affected ASICs or investigating further."
        
        msg.setInformativeText(warning_text)
        
        detailed_text = "DETAILED DUPLICATE ANALYSIS:\n\n"
        
        if duplicate_str_details:
            detailed_text += "STRING ID DUPLICATES:\n"
            for dup in duplicate_str_details:
                detailed_text += f"EFUSE String ID: {dup['efuse_id']}\n"
                detailed_text += f"Duplicate count: {dup['count']}\n"
                detailed_text += "ASICs affected:\n"
                for asic in dup['asics']:
                    detailed_text += f"  - {asic['feb_type']} {asic['polarity']} HW:{asic['hw_addr']} (INT:{asic['efuse_int']})\n"
                detailed_text += "\n"
        
        if duplicate_int_details:
            detailed_text += "INTEGER ID DUPLICATES:\n"
            for dup in duplicate_int_details:
                detailed_text += f"EFUSE Integer ID: {dup['efuse_id']}\n"
                detailed_text += f"Duplicate count: {dup['count']}\n"
                detailed_text += "ASICs affected:\n"
                for asic in dup['asics']:
                    detailed_text += f"  - {asic['feb_type']} {asic['polarity']} HW:{asic['hw_addr']} (STR:{asic['efuse_str']})\n"
                detailed_text += "\n"
        
        detailed_text += "RECOMMENDATIONS:\n"
        detailed_text += "1. Verify ASIC physical installation\n"
        detailed_text += "2. Re-read EFUSE IDs to confirm duplicates\n"
        detailed_text += "3. Check for communication issues\n"
        detailed_text += "4. Consider ASIC replacement if duplicates persist\n"
        detailed_text += "5. Document findings for quality control"
        
        msg.setDetailedText(detailed_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.ApplicationModal)
        msg.exec_()
        
    def show_lv_warning(self, side, warnings, warningType):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("LV Current Warning")
        warning_text = ""
        
        if warningType == "low":
            msg.setText(f"Low Current Detected on {side}")
        
            warning_text += "The following currents are below the expected threshold (0.8A):\n\n"
        elif warningType == "high":
            msg.setText(f"High Current Detected on {side}")
        
            warning_text += "The following currents are above the expected threshold (3.0A):\n\n"
            
        for warning in warnings:
            warning_text += f"• {warning}\n"
        
        warning_text += "\nThis may indicate:\n"
        warning_text += "• Connection issues\n"
        warning_text += "• Module malfunction\n"
        warning_text += "• Incorrect configuration\n\n"
        warning_text += "Please verify connections and module status."
        
        msg.setDetailedText(warning_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        
        msg.setWindowModality(Qt.ApplicationModal)
        msg.exec_()
        
    def stop_tests(self):
        self.stop_button.setText("STOPPING...")
        self.stop_button.setEnabled(False)
        self.run_button.setEnabled(True)
        self.run_button.setText("RUN")
        self.test_running = False
        
        if hasattr(self, "worker") and self.worker:
            self.worker.request_stop()
            
        QMessageBox.information(self, f"Stopping Test in Tab {self.tab_num}", "Tests is being stopped. The process might continue for a brief moment.")
        
    def show_lv_critical_error(self, side, errors):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("CRITICAL LV ERROR")
        msg.setText(f"CRITICAL: Unsafe Current Levels on {side}")
        
        detailed_text = "The following currents are below the expected threshold (1.5A):\n\n"
        
        for error in errors:
            detailed_text += f"• {error}\n"
        
        detailed_text += "SAFETY MEASURES:\n"
        detailed_text += "• Tests have been automatically stopped\n"
        detailed_text += "• Module may be damaged or disconnected\n"
        detailed_text += "• Check all connections before restarting\n"
        detailed_text += "• Contact technical support if problem persists\n\n"
        detailed_text += "DO NOT RESTART TESTS until the issue is resolved."
        
        msg.setDetailedText(detailed_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.ApplicationModal)
        
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #ffebee;
            }
            QMessageBox QLabel {
                color: #c62828;
                font-weight: bold;
            }
        """)
        
        self.stop_tests()
        msg.exec_()
        
    def update_feb_nside(self, v12_value, i12_value, v18_value, i18_value, test_step=""):
        if v12_value != -1.0:
            self.nside_entries[0].setText(str(v12_value) + "V")
        if i12_value != -1.0:
            self.nside_entries[1].setText(str(i12_value) + "A")
        if v18_value != -1.0:
            self.nside_entries[2].setText(str(v18_value) + "V")
        if i18_value != -1.0:
            self.nside_entries[3].setText(str(i18_value) + "A")
            
        if test_step == "read_lv_bc":
            warnings = []
            
            if i12_value != -1.0 and i12_value < 0.8:
                warnings.append(f"N-side 1.2V current is {i12_value:.3f}A (< 0.8A)")
            
            if i18_value != -1.0 and i18_value < 0.8:
                warnings.append(f"N-side 1.8V current is {i18_value:.3f}A (< 0.8A)")
            
            if warnings:
                self.show_lv_warning("N-side", warnings, "low")
                
        if test_step == "read_lv_ac":
            warnings = []
            errors = []
            
            if i12_value != -1.0 and i12_value > 3.0:
                warnings.append(f"N-Side 1.2V current is {i12_value:.3f}A (> 3.0V)")
                
            if i18_value != -1.0 and i18_value > 2.5:
                warnings.append(f"N-Side 1.8V current is {i18_value:.3f}A (> 2.5V)")
                
            if warnings:
                self.show_lv_warning("N-Side", warnings, "high")
                
            if i12_value != -1.0 and i12_value < 1.5:
                errors.append(f"N-Side 1.2V current is {i12_value:.3f}A (< 1.5A)")
                
            if i18_value != -1.0 and i18_value < 1.5:
                errors.append(f"N-Side 1.8V current is {i18_value:.3f}A (< 1.5A)")
                
            if errors:
                self.show_lv_critical_error("N-Side", errors)
        
    def update_feb_pside(self, v12_value, i12_value, v18_value, i18_value, test_step=""):
        if v12_value != -1.0:
            self.pside_entries[0].setText(str(v12_value) + "V")
        if i12_value != -1.0:
            self.pside_entries[1].setText(str(i12_value) + "A")
        if v18_value != -1.0:
            self.pside_entries[2].setText(str(v18_value) + "V")
        if i18_value != -1.0:
            self.pside_entries[3].setText(str(i18_value) + "A")
            
        if test_step == "read_lv_bc":
            warnings = []
            
            if i12_value != -1.0 and i12_value < 0.8:
                warnings.append(f"P-side 1.2V current is {i12_value:.3f}A (< 0.8A)")
            
            if i18_value != -1.0 and i18_value < 0.8:
                warnings.append(f"P-side 1.8V current is {i18_value:.3f}A (< 0.8A)")
            
            if warnings:
                self.show_lv_warning("P-side", warnings, "low")
                
        if test_step == "read_lv_ac":
            warnings = []
            errors = []
            
            if i12_value != -1.0 and i12_value > 3.0:
                warnings.append(f"P-Side 1.2V current is {i12_value:.3f}A (> 3.0V)")
                
            if i18_value != -1.0 and i18_value > 2.5:
                warnings.append(f"P-Side 1.8V current is {i18_value:.3f}A (> 2.5V)")
                
            if warnings:
                self.show_lv_warning("P-Side", warnings, "high")
                
            if i12_value != -1.0 and i12_value < 1.5:
                errors.append(f"P-Side 1.2V current is {i12_value:.3f}A (< 1.5A)")
                
            if i18_value != -1.0 and i18_value < 1.5:
                errors.append(f"P-Side 1.8V current is {i18_value:.3f}A (< 1.5A)")
                
            if errors:
                self.show_lv_critical_error("P-Side", errors)
        
    def update_checkbox_feb(self):
        if self.check_lv_nside_12.isChecked():
            self.check_lv_nside_12.setText("ON")
        else:
            self.check_lv_nside_12.setText("OFF")
            
        if self.check_lv_nside_18.isChecked():
            self.check_lv_nside_18.setText("ON")
        else:
            self.check_lv_nside_18.setText("OFF")
        
        if self.check_lv_pside_12.isChecked():
            self.check_lv_pside_12.setText("ON")
        else:
            self.check_lv_pside_12.setText("OFF")
            
        if self.check_lv_pside_18.isChecked():
            self.check_lv_pside_18.setText("ON")
        else:
            self.check_lv_pside_18.setText("OFF")
            
    def clear_checkbox_colors(self):
        for checkbox in self.checkbox_vars1:
            checkbox.setStyleSheet("")
         
        for checkbox in self.checkbox_vars2:
            checkbox.setStyleSheet("")
    
    def update_temp_checkboxes(self, nside_index, nside_values, pside_index, pside_values, nside_measured_addresses=None, pside_measured_addresses=None):
        temp_values = { "N": nside_values if nside_values is not None else [],
                       "P": pside_values if pside_values is not None else [] }
        
        # N-side
        if nside_index and temp_values["N"] and nside_measured_addresses:
            for measurement_idx, temp in enumerate(temp_values["N"]):
                if measurement_idx < len(nside_measured_addresses):
                    asic_address = nside_measured_addresses[measurement_idx]
                    
                    if asic_address < len(self.checkbox_vars1):
                        checkbox = self.checkbox_vars1[asic_address]
                        
                        if temp >= 60:
                            color_index = 0
                        elif temp < 60 and temp >= 40:
                            color_index = 1
                        elif temp > 20 and temp < 40:
                            color_index = 2
                        else:
                            color_index = 3
                        
                        checkbox.setStyleSheet(f"background-color: {self.temp_colors[color_index]}; border-radius: 3px;")
                        
        # P-side
        if pside_index and temp_values["P"] and pside_measured_addresses:
            for measurement_idx, temp in enumerate(temp_values["P"]):
                if measurement_idx < len(pside_measured_addresses):
                    asic_address = pside_measured_addresses[measurement_idx]
                    
                    if asic_address < len(self.checkbox_vars2):
                        checkbox = self.checkbox_vars2[asic_address]
                        
                        if temp > 60:
                            color_index = 0
                        elif temp >= 20:
                            color_index = 1
                        else:
                            color_index = 2
                        
                        checkbox.setStyleSheet(f"background-color: {self.temp_colors[color_index]}; border-radius: 3px;")
                    
    def validate_vddm_values(self, vddm_values):
        critical_values = {"N": [], "P": []}
        warning_values = {"N": [], "P": []}
        has_critical = False
        has_warning = False
        
        if vddm_values.get("N"):
            for i, value in enumerate(vddm_values["N"]):
                if value < 1000:
                    critical_values["N"].append({"index": i, "value": value})
                    has_critical = True
                elif value > 1350:
                    warning_values["N"].append({"index": i, "value": value})
                    has_warning = True
        
        if vddm_values.get("P"):
            for i, value in enumerate(vddm_values["P"]):
                if value < 1000:
                    critical_values["P"].append({"index": i, "value": value})
                    has_critical = True
                elif value > 1350:
                    warning_values["P"].append({"index": i, "value": value})
                    has_warning = True
        
        if has_critical:
            self.show_vddm_critical_error(critical_values)
            return "CRITICAL_ERROR"
        
        if has_warning:
            self.show_vddm_warning(warning_values)
            return "WARNING"
        
        return "OK"

    def show_vddm_warning(self, warning_values):
        warning_messages = []
        
        if warning_values["N"]:
            for item in warning_values["N"]:
                warning_messages.append(f"N-side ASIC {item['index']}: {item['value']}mV (> 1350mV)")
        
        if warning_values["P"]:
            for item in warning_values["P"]:
                warning_messages.append(f"P-side ASIC {item['index']}: {item['value']}mV (> 1350mV)")
        
        if not warning_messages:
            return
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("VDDM High Voltage Warning")
        msg.setText("High VDDM Voltages Detected")
        
        warning_text = "The following VDDM values are above the recommended threshold (1350mV):\n\n"
        for warning_msg in warning_messages:
            warning_text += f"• {warning_msg}\n"
        
        warning_text += "\nThis may indicate:\n"
        warning_text += "• Higher than expected power consumption\n"
        warning_text += "• Potential thermal issues\n"
        warning_text += "• ASIC configuration problems\n\n"
        warning_text += "Monitor the situation closely.\n"
        warning_text += "Tests will continue, but consider investigating if values persist."
        
        msg.setInformativeText(warning_text)
        
        detailed_text = "VDDM VOLTAGE GUIDELINES:\n"
        detailed_text += "• Normal range: 1000-1350mV\n"
        detailed_text += "• Warning threshold: > 1350mV\n"
        detailed_text += "• Critical threshold: < 1000mV\n\n"
        detailed_text += "RECOMMENDED ACTIONS:\n"
        detailed_text += "• Monitor temperature readings\n"
        detailed_text += "• Check ASIC configuration\n"
        detailed_text += "• Verify cooling system operation\n"
        detailed_text += "• Consider reducing operational parameters if needed"
        
        msg.setDetailedText(detailed_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.ApplicationModal)
        msg.exec_()

    def show_vddm_critical_error(self, critical_values):
        critical_messages = []
        
        if critical_values["N"]:
            for item in critical_values["N"]:
                critical_messages.append(f"N-side ASIC {item['index']}: {item['value']}mV (< 1000mV)")
        
        if critical_values["P"]:
            for item in critical_values["P"]:
                critical_messages.append(f"P-side ASIC {item['index']}: {item['value']}mV (< 1000mV)")
        
        if not critical_messages:
            return
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("CRITICAL VDDM ERROR - TESTS STOPPED")
        msg.setText("CRITICAL: VDDM Voltage Too Low")
        
        error_text = "DANGEROUS VDDM levels detected. Tests have been automatically stopped.\n\n"
        error_text += "Critical values (< 1000mV):\n"
        for critical_msg in critical_messages:
            error_text += f"• {critical_msg}\n"
        
        msg.setInformativeText(error_text)
        
        detailed_text = "SAFETY CRITICAL SITUATION:\n"
        detailed_text += "• VDDM voltage below safe operating threshold\n"
        detailed_text += "• ASICs may not function correctly\n"
        detailed_text += "• Risk of data corruption or hardware damage\n"
        detailed_text += "• Tests automatically stopped for protection\n\n"
        
        detailed_text += "IMMEDIATE ACTIONS REQUIRED:\n"
        detailed_text += "1. Check power supply connections\n"
        detailed_text += "2. Verify module seating and contacts\n"
        detailed_text += "3. Inspect for physical damage\n"
        detailed_text += "4. Check power supply voltage levels\n"
        detailed_text += "5. Contact technical support\n\n"
        
        detailed_text += "DO NOT restart tests until:\n"
        detailed_text += "• Root cause is identified and fixed\n"
        detailed_text += "• VDDM values return to normal range (1000-1350mV)\n"
        detailed_text += "• System integrity is verified"
        
        msg.setDetailedText(detailed_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        msg.setWindowModality(Qt.ApplicationModal)
        
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #ffebee;
            }
            QMessageBox QLabel {
                color: #c62828;
                font-weight: bold;
            }
        """)
        
        self.stop_tests()
        msg.exec_()
    
    def update_vddm_plot(self, nside_index, nside_values, pside_index, pside_values, nside_measured_addresses=None, pside_measured_addresses=None):
        vddm_values = { "N": nside_values if nside_values is not None else [],
                       "P": pside_values if pside_values is not None else [] }

        if vddm_values.get("N") and nside_measured_addresses:
            self.nside_datasets.append((nside_measured_addresses, vddm_values.get("N", [])))
        elif vddm_values.get("N") and nside_index:
            self.nside_datasets.append((nside_index, vddm_values.get("N", [])))
        
        if vddm_values.get("P") and pside_measured_addresses:
            self.pside_datasets.append((pside_measured_addresses, vddm_values.get("P", [])))
        elif vddm_values.get("P") and pside_index:
            self.pside_datasets.append((pside_index, vddm_values.get("P", [])))
        
        self.update_nside_plot()
        self.update_pside_plot()
        
        validation_result = self.validate_vddm_values(vddm_values)
        
        if validation_result == "CRITICAL_ERROR":
            pass
        
    def update_nside_plot(self):
        self.ax_nside.clear()
        
        min_value = float('inf')
        max_value = float('-inf')
        
        for _, values in self.nside_datasets:
            if values and len(values) > 0:
                min_value = min(min_value, min(values))
                max_value = max(max_value, max(values))
        
        if min_value == float('inf') or max_value == float('-inf'):
            min_value, max_value = 1000, 1400
        else:
            range_value = max_value - min_value
            margin = range_value * 0.5
            min_value = min_value - margin
            max_value = max_value + margin
        
        self.ax_nside.set_ylim(min_value, max_value)
        
        self.ax_nside.xaxis.label.set_fontsize(8)
        self.ax_nside.yaxis.label.set_fontsize(8)
        self.ax_nside.title.set_fontsize(9)
        self.ax_nside.tick_params(axis='both', which='major', labelsize=7)
        
        self.ax_nside.set_xlim(-0.5, 7.5)
        self.ax_nside.set_xticks(range(8))
        self.ax_nside.set_xticklabels([str(i) for i in range(8)])
        
        for i, (index, values) in enumerate(self.nside_datasets):
            if index and values and len(index) == len(values):
                marker_idx = i % len(self.markers)
                
                sorted_points = sorted(zip(index, values))
                sorted_x, sorted_y = zip(*sorted_points) if sorted_points else ([], [])
                
                self.ax_nside.plot(sorted_x, sorted_y, 'r-', linewidth=1.5, alpha=0.6)
                self.ax_nside.scatter(index, values, facecolor='none', edgecolor='red',
                                    marker=self.markers[marker_idx], s=40, alpha=0.7,
                                    label=f'Measure {i+1}')
        
        if len(self.nside_datasets) > 1:
            self.ax_nside.legend(fontsize=7, loc='best')
        
        self.ax_nside.set_title('N-side', fontsize=9)
        self.ax_nside.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
        self.figure_nside.tight_layout()
        self.canvas_nside.draw()

    def update_pside_plot(self):
        self.ax_pside.clear()
        
        min_value = float('inf')
        max_value = float('-inf')
        
        for _, values in self.pside_datasets:
            if values and len(values) > 0:
                min_value = min(min_value, min(values))
                max_value = max(max_value, max(values))
        
        if min_value == float('inf') or max_value == float('-inf'):
            min_value, max_value = 1000, 1400
        else:
            range_value = max_value - min_value
            margin = range_value * 0.5
            min_value = min_value - margin
            max_value = max_value + margin
        
        self.ax_pside.set_ylim(min_value, max_value)
        
        self.ax_pside.xaxis.label.set_fontsize(8)
        self.ax_pside.yaxis.label.set_fontsize(8)
        self.ax_pside.title.set_fontsize(9)
        self.ax_pside.tick_params(axis='both', which='major', labelsize=7)
        
        self.ax_pside.set_xlim(-0.5, 7.5)
        self.ax_pside.set_xticks(range(8))
        self.ax_pside.set_xticklabels([str(i) for i in range(8)])
        
        for i, (index, values) in enumerate(self.pside_datasets):
            if index and values and len(index) == len(values):
                marker_idx = i % len(self.markers)
                
                sorted_points = sorted(zip(index, values))
                sorted_x, sorted_y = zip(*sorted_points) if sorted_points else ([], [])
                
                self.ax_pside.plot(sorted_x, sorted_y, 'b-', linewidth=1.5, alpha=0.6)
                self.ax_pside.scatter(index, values, facecolor='none', edgecolor='blue',
                                    marker=self.markers[marker_idx], s=40, alpha=0.7,
                                    label=f'Measure {i+1}')
        
        if len(self.pside_datasets) > 1:
            self.ax_pside.legend(fontsize=7, loc='best')
        
        self.ax_pside.set_title('P-side', fontsize=9)
        self.ax_pside.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
        self.figure_pside.tight_layout()
        self.canvas_pside.draw()
    
    def update_checkboxes(self):
        if self.checkbox_vars_tests[0].isChecked():
            self.checkbox_vars_tests[1].setEnabled(True)
            self.checkbox_vars_tests[2].setEnabled(True)
            self.checkbox_vars_tests[3].setEnabled(True)
            self.checkbox_vars_tests[4].setEnabled(True)
        else:
            for i in range(1, len(self.checkbox_vars_tests)):
                self.checkbox_vars_tests[i].setEnabled(False)
                self.checkbox_vars_tests[i].setChecked(False)
                
    def toggle_all_nside(self, state):
        for chk in self.checkbox_vars1:
            chk.blockSignals(True)
        
        for chk in self.checkbox_vars1:
            chk.setChecked(state == Qt.Checked)
            
        for chk in self.checkbox_vars1:
            chk.blockSignals(False)
            
    def toggle_all_pside(self, state):
        for chk in self.checkbox_vars2:
            chk.blockSignals(True)
        
        for chk in self.checkbox_vars2:
            chk.setChecked(state == Qt.Checked)
            
        for chk in self.checkbox_vars2:
            chk.blockSignals(False)
            
    def update_check_all_nside(self):
        self.check_all_nside.blockSignals(True)
        all_checked = all(chk.isChecked() for chk in self.checkbox_vars1)
        self.check_all_nside.setChecked(all_checked)
        self.check_all_nside.blockSignals(False)
        
    def update_check_all_pside(self):
        self.check_all_pside.blockSignals(True)
        all_checked = all(chk.isChecked() for chk in self.checkbox_vars2)
        self.check_all_pside.setChecked(all_checked)
        self.check_all_pside.blockSignals(False)
    
    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.entry_directory.text())
        if directory:
            self.entry_directory.setText(directory)
            
    def select_calibration(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Calibration Directory", self.entry_calibration.text())
        if directory:
            self.entry_calibration.setText(directory)
            
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
    def update_test_label(self, text):
        self.info_label.setText(text)
        
    def update_emu_values(self, v_value, i_value):
        self.emu_v_entry.setText(str(v_value))
        self.emu_i_entry.setText(str(i_value))
        
    def update_calib_path(self, text):
        self.entry_calibration.setText(text)
        
    def update_save_path(self, text):
        self.default_save_path += text
        
    def show_console(self):
        self.console_manager.show_console(self.tab_num, self)
    
    def log_to_console(self, message, level="INFO"):
        self.console_manager.add_log(self.tab_num, message, level)
        
    def handle_log_message(self, message, level):
        self.console_manager.add_log(self.tab_num, message, level)
        
    def run_tests(self):
        self.nside_datasets = []
        self.pside_datasets = []
        self.update_nside_plot()
        self.update_pside_plot()
        
        if self.test_running:
            QMessageBox.information(self, "Already Running", f"Test is already running on Tab {self.tab_num}.")
            return
        
        self.run_button.setEnabled(False)
        self.run_button.setText("RUNNING...")
        self.stop_button.setEnabled(True)
        self.test_running = True
        self.progress_bar.setValue(0)
        
        module_text = self.module_entry.text()
        if len(module_text.split()) == 4:
            parts = module_text.split()
            module = parts[1]
            s_size = parts[2]
            s_qgrade = parts[3]
            
            for option in self.sensorsize_options:
                if option.startswith(s_size) or s_size in option:
                    s_size = option
                    break
                
            for option in self.sensorqgrade_options:
                if option.startswith(s_qgrade) or s_qgrade in option:
                    s_qgrade = option
                    break
            
            self.module_entry.setText(module)
            
            self.sensorsize_combobox.setCurrentText(s_size)
            self.sensorqgrade_combobox.setCurrentText(s_qgrade)
        else:
            module = module_text
            s_size = self.sensorsize_combobox.currentText()
            s_qgrade = self.sensorqgrade_combobox.currentText()
        
        emu = self.emu_combobox.currentText()
        test_values = [1 if checkbox.isChecked() else 0 for checkbox in self.checkbox_vars_tests]
        asic_nside_values = [1 if checkbox.isChecked() else 0 for checkbox in self.checkbox_vars1]
        asic_pside_values = [1 if checkbox.isChecked() else 0 for checkbox in self.checkbox_vars2]
        feb_nside = self.febnside_entry.text() #if self.febnside_entry.text() else "0124A2"
        feb_pside = self.febpside_entry.text() #if self.febnside_entry.text() else "0124B2"
        suid = self.sensor_entry.text() #if self.sensor_entry.text() else "1234A"
        lv_nside_12_checked = 1 if self.check_lv_nside_12.isChecked() else 0
        lv_pside_12_checked = 1 if self.check_lv_pside_12.isChecked() else 0
        lv_nside_18_checked = 1 if self.check_lv_nside_18.isChecked() else 0
        lv_pside_18_checked = 1 if self.check_lv_pside_18.isChecked() else 0
        hv_nside = self.hv_nside_entry.text() if self.hv_nside_entry.text() else 0
        hv_pside = self.hv_pside_entry.text() if self.hv_pside_entry.text() else 0
        module_files = self.entry_directory.text()
        calib_path = self.entry_calibration.text()
        
        params = (
            module, feb_nside, feb_pside, hv_nside, hv_pside, emu, test_values, s_size, s_qgrade,
            asic_nside_values, asic_pside_values, suid, lv_nside_12_checked, lv_pside_12_checked,
            lv_nside_18_checked, lv_pside_18_checked, module_files, calib_path
        )
        
        self.thread = QThread()
        self.worker = TestWorker(self.main, params, self.tab_num)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.progressSignal.connect(self.update_progress)
        self.worker.infoSignal.connect(self.update_test_label)
        self.worker.logSignal.connect(self.handle_log_message)
        self.worker.emuSignal.connect(self.update_emu_values)
        self.worker.vddmSignal.connect(self.update_vddm_plot)
        self.worker.tempSignal.connect(self.update_temp_checkboxes)
        self.worker.clearSignal.connect(self.clear_checkbox_colors)
        self.worker.efuseidWarningSignal.connect(self.show_efuse_duplicate_warning)
        self.worker.uplinksWarningSignal.connect(self.uplinks_length_warning)
        self.worker.febnsideSignal.connect(self.update_feb_nside)
        self.worker.febpsideSignal.connect(self.update_feb_pside)
        self.worker.calibSignal.connect(self.update_calib_path)
        self.worker.savepathSignal.connect(self.update_save_path)
        self.worker.finishedSignal.connect(self.handle_test_completion)
        self.worker.finishedSignal.connect(self.thread.quit)
        
        self.thread.start()
    
    def handle_test_completion(self, success, error_message=None):
        self.test_running = False
        self.run_button.setEnabled(True)
        self.run_button.setText("RUN")
        self.stop_button.setEnabled(False)
        self.stop_button.setText("STOP")
        
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        
        if not success:
            if hasattr(self, "worker") and self.worker and self.worker.stop_requested:
                QMessageBox.information(self, f"Stopped Tab {self.tab_num}", "Tests stopped.")
            else:
                QMessageBox.critical(self, f"Error in Tab {self.tab_num}", f"Tests failed: {error_message}")
        else:
            QMessageBox.information(self, f"Result Tab {self.tab_num}", "Tests concluded.")
    
    def save_observations(self):
        try:
            observations = self.text_area.toPlainText()
            
            if not hasattr(self.main.vd, 'module_dir') or not self.main.vd.module_dir or \
               not hasattr(self.main.vd, 'module_sn_tmp') or not self.main.vd.module_sn_tmp:
                QMessageBox.critical(self, "Error", "Cannot save observations. Please run tests first to initialize the module.")
                return
                
            self.main.write_observations(observations)
            QMessageBox.information(self, "Result", "Observations saved.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to save observations: {str(e)}")
