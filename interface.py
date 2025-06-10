from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import sys
import multiprocessing
sys.path.append('../autogen/agwb/python/')
sys.path.append('../smx_tester/')
from functions.file_management import FileManagement as fm
from main import Main
from smx_tester import *
from tab_interface import TabInterface

class Interface(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.log = fm.set_logging_details()
        
        self.setWindowTitle("STS_Module Testing")
        self.setStyleSheet("background-color: lavender;")
        self.setFixedSize(1200, 1000)
        
        self.center_window()
        
        try:
            self.setWindowIcon(QIcon("/home/cbm/lsegura/emu_ladder/python/module_tests/dinosaur_icon.png"))
        except:
            print("Couldn't load icon")
        
        self.notebook = QTabWidget(self)
        self.setCentralWidget(self.notebook)
        
        self.tabs = []
        
        for tab_num in range(3):
            main_instance = Main()
            tab = TabInterface(None, main_instance, self, tab_num)
            self.notebook.addTab(tab, f"Setup {tab_num}")
            self.tabs.append(tab)
    
    def center_window(self):
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    
    interface = Interface()
    interface.show()
    
    sys.exit(app.exec_())
