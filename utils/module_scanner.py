#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__version__    = "3"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''  '''

import sys
import re

import requests
from bs4 import BeautifulSoup
import webbrowser

from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore    import QProcess, Qt
from PyQt5.QtGui     import QIntValidator

from loguru import logger

# parts of ST3
sys.path.append('gui')
import emu_ladder.python.module_tests.utils.gui_ModuleScanner as ModuleScanner

sys.path.append('lib')
import emu_ladder.python.module_tests.utils.feb_type_finder as feb_type_finder

class ModuleScanner(QDialog, ModuleScanner.Ui_ModuleScanner):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.feb_a_sn    : str = ''
        self.feb_a_type  : str = ''
        self.feb_a_uplink: str = ''
        self.feb_a_site  : str = ''

        self.feb_b_sn    : str = ''
        self.feb_b_type  : str = ''
        self.feb_b_uplink: str = ''
        self.feb_b_site  : str = ''

        self.sensor:  str = 'Unknown'
        self.size   : str = 'Unknown'
        self.grade  : str = 'Unknown'

        # L0DR300010 M0DR3T4000104B2 62 C
        self.ladder : str = 'Unknown'
        self.module : str = 'Unknown'

        self.url    : str = 'Unknown'

        ## FEB A
        ##
        self.pb_feb_a.setShortcut(Qt.Key_A)
        self.pb_feb_a.clicked.connect(    lambda: self.do_scan_feb("A") )
        self.le_feb_a.textEdited.connect( lambda: self.do_edit_feb("A") )
        self.le_feb_a.setValidator( QIntValidator(999, 7000) )

        ## FEB B
        ##
        self.pb_feb_b.setShortcut(Qt.Key_B)
        self.pb_feb_b.clicked.connect(    lambda: self.do_scan_feb("B") )
        self.le_feb_b.textEdited.connect( lambda: self.do_edit_feb("B") )
        self.le_feb_b.setValidator( QIntValidator(999, 7000) )

        ## Module QR
        ##
        self.pbScanQR.setShortcut(Qt.Key_1)
        self.pbScanQR.clicked.connect( self.do_scan_module_qr )
        self.leModuleName.textEdited.connect( self.do_edit_module_name )

        ## Sensor Bar
        ##
        onlyInt = QIntValidator()
        onlyInt.setRange(1022, 30394)
        self.leSensorName.setValidator(onlyInt)

        self.pbScanBAR.clicked.connect( self.do_scan_sensor_bar )
        self.pbScanBAR.setShortcut(Qt.Key_2)

        self.leSensorName .textEdited.connect( self.do_set_sensor )
        self.leSensorGrade.textEdited.connect( self.do_set_sensor )

        self.pbClear.clicked.connect( self.do_clear_all )
        self.pbClear.setShortcut(Qt.CTRL + Qt.Key_C)

        self.pbOpenLink.clicked.connect( self.open_in_browser )
        self.pbOpenLink.setShortcut(Qt.CTRL + Qt.Key_L)

        self.pbSave.clicked.connect( self.save_and_close )
        self.pbSave.setShortcut(Qt.Key_Return)

    #__________________________________________________________________________
    def do_scan_feb(self, feb_type):
        ''' run external FEB A scanner script'''
        process = QProcess(self)
        process.start('python3', ['module_tests/scripts/scan_feb_number.py'])
        process.waitForFinished()

        sn = process.readAllStandardOutput().data().decode()
        print(f"FEB number: {sn}")

        self.verify_feb(str(sn), feb_type)

    #__________________________________________________________________________
    def do_edit_feb(self, feb_type):

        if not len(self.le_feb_a.text()) and not len(self.le_feb_b.text()):
            return

        if feb_type == 'A':
            if not self.le_feb_a.text()[0] in ['1', '3', '5']:
                self.le_feb_a.setText('ERROR')
                logger.error("FEB number is not valid")
                return
            sn = self.le_feb_a.text()

        elif feb_type == 'B':
            if not self.le_feb_b.text()[0] in ['2', '4', '6']:
                self.le_feb_b.setText('ERROR')
                logger.error("FEB number is not valid")
                return
            sn = self.le_feb_b.text()
        
        self.verify_feb(str(sn), feb_type)
        # self.verify_feb(sn, feb_type)

    #__________________________________________________________________________
    def verify_feb(self, sn, feb_type):
        ''' run external FEB A scanner script'''

        try:
            ab, uplink, site = feb_type_finder.get_feb_type(sn)
        except Exception as e:
            # logger.error(f"Error reading FEB number: {e}")
            return

        if ab != feb_type:
            logger.error(f"FEB type is {ab}")
            if feb_type == 'A':
                self.le_feb_a.clear()
            elif feb_type == 'B':
                self.le_feb_b.clear()
            return

        elif ab == 'A':
            self.feb_a_sn     = str(sn)
            self.feb_a_type   = ab
            self.feb_a_uplink = uplink
            self.feb_a_site   = site
            self.le_feb_a.setText(self.feb_a_sn) # QLineEdit
            self.lb_feb_a_uplink.setText(uplink) # QLabel
            self.lb_feb_a_site.setText(site)

        elif ab == 'B':
            self.feb_b_sn     = str(sn)
            self.feb_b_type   = ab
            self.feb_b_uplink = uplink
            self.feb_b_site   = site
            self.le_feb_b.setText(self.feb_b_sn)
            self.lb_feb_b_uplink.setText(uplink)
            self.lb_feb_b_site.setText(site)

    #__________________________________________________________________________
    def do_scan_module_qr(self):
        ''' run external QR scanner script'''
        process = QProcess(self)
        process.start('python3', ['module_tests/scripts/scan_module_qrcode.py'])
        process.waitForFinished()

        QR_string = process.readAllStandardOutput().data().decode()

        if QR_string[0:44] == 'http://web-docs.gsi.de/~dtl-sts/?m=MODULE&n=' or \
           QR_string[0:44] == 'http://web-docs.gsi.de/~dtl-sts/?m=module&n=' :
            self.read_module_data_from_db( QR_string )
        else:
            self.do_parse_string( QR_string )

        self.update_status()

    #__________________________________________________________________________
    def do_parse_string(self, QR_string):
        ''' parse string from QR reader script'''

        # logger.debug( QR_string , len(QR_string))

        # !!! add checking old or new pattern is set by checking match
        #
        if len(QR_string) in  [32, 33]: # 2 digit and 3 digit sensor size 62, 124
            # L0DR300010 M0DR3T4000104B2 62 C
            # self.leModuleName.setText(QR_string)
            pattern = r'L(\w+)\s+M(\w+)\s+(\d+)\s+(\w+)'
            match   = re.match(pattern, QR_string)
            lader, module, size, grade = match.groups()
            # self.ladder = 'L'+lader
            self.module = 'M'+module
            # self.size   = int(size)
            # self.grade  = grade
            # self.update_status()

            self.url = f'http://web-docs.gsi.de/~dtl-sts/?m=MODULE&n={self.module}'
            self.read_module_data_from_db(self.url)
    #__________________________________________________________________________
    def do_edit_module_name(self):
        ''' run external QR scanner script'''
        text  = self.leModuleName.text()
        logger.debug( text )

        if len( text ) > 14:
            self.module = text
            logger.info(f"New Module Name: {self.module}")
        self.update_status()

    #__________________________________________________________________________
    def do_scan_sensor_bar(self):
        ''' run external QR scanner script'''
        process = QProcess(self)
        process.start('python3', ['module_tests/scripts/scan_sensor_barcode.py'])
        process.waitForFinished()

        self.sensor = process.readAllStandardOutput().data().decode()
        self.leSensorName.setText(self.sensor)
        self.update_status()
    
    #__________________________________________________________________________
    def do_set_sensor(self):
        ''' run external QR scanner script'''
        sensor_name = str( self.leSensorName.text()  )
        self.grade  = str( self.leSensorGrade.text() )
        
        if len( sensor_name ) == 5:
            self.sensor = sensor_name
            logger.info(f"New Sensor ID: {self.sensor}")

            if self.sensor[4] in ['0', '1']:
                self.size = '62x22'
            elif self.sensor[4] in ['2']:
                self.size = '62x42'
            elif self.sensor[4] in ['3']:
                self.size = '62x62'
            elif self.sensor[4] in ['4']:
                self.size = '62x124'
            self.update_status()

    # ====================================================================================================
    def read_module_data_from_db(self, url='http://web-docs.gsi.de/~dtl-sts/?m=MODULE&n=M3DL1T2001122A2'):
        
        # Send an HTTP request to the specified URL and save the response from server in a response object called r
        self.url = url.strip()
        r = requests.get(self.url)

        # Parse the response content as HTML
        soup = BeautifulSoup(r.content, 'html.parser')

        # Find all div elements on the page
        divs = soup.find_all('div')

        # Example: Extracting a specific property
        for div in divs:

            class_name = div.get('class')
            # print(f"Div class: {class_name}")

            if class_name == ['module-data']:
                # for attribute, value in div.attrs.items():
                #     print(f"  {attribute}: {value}")  # Attributes and their values
                
                mydiv = div.attrs.items()
                # print(mydiv)

                # <div class='module-data' 
                #     sensor='05032' 
                #     ladder='L3DL100112' 
                #     module='M3DL1T2001122A2'
                #     size='62x42'
                #     grade='A'
                #     feb_a ='1210'
                #     feb_b ='2135'>
                # </div>

                # Convert the list of tuples into a dictionary
                attributes_dict = dict(mydiv)

                # Extract the value of the 'sensor' attribute
                self.module = attributes_dict.get('module')
                self.ladder = attributes_dict.get('ladder')
                
                self.sensor = attributes_dict.get('sensor')
                self.size   = attributes_dict.get('size')
                self.grade  = attributes_dict.get('grade')

                self.feb_a_sn = attributes_dict.get('feb_a')
                self.verify_feb(self.feb_a_sn, 'A')

                self.feb_b_sn = attributes_dict.get('feb_b')
                self.verify_feb(self.feb_b_sn, 'B')

                self.update_status()

                break

    #__________________________________________________________________________
    def update_status(self):
        '''Update values on window'''
        logger.debug(self.module )
        logger.debug(self.ladder )
        logger.debug(self.sensor )
        logger.debug(self.size   ) 
        logger.debug(self.grade  )

        self.le_feb_a.setText(        self.feb_a_sn )
        self.lb_feb_a_uplink.setText( self.feb_a_uplink)
        self.lb_feb_a_site.setText(   self.feb_a_site)

        self.le_feb_b.setText(        self.feb_b_sn )
        self.lb_feb_b_uplink.setText( self.feb_b_uplink)
        self.lb_feb_b_site.setText(   self.feb_b_site)

        self.leModuleName.setText( self.module)
        self.lbLadder    .setText( f'Ladder: {self.ladder}')

        self.leSensorName.setText( self.sensor )
        self.leSensorGrade.setText( self.grade  )
        self.lbSensor.setText( f'Sensor: {self.sensor} {self.size} {self.grade}')

    #==========================================================================
    def open_in_browser(self):
        '''Open link in browser'''
        if self.url == '':
            logger.error("Plese scan QR first")
        else:
            logger.debug(f'open url: {self.url}')
            webbrowser.get('firefox').open_new_tab(self.url)

    #__________________________________________________________________________
    def save_and_close(self):
        try:
            print("=== SAVING SCANNER DATA ===")
            
            print(f"Module: '{self.module}'")
            print(f"Sensor: '{self.sensor}'")
            print(f"Size: '{self.size}'")
            print(f"Grade: '{self.grade}'")
            print(f"FEB A: '{self.feb_a_sn}'")
            print(f"FEB B: '{self.feb_b_sn}'")
            
            has_module = self.module and self.module not in ['Unknown', '']
            has_sensor = self.sensor and self.sensor not in ['Unknown', '']
            has_feb_a = self.feb_a_sn and self.feb_a_sn != ''
            has_feb_b = self.feb_b_sn and self.feb_b_sn != ''
            
            if not (has_module or has_sensor or has_feb_a or has_feb_b):
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(self, "Data empty", 
                                        "Valid data not found.\nClose?",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            
            print("Closing scanned with saved data...")
            self.accept()
            
        except Exception as e:
            print(f"Error saving data: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Error saving:\n{str(e)}")
   
    #__________________________________________________________________________
    def do_clear_all(self):
        '''Update values on window'''
        self.feb_a_sn     = ''
        self.feb_a_type   = ''
        self.feb_a_uplink = ''
        self.feb_a_site   = ''

        self.feb_b_sn     = ''
        self.feb_b_type   = ''
        self.feb_b_uplink = ''
        self.feb_b_site   = ''

        self.sensor = 'Unknown'
        self.size   = 'Unknown'
        self.grade  = 'Unknown'

        self.module = 'Unknown'
        self.ladder = 'Unknown'
        self.url    = 'Unknown'
        
        self.leModuleName.clear()
        self.leSensorName.clear()
        self.leSensorGrade.clear()
        self.le_feb_a.clear()
        self.le_feb_b.clear()
        
        self.update_status()

    #__________________________________________________________________________
    def closeEvent(self, evnt):
        ''' closing after selecting one of the cables'''
        logger.info(self.module)
        logger.info(self.sensor)

################################################################################
if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = ModuleScanner()
    window.pbSave.setDisabled(1)
    window.show()
    sys.exit(app.exec_())
