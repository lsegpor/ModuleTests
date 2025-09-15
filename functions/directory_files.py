import time
import sys
import os
import logging
sys.path.append('../../autogen/agwb/python/')
from smx_tester import *
import re
import threading

class DirectoryFiles:
    
    def __init__(self, vd=None):
        self.vd = vd
        self.log = logging.getLogger()
        self.file_locks = {}
        
    def _acquire_file_lock(self, file_path):
        # Simple mutex-based locking
        if file_path not in self.file_locks:
            self.file_locks[file_path] = threading.Lock()
        self.file_locks[file_path].acquire()
    
    def _release_file_lock(self, file_path):
        if file_path in self.file_locks:
            self.file_locks[file_path].release()

    # Module testing directory & files
    def read_moduleId(self, module):
        #module_sn = "M5UR3B2011342B2"
        module_sn = module
        match = re.match(r"M([0-8][DU])([LR][0-8])(T[0-4]|B[0-4])(0[01])(\d{3})([0-4])(A2|B2)", module_sn)
        
        if match:
            if match.group(3)[1] == match.group(6):
                ladder_sn = f"L{match.group(1)}{match.group(2)}{match.group(4)}{match.group(5)}"
            else:
                ladder_sn = "NOT_MATCHING"
        else:
            ladder_sn = "UNKNOWN"

        return module_sn, ladder_sn

    def check_moduleId(self, module_str, s_size, s_qgrade):
        module_id = ""
        sensor_size = ""
        sensor_qgrade = ""
        if (len(module_str) == 0):
            print("MODULE NAME should not be left empty")
            sys.exit()
        else:
            module_id = module_str
            if (module_id[-2:-1] == 'A' or module_id[-2:-1] == 'B'):
                sensor_size = s_size
                sensor_qgrade = s_qgrade
                return (module_id, sensor_size, sensor_qgrade)
            else:
                print("MODULE ID must contain the FEB type (A/B) in the second-to-last position")
                return ['na']
            
    def read_test_center(self):
        #test_center = input("INTRODUCE THE TEST CENTER ([1 or GSI, 2 or KIT): ")
        test_center = "GSI"
        test_center_list = ['1', '2', 'GSI', 'KIT','gsi', 'kit']
        if (test_center in test_center_list):
            if (test_center =='1' or test_center == 'gsi'):
                test_center = 'GSI'
            if (test_center =='2' or test_center == 'kit'):
                test_center = 'KIT'
            return test_center
        else:
            log.error("TEST CENTER NAME is not included in the list")
            return 'na'

    def read_operator_id(self):
        #operator_id = input("Insert the Operator ID (example: Jane Doe): ")
        operator_id = "Dairon Rodriguez Garces"
        operator_id_list = []
        with open("operators_file.txt") as file:
            for line in file:
                operator_id_list.append(line.rstrip())
        file.close()
        
        if (operator_id in operator_id_list):
            return operator_id
        else:
            #add_to_list = input("OPERATOR'S ID is not found. Should be added to the list (Y/N):")
            add_to_list = "Y"
            if (add_to_list == 'Y' or 'y' or 'yes'):
                operator_id_file = open("operators_file.txt", "a")
                operator_id_file.write(operator_id)
            else:
                return 'na'

    def initWorkingDirectory(self, module_dir, module_sn):
        self._acquire_file_lock(module_dir)
        try:
            # Creating the directory of module testing 
            # importing the module name  
            # module_sn = "M" + module_sn
            # module_path = module_path
            # module_dir  = module_path + '/' + module_sn
            module_dir  = module_dir
            # other variables:                                   
            date  = time.strftime("%y%m%d-%H:%M:%S")
        # checking if directory exists                       
            if not os.path.isdir(module_dir):           
                try:
                    os.makedirs(module_dir)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
                    else:
                        print("Succesfully created Module directory %s:" + (module_dir))

            # creating log file                                  
            logfile = open(module_dir + "/" + module_sn + "_log.log","a")
            
            # checking if data file exists                       
            if (os.path.isfile(module_dir + "/" + module_sn + "_data.dat") == True):
                print("Data file already exists. Would you like to re-write it (Y/N):")
                #writing_flag = input()
                writing_flag = "N"
                if ( writing_flag == 'N' or writing_flag == 'No' or writing_flag == 'n' or writing_flag == 'no'):
                    module_sn = module_sn + "_" + time.strftime("%y%m%d_%H%M")       # changing file name with different date                                        
                    print("Data file will be created with the following name: %s" %(module_sn + "_data.dat"))
                else:
                    module_sn = module_sn
            else:
                module_sn = module_sn
                print("Data file does not exists & it will be created with the following name: %s"  %( module_sn + "_data.dat"))

            # creating data file and initializing it
            datafile = open(module_dir + "/" + module_sn + "_data.dat","w+")
            datafile.write("FILENAME_DATA: ")
            datafile.write(module_sn)
            datafile.write("\n")
            datafile.write("TEST_DATE: ")
            datafile.write(date)
            datafile.write("\n")
            datafile.close()

            # initializing log file                        
            logfile.write(date)
            logfile.write("\t")
            logfile.write("MODULE_ID:")
            logfile.write("\t")
            logfile.write(module_sn)
            logfile.write("\n")    
            logfile.close()

            return module_sn
        
        finally:
            self._release_file_lock(module_dir)

    def close_log_file(self, module_sn):
        # ending testing & closing data and log files
        logfile.write(date)
        logfile.write("\t")
        logfile.write("Ending test sequence")
        logfile.write("\n")
        logfile.close()
        datafile.close()                                                                    

    def write_data_file(self, module_dir, module_sn, info = "a"):
        file_path = f"{module_dir}/{module_sn}_data.dat"
        self._acquire_file_lock(file_path)
        try:
            with open(file_path, "a") as datafile:
                datafile.write(str(info))
                datafile.write("\n")
        finally:
            self._release_file_lock(file_path)

    def write_log_file(self, module_dir, module_sn = "M00", info = ""):
        file_path = f"{module_dir}/{module_sn}_log.log"
        self._acquire_file_lock(file_path)
        try:
            date = time.strftime("%y%m%d-%H:%M:%S")
            with open(file_path, "a") as logfile:
                logfile.write(date)
                logfile.write("\t")
                logfile.write("[INFO]")
                logfile.write("\t")
                logfile.write(str(info))
                logfile.write("\n")
        finally:
            self._release_file_lock(file_path)

    def making_pscan_dir(self, module_dir):
        # Creating the pscan_files directory
        # checking if directory exists
        print("Creating Pscan files directory")
        pscan_dir = module_dir + "/pscan_files/"
        
        self._acquire_file_lock(pscan_dir)
        try:
            if os.path.isdir(pscan_dir):
                print("This module directory already exists")
            else:
                # creating the module files directory             
                try:
                    os.makedirs(pscan_dir)
                    print(f"Successfully created directory: {pscan_dir}")
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
                    else:
                        print("Succesfully created directory: %s" + (pscan_dir))
                        
            return pscan_dir
        
        finally:
            self._release_file_lock(pscan_dir)

    def making_trim_dir(self, module_dir):
        # Creating the trim_files directory
        # checking if directory exists
        print("Creating Trim files directory")
        trim_dir = module_dir + "/trim_files/"
        
        self._acquire_file_lock(trim_dir)
        try:
            if os.path.isdir(trim_dir):
                print("This module directory already exists")
            else:
                # creating the module files directory             
                try:
                    os.makedirs(trim_dir)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
                    else:
                        print("Succesfully created directory: %s" + (trim_dir))
                        
            return trim_dir
        
        finally:
            self._release_file_lock(trim_dir)

    def making_conn_check_dir(self, module_dir):
        # Creating the connection_files directory                                                                                                                        
        # checking if directory exists                                                                                                                                                                  
        print("Creating Connection files directory")
        conn_check_dir = module_dir + "/conn_check_files/"
        
        self._acquire_file_lock(conn_check_dir)
        try:
            if (os.path.isdir(conn_check_dir) == True):
                print("This module directory already exists")
            else:
                # creating the module files directory                                                                                                                                                       
                try:
                    os.makedirs(conn_check_dir)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
                    else:
                        print("Succesfully created directory: %s" + (conn_check_dir))
                        
            return conn_check_dir
        
        finally:
            self._release_file_lock(conn_check_dir)
