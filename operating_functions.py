import sys
import logging
from datetime import datetime
sys.path.append('../../autogen/agwb/python/')
from smx_tester import *
from directory_files import DirectoryFiles
import multiprocessing
import time
import os
import traceback
from PyQt5.QtCore import QCoreApplication
import threading
import ctypes

class OperatingFunctions: 
    
    def __init__(self, vd):
        self.vd = vd
        self.df=DirectoryFiles(self.vd)

    log = logging.getLogger()

    def run_with_timeout_and_interrupt(self, method, args=(), kwargs={}, timeout=None, check_continue=None):
        finished = [False]
        result = [None]
        error = [None]
        stop_requested = [False]
        
        def run_method():
            try:
                result[0] = method(*args, **kwargs)
            except Exception as e:
                error[0] = (str(e), traceback.format_exc())
            finally:
                finished[0] = True
        
        thread = threading.Thread(target=run_method)
        thread.daemon = True
        thread.start()
        
        def check_stop_thread():
            while not finished[0] and not stop_requested[0]:
                time.sleep(0.1)
                
                if check_continue and not check_continue():
                    print(f"Stop requested by user")
                    stop_requested[0] = True
                    
                    try:
                        thread_id = thread.ident
                        if thread_id:
                            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                                ctypes.c_long(thread_id),
                                ctypes.py_object(SystemExit)
                            )
                            if res > 1:
                                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                                    ctypes.c_long(thread_id),
                                    ctypes.c_long(0)
                                )
                    except Exception as e:
                        print(f"Error interrupting thread: {str(e)}")
                    
                    break
        
        stop_thread = threading.Thread(target=check_stop_thread)
        stop_thread.daemon = True
        stop_thread.start()
        
        start_time = time.time()
        last_progress_time = start_time
        
        try:
            while thread.is_alive():
                current_time = time.time()
                if timeout and (current_time - start_time > timeout):
                    print(f"Timeout after {timeout} seconds, interrupting execution")
                    stop_requested[0] = True
                    time.sleep(1)
                    break
                
                if current_time - last_progress_time >= 5:
                    elapsed = current_time - start_time
                    print(f"Method still running after {elapsed:.1f} seconds...")
                    last_progress_time = current_time
                
                QCoreApplication.processEvents()
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt detected, attempting to stop gracefully")
            stop_requested[0] = True
        finally:
            if 'stop_thread' in locals() and stop_thread.is_alive():
                stop_thread.join(timeout=1.0)
        
        if finished[0]:
            if error[0] is not None:
                print(f"Error executing method: {error[0][0]}")
                print(error[0][1])
                return None
            return result[0]
        else:
            print("Method execution was interrupted")
            thread.join(timeout=2.0)
            return None
    
    def read_FebSN_Nside(module_sn = 'M00'):
        # Fucntion to read the FEB serial number
        feb_sn = input("--> INTRODUCE THE SERIAL NUMBER for the N-side FEB. (XXXType<A/B>NumberOfUplinks ex: 138A2): ")
        #feb_sn = "2099B2"
        if (feb_sn[-2:-1] == 'A' or feb_sn[-2:-1] == 'B'):
            if (feb_sn[-2:-1] != module_sn[-2:-1]):
                return feb_sn
            else:
                log.error("Please, check that the SN of the N-side FEB is the right one. It contradicts the module ID")
                return 'na'
        else:
            log.error("FEB ID must contain the FEB type (A/B) in the second-to-last position")
            return 'na'

    def read_FebSN_Pside(module_sn = 'M00'):
        # Fucntion to read the FEB serial number
        feb_sn = input("--> INTRODUCE THE SERIAL NUMBER for the P-side FEB. (XXXType<A/B>NumberOfUplinks ex: 138B2): ")
        #feb_sn = "1100A2"
        if (feb_sn[-2:-1] == 'A' or feb_sn[-2:-1] == 'B'):
            if (feb_sn[-2:-1] == module_sn[-2:-1]):
                return feb_sn
            else:
                log.error("Please, check the FEB_SN is the right one. It contradicts the module ID")
                return 'na'
        else:
            log.error("FEB ID must contain the FEB type (A/B) in the second-to-last position")
            return 'na'
     
    def read_asicIDs_FEB(self, smx_l_side, pol, feb_type):
        # Function to read the overall ASIC ID (FEB where ASIC belongs, polarity, HW address, ASIC e-fuse ID(string) and (int)) 
        info = ""
        feb_type_sw = []
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn, info)
        if (pol == 'N' or pol == '0'):
            pol_str = 'N-side'
            pol_calib = 0
            info = 'EFUSE_ID_N'
        else:
            pol_str = 'P-side'
            pol_calib = 1
            info = 'EFUSE_ID_P'
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        header_line  = "FEB-ID_\t\t_POLARITY_\t\t_HW-ADDR_\t\t_EFUSE-ID-(STR)_\t\t_EFUSE-ID-(INT)_"
        log.info(header_line)
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, header_line)

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)

        #smx_counter =0

        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                if (smx.address == asic_sw):
                    addr = smx.address
                    asic_id_int = smx.read_efuse()
                    asic_id_str = smx.read_efuse_str()
                    info  = "{} \t\t {} \t\t {} \t\t {} \t\t {}".format(feb_type, pol_str, addr, asic_id_str, asic_id_int)
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    log.info(info)
                else:
                    pass
        return 0

              
    def read_VDDM_TEMP_FEB(self, smx_l_side, pol, feb_type, check_continue=None):
        # Function to read the VDDM and TEMP of the ASICs
        info = ""
        feb_type_sw = []
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        
        if not hasattr(self.vd, "stored_vddm_values"):
            self.vd.stored_vddm_values = {"N": [], "P": []}
        
        if (pol == "N" or pol == "0"):
            pol_str = "N-side"
            info = "VDDM_TEMP_N"
            self.vd.stored_vddm_values["N"] = []
        else:
            pol_str = "P-side"
            info = "VDDM_TEMP_P"
            self.vd.stored_vddm_values["P"] = []
            
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        header_line  = "FEB-ID_\t\t_POLARITY_\t\t_HW-ADDR_\t_VDDM POTENTIAL [LSB] | [mV]_\t\t_TEMP [mV] | [C]_"    
        log.info(header_line)
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, header_line)

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)
            
        if check_continue and not check_continue():
            log.info("read_VDDM_TEMP_FEB aborted during initialization")
            return -1

        for asic_sw in feb_type_sw:
            if check_continue and not check_continue():
                log.info(f"read_VDDM_TEMP_FEB aborted at asic_sw={asic_sw}")
                return -1
                
            for smx in smx_l_side:
                if check_continue and not check_continue():
                    log.info(f"read_VDDM_TEMP_FEB aborted at asic_sw={asic_sw}, smx.address={smx.address}")
                    return -1
                    
                if (smx.address == asic_sw):
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        log.info(f"Running read_vddm with timeout and interrupt for ASIC {smx.address}")
                        asic_vddm = self.run_with_timeout_and_interrupt(
                            smx.read_vddm,
                            args=(),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if asic_vddm is None and check_continue and not check_continue():
                            log.info(f"read_vddm was interrupted for ASIC {smx.address}")
                            return -1
                        
                        if check_continue and not check_continue():
                            log.info(f"read_VDDM_TEMP_FEB aborted after read_vddm for ASIC {smx.address}")
                            return -1
                            
                        log.info(f"Running read_temp with timeout and interrupt for ASIC {smx.address}")
                        asic_temp = self.run_with_timeout_and_interrupt(
                            smx.read_temp,
                            args=(),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if asic_temp is None and check_continue and not check_continue():
                            log.info(f"read_temp was interrupted for ASIC {smx.address}")
                            return -1
                    else:
                        asic_vddm = smx.read_vddm()
                        asic_temp = smx.read_temp()
                    
                    if pol == "N" or pol == "0":
                        self.vd.stored_vddm_values["N"].append(asic_vddm[1])
                        self.vd.stored_temp_values["N"].append(asic_temp[1])
                    else:
                        self.vd.stored_vddm_values["P"].append(asic_vddm[1])
                        self.vd.stored_temp_values["P"].append(asic_temp[1])
                        
                    info = "{} \t\t {} \t\t {} \t\t\t {} \t {:.1f} \t\t\t {:.1f} \t {:.1f}".format(feb_type, pol_str, smx.address, asic_vddm[0], asic_vddm[1], asic_temp[0], asic_temp[1])
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    log.info(info)
                else:
                    pass
                
        log.info(f"VDDM VALUES AFTER {pol} READING:")
        log.info(f"Stored N-side values: {self.vd.stored_vddm_values['N']}")
        log.info(f"Stored P-side values: {self.vd.stored_vddm_values['P']}")
                
        return 0
    
    def load_STD_Config(self, smx_l_side, pol, feb_type, check_continue=None):
        # Function to write on each ASIC the default settings
        feb_type_sw = []
        if (pol == 'N' or pol == '0'):
            pol_str = 'N-side'
            pol_calib = 0 
        else:
            pol_str = 'P-side'
            pol_calib = 1

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)
            
        if check_continue and not check_continue():
            log.info("load_STD_Config aborted during initialization")
            return -1

        for asic_sw in feb_type_sw:
            if check_continue and not check_continue():
                log.info(f"load_STD_Config aborted at asic_sw={asic_sw}")
                return -1
                
            for smx in smx_l_side:
                if check_continue and not check_continue():
                    log.info(f"load_STD_Config aborted at asic_sw={asic_sw}, smx.address={smx.address}")
                    return -1
                    
                if (smx.address == asic_sw):
                    header_line  = "--> SETTING STANDARD CONFIGURATION for ASIC with HW address {} and polarity {}".format(smx.address,pol_str)
                    log.info(header_line)
                    
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        log.info(f"Running write_def_ana_reg with timeout and interrupt for ASIC {smx.address}")
                        result = self.run_with_timeout_and_interrupt(
                            smx.write_def_ana_reg,
                            args=(smx.address, pol_calib),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            log.info(f"write_def_ana_reg was interrupted for ASIC {smx.address}")
                            return -1
                        
                        if check_continue and not check_continue():
                            log.info(f"load_STD_Config aborted after write_def_ana_reg for ASIC {smx.address}")
                            return -1
                            
                        log.info(f"Running read_reg_all with timeout and interrupt for ASIC {smx.address}")
                        result = self.run_with_timeout_and_interrupt(
                            smx.read_reg_all,
                            kwargs={"compFlag": False},
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            log.info(f"read_reg_all was interrupted for ASIC {smx.address}")
                            return -1
                    else:
                        smx.write_def_ana_reg(smx.address, pol_calib)
                        smx.read_reg_all(compFlag = False)
                else:
                    pass
        return 0
         
    def set_Trim_default(self, smx_l_side, pol, feb_type, cal_asic_list, check_continue=None):
        feb_type_sw = []
        if (pol == 'N' or pol == '0'):
            pol_str = 'N-side'
        else:
            pol_str = 'P-side'

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)
            
        if check_continue and not check_continue():
            log.info("set_Trim_default aborted during initialization")
            return -1

        for asic_sw in feb_type_sw:
            if check_continue and not check_continue():
                log.info(f"set_Trim_default aborted at asic_sw={asic_sw}")
                return -1
                
            for smx in smx_l_side:
                if check_continue and not check_continue():
                    log.info(f"set_Trim_default aborted at asic_sw={asic_sw}, smx.address={smx.address}")
                    return -1
                    
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    header_line  = "--> SETTING DEFAULT TRIM for ASIC with HW address {} and polarity {}".format(smx.address, pol_str)
                    log.info(header_line)
                    
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        log.info(f"Running set_trim_default with timeout and interrupt for ASIC {smx.address}")
                        result = self.run_with_timeout_and_interrupt(
                            smx.set_trim_default,
                            args=(128, 36),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            log.info(f"set_trim_default was interrupted for ASIC {smx.address}")
                            return -1
                    else:
                        smx.set_trim_default(128, 36)
                else:
                    pass
        return 0
     
    def scan_VrefP_N_Thr2glb(self, smx_l_side, pol, feb_type, cal_asic_list, npulses = 100, test_ch = 64, amp_cal_min = 30, amp_cal_max = 247, amp_cal_fast = 30, vref_t = 118, check_continue=None, progress_callback=None, base_progress=0):
        smx_cnt = 0
        feb_type_sw = []
        cal_set_asic = []
        if (pol == 'N' or pol == '0'):
            pol_str = 'N-side'
            pol_calib = 0 
        else:
            pol_str = 'P-side'
            pol_calib = 1

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)
            
        if check_continue and not check_continue():
            log.info("scan_VrefP_N_Thr2glb aborted during initialization")
            return -1
        
        total_iterations = 0
        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    total_iterations += 1
        
        current_iteration = 0

        for asic_sw in feb_type_sw:
            if check_continue and not check_continue():
                log.info(f"scan_VrefP_N_Thr2glb aborted at asic_sw={asic_sw}")
                return -1
                
            for smx in smx_l_side:
                if check_continue and not check_continue():
                    log.info(f"scan_VrefP_N_Thr2glb aborted at asic_sw={asic_sw}, smx.address={smx.address}")
                    return -1
                    
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    header_line  = "--> SCANNING VREF_P,N & THR2_GLB for ASIC with HW address {} and polarity {}".format(smx.address, pol_str)
                    log.info(header_line)
                    
                    if progress_callback:
                        progress_callback(base_progress, current_iteration, total_iterations)
                    
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        log.info(f"Running vrefpn_scan with timeout and interrupt for ASIC {smx.address}")
                        result = self.run_with_timeout_and_interrupt(
                            smx.vrefpn_scan,
                            args=(pol_calib, test_ch, npulses, amp_cal_min, amp_cal_max, amp_cal_fast, vref_t),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            log.info(f"vrefpn_scan was interrupted for ASIC {smx.address}")
                            return -1
                        
                        cal_set_asic.append(result)
                    else:
                        cal_set_asic.append(smx.vrefpn_scan(pol_calib, test_ch, npulses, amp_cal_min, amp_cal_max, amp_cal_fast, vref_t))
                        
                    current_iteration += 1
                
                    if progress_callback:
                        progress_callback(base_progress, current_iteration, total_iterations)
                else:
                    pass
        return cal_set_asic

    def print_cal_settings(self, pol, cal_set_side, cal_asic_list, vref_t_calib = 118):
        # Publishing the VREF_P_N & Thr2_glb results
        if (pol == 'N' or pol == '0'):
            pol_str = 'N-side'
        else:
            pol_str = 'P-side'
        info = "--> CALIBRATION SETTINGS for {}".format(pol_str)
        log.info(info)
        header_line = "HW_address \t VRef_P \t VRef_N \t VRef_T \t Thr2_glb"
        log.info(header_line)
        
        smx_cnt = 0
        for asic in cal_set_side:
            info = "{}\t{}\t{}\t{}\t{}".format(cal_asic_list[smx_cnt], asic[0], asic[1], vref_t_calib,  asic[2])
            log.info(info)
            smx_cnt +=1
        return 0

    def writing_cal_settings(self, smx_l_side, pol, feb_type,  cal_set_side, cal_asic_list, vref_t_calib = 118):
        vref_n_arr = []
        vref_p_arr = []
        thr2_glb_arr = []
        feb_type_sw = []
        #if (len(smx_l_side)!= len(cal_set_side)):
        #log.error("Length of the calibration settings array and the number of ASICs does not coincide")
        #else:
        info = ""
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        for asic in cal_set_side:
            vref_p_arr.append(asic[0])
            vref_n_arr.append(asic[1])
            thr2_glb_arr.append(asic[2])
        if (pol == 'N' or pol == '0'):
            pol_str = 'N-side'
            info = "CAL_SETTINGS_N"
        else:
            pol_str = 'P-side'
            info = "CAL_SETTINGS_P"
        log.info(info)
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        info = "INDEX: \t HW_ADDR: \t VRef_P: \t VRef_N: \t VRef_T: \t VRef_T_range \t Thr2_glb:"
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)

        smx_cnt = 0
        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    smx.write(130, 9, vref_p_arr[smx_cnt])
                    smx.write(130, 8, vref_n_arr[smx_cnt])
                    smx.write(130, 18, vref_t_calib)
                    smx.write(130, 7, thr2_glb_arr[smx_cnt])
                    vreft_range  = (smx.read(130,10)&64)>>4 or (smx.read(130,18)&192)>>6
                    # -----------------------------------------------------------------------
                    info = "{}\t\t {}\t\t {}\t\t {}\t\t {}\t\t {}\t\t {}".format(smx_cnt, smx.address, smx.read(130,9)&0xff, smx.read(130,8)&0xff, smx.read(130,18)&0xff, vreft_range, smx.read(130,7)&0xff)
                    log.info(info)
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    smx_cnt +=1
                else:
                    pass
                
    # To check calibration function
    def calib_FEB(self, smx_l_side, trim_dir, pol, feb_type, cal_asic_list, npulses = 40, amp_cal_min = 30, amp_cal_max = 247, amp_cal_fast = 30, much_mode_on = 0, check_continue=None):
        # Function to calibrate the ADC and FAST discriminator of each ASIC according to the given polarity
        info = ""
        feb_type_sw = []
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        filename_trim = trim_dir
        pol_calib = 0
        if (pol == 'N' or pol == '0'):
            pol_str = 'elect'
            pol_calib = 0
            info = 'TRIM_FILE_N'
        elif (pol == 'P' or pol == '1'):
            pol_str = 'holes'
            pol_calib = 1
            info = 'TRIM_FILE_P'
        else:
            log.error("Please check the polarity is correct: (ex: string 'N' or '0', 'P' or '1')")
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        
        if check_continue and not check_continue():
            log.info("calib_FEB aborted after initialization")
            return -1
        
        trim_final = [[0 for d in range(32)] for ch in range(128)]    
        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)
        
        for asic_sw in feb_type_sw:
            if check_continue and not check_continue():
                log.info(f"calib_FEB aborted at asic_sw={asic_sw}")
                return -1
            
            for smx in smx_l_side:
                if check_continue and not check_continue():
                    log.info(f"calib_FEB aborted at asic_sw={asic_sw}, smx.address={smx.address}")
                    return -1
                
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    asic_hw_addr = smx.address
                    # Launching the calibration with the corresponding
                    info = "--> RUNNING CALIBRATION FOR ASIC with HW ADDRESS {} in {}".format(asic_hw_addr, pol_str)
                    log.info(info)
                    # Elements for the filename
                    asic_id_str = smx.read_efuse_str()
                    vref_n = smx.read(130,8)&0xff
                    vref_p = smx.read(130,9)&0xff
                    vref_t = smx.read(130,18)&0xff
                    thr2_glb = smx.read(130,7)&0xff
                    date_fw = datetime.now().strftime("%y%m%d_%H%M")
                    filename_str = 'ftrim_' + asic_id_str + '_HW_' + str(asic_hw_addr) + '_SET_'+ str(vref_p) + '_' + str(vref_n) + '_' + str(vref_t) + '_' + str(thr2_glb) + '_R_' + str(amp_cal_min) + '_' + str(amp_cal_max) + '_' + pol_str
                    filename_trim = trim_dir + filename_str
                    # Executing calibration
                    log.info("Calib file name: {}".format(filename_trim))
                    
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        log.info(f"Running get_trim_adc_SA with timeout and interrupt for ASIC {asic_hw_addr}")
                        
                        result = self.run_with_timeout_and_interrupt(
                            smx.get_trim_adc_SA,
                            args=(pol_calib, trim_final, 40, amp_cal_min, amp_cal_max, much_mode_on),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            log.info(f"get_trim_adc_SA was interrupted for ASIC {asic_hw_addr}")
                            return -1
                        
                        if check_continue and not check_continue():
                            log.info(f"calib_FEB aborted after get_trim_adc_SA for ASIC {asic_hw_addr}")
                            return -1
                        
                        log.info(f"Running get_trim_fast with timeout and interrupt for ASIC {asic_hw_addr}")
                        result = self.run_with_timeout_and_interrupt(
                            smx.get_trim_fast,
                            args=(pol_calib, trim_final, npulses, amp_cal_fast, much_mode_on),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            log.info(f"get_trim_fast was interrupted for ASIC {asic_hw_addr}")
                            return -1
                        
                        if check_continue and not check_continue():
                            log.info(f"calib_FEB aborted after get_trim_fast for ASIC {asic_hw_addr}")
                            return -1
                    else:
                        smx.get_trim_adc_SA(pol_calib, trim_final, 40, amp_cal_min, amp_cal_max, much_mode_on)
                        
                        if check_continue and not check_continue():
                            log.info(f"calib_FEB aborted after get_trim_adc_SA for ASIC {asic_hw_addr}")
                            return -1
                        
                        smx.get_trim_fast(pol_calib, trim_final, npulses, amp_cal_fast, much_mode_on)
                        
                    if check_continue and not check_continue():
                        log.info(f"calib_FEB aborted before writing trim file for ASIC {asic_hw_addr}")
                        return -1
                    
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        log.info(f"Running write_trim_file with timeout and interrupt for ASIC {asic_hw_addr}")
                        result = self.run_with_timeout_and_interrupt(
                            smx.write_trim_file,
                            args=(filename_trim, pol_calib, trim_final, amp_cal_min, amp_cal_max, amp_cal_fast, much_mode_on),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            log.info(f"write_trim_file was interrupted for ASIC {asic_hw_addr}")
                            return -1
                    else:
                        smx.write_trim_file(filename_trim, pol_calib, trim_final, amp_cal_min, amp_cal_max, amp_cal_fast, much_mode_on)
                    
                    info = "CAL_ASIC_HW_ADDR_{}: {}.txt".format(asic_hw_addr,filename_str)
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    self.df.write_log_file(self.vd.module_dir, self.vd.module_sn, info)            
                else:
                    pass
                    
        return 0

    def set_trim_calib(self, smx_l_side, trim_dir, pol, feb_type, cal_asic_list, much_mode_on = 0, check_continue=None):
        # Function to set the calibration values the ADC and FAST discriminator of each ASIC according to the given polarity and the ASIC ID                            
        filename_trim = trim_dir
        feb_type_sw = []
        pol_calib = 0
        if (pol == 'N' or pol == '0'):
            pol_str = 'elect'
            pol_calib = 0
        elif (pol == 'P' or pol == '1'):
            pol_str = 'holes'
            pol_calib = 1
        else:
            log.error("Please check the polarity is correct: (ex: string 'N' or '0', 'P' or '1')")

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)
            
        if check_continue and not check_continue():
            log.info("set_trim_calib aborted during initialization")
            return -1

        for asic_sw in feb_type_sw:
            if check_continue and not check_continue():
                log.info(f"set_trim_calib aborted at asic_sw={asic_sw}")
                return -1
                
            for smx in smx_l_side:
                if check_continue and not check_continue():
                    log.info(f"set_trim_calib aborted at asic_sw={asic_sw}, smx.address={smx.address}")
                    return -1
                    
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    asic_hw_addr = smx.address
                    # Setting the TRIM calibration values                                                                                                                  
                    info = "--> SETTING TRIM CALIBRATION VALUES FOR ASIC with HW ADDRESS {} in {}".format(asic_hw_addr, pol_str)
                    log.info(info)
                    # Elements for the trim file
                    
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        log.info(f"Running read_efuse_str with timeout and interrupt for ASIC {smx.address}")
                        asic_id_str = self.run_with_timeout_and_interrupt(
                            smx.read_efuse_str,
                            args=(),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if asic_id_str is None and check_continue and not check_continue():
                            log.info(f"read_efuse_str was interrupted for ASIC {smx.address}")
                            return -1
                        
                        if check_continue and not check_continue():
                            log.info(f"set_trim_calib aborted after read_efuse_str for ASIC {smx.address}")
                            return -1
                            
                        log.info(f"Running set_trim with timeout and interrupt for ASIC {smx.address}")
                        result = self.run_with_timeout_and_interrupt(
                            smx.set_trim,
                            args=(trim_dir, pol_calib, asic_id_str),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            log.info(f"set_trim was interrupted for ASIC {smx.address}")
                            return -1
                    else:
                        asic_id_str = smx.read_efuse_str()
                        smx.set_trim(trim_dir, pol_calib, asic_id_str)
                else:
                    pass
        return 0

    def check_trim(self, smx_l_side, pscan_dir, pol, feb_type, cal_asic_list, disc_list = [5,10,16,24,30,31], vp_min = 0, vp_max = 255, vp_step = 1, npulses = 100, check_continue=None):
        # Function to measure the ADC and FAST discriminator response function for a  given number of discriminators of an ASIC                                                          
        info = ""
        feb_type_sw = []
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        pol_calib = 0
        disc_list = disc_list
        npulses = npulses
        vp_min = vp_min
        vp_max = vp_max
        vp_step = vp_step
        
        if (pol == 'N' or pol == '0'):
            pol_str = 'elect'
            pol_calib = 0
            info = 'PSCAN_FILE_N'
        elif (pol == 'P' or pol == '1'):
            pol_str = 'holes'
            pol_calib = 1
            info = 'PSCAN_FILE_P'
        else:
            log.error("Please check the polarity is correct: (ex: string 'N' or '0', 'P' or '1')")
            
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        
        if check_continue and not check_continue():
            log.info("check_trim aborted after initialization")
            return -1

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)

        for asic_sw in feb_type_sw:
            if check_continue and not check_continue():
                log.info(f"check_trim aborted at asic_sw={asic_sw}")
                return -1
            
            for smx in smx_l_side:
                if check_continue and not check_continue():
                    log.info(f"check_trim aborted at asic_sw={asic_sw}, smx.address={smx.address}")
                    return -1
                
                asic_hw_addr = smx.address
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):                                                                                                  
                    info = "PSCAN_ASIC_HW_ADDR_{}: {}".format(asic_hw_addr, pol_str)
                    log.info(info)
                                                                                                                                            
                    asic_id_str = smx.read_efuse_str()
                    
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        log.info(f"Running check_trim_red with timeout and interrupt for ASIC {asic_hw_addr}")
                        
                        pscan_filename = self.run_with_timeout_and_interrupt(
                            smx.check_trim_red,
                            args=(
                                pscan_dir, pol_calib, asic_id_str, 
                                disc_list, vp_min, vp_max, vp_step, npulses
                            ),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if pscan_filename is None:
                            if check_continue and not check_continue():
                                log.info(f"check_trim_red was interrupted for ASIC {asic_hw_addr}")
                                return -1
                            else:
                                log.error(f"check_trim_red failed for ASIC {asic_hw_addr}")
                                continue
                    else:
                        log.warning("run_with_timeout_and_interrupt not available, using original method (cannot be interrupted)")
                        try:
                            pscan_filename = smx.check_trim_red(
                                pscan_dir, pol_calib, asic_id_str, 
                                disc_list, vp_min, vp_max, vp_step, npulses
                            )
                        except Exception as e:
                            log.error(f"Error in check_trim_red for ASIC {asic_hw_addr}: {str(e)}")
                            continue
                    
                    if check_continue and not check_continue():
                        log.info(f"check_trim aborted after check_trim_red for ASIC {asic_hw_addr}")
                        return -1
                        
                    info = "PSCAN_ASIC_HW_ADDR_{}: {}".format(asic_hw_addr, pscan_filename)
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    self.df.write_log_file(self.vd.module_dir, self.vd.module_sn, info)
                else:
                    pass
                    #info = "SKIP_PSCAN_ASIC_HW_ADDR_{}".format(asic_hw_addr)
                    #log.info(info)
                    #self.df.write_data_file(self.vd.module_dir, self.vd.self.vd.module_sn_tmp, info)
                    #self.df.write_log_file(self.vd.module_dir, self.vd.module_sn, info)
        return 0

    def connection_check(self, smx_l_side, conn_check_dir, pol, feb_type, cal_asic_list, nloops = 5, vref_t = 108, check_continue=None):
        # Function to check the connectivy of each channel by counting noise hits at a lower threshold
        info = ""
        feb_type_sw = []
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        if (pol == 'N' or pol == '0'):
            pol_str = 'elect'
            pol_calib = 0
            info = 'CH_CONN_CHECK_FILE_N'
        elif (pol == 'P' or pol == '1'):
            pol_str = 'holes'
            pol_calib = 1
            info = 'CH_CONN_CHECK_FILE_P'
        else:
            log.error("Please check the polarity is correct: (ex: string 'N' or '0', 'P' or '1')")
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        
        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)
            
        if check_continue and not check_continue():
            log.info("connection_check aborted during initialization")
            return -1

        log.info("FEB type: {}".format(feb_type[-2:-1]))
        for asic_sw in feb_type_sw:
            if check_continue and not check_continue():
                log.info(f"connection_check aborted at asic_sw={asic_sw}")
                return -1
                
            for smx in smx_l_side:
                if check_continue and not check_continue():
                    log.info(f"connection_check aborted at asic_sw={asic_sw}, smx.address={smx.address}")
                    return -1
                    
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    # Checking ENC and calibration results for an ASIC     
                    info = "CONN-CHECK_ASIC_HW_ADDR_{}: {}".format(smx.address, pol_str)
                    log.info(info)
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    self.df.write_log_file(self.vd.module_dir, self.vd.module_sn, info)
                    
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        log.info(f"Running connection_check with timeout and interrupt for ASIC {smx.address}")
                        result = self.run_with_timeout_and_interrupt(
                            smx.connection_check,
                            args=(conn_check_dir, pol_calib, nloops, vref_t),
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            log.info(f"connection_check was interrupted for ASIC {smx.address}")
                            return -1
                    else:
                        smx.connection_check(conn_check_dir, pol_calib, nloops, vref_t)
                else:
                    pass
        return 0
