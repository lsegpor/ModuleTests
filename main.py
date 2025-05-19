import sys
sys.path.append('../autogen/agwb/python/')
sys.path.append('../smx_tester/')
from smx_tester import *
from config_tests import ConfigTests as ct
from file_management import FileManagement as fm
from operating_functions import OperatingFunctions
from power_tests import PowerTests as pt
from variables_definition import VariablesDefinition
from directory_files import DirectoryFiles
import emu_lock
import threading



class Main:

    def __init__(self):
        self.df = DirectoryFiles()
        self.vd = VariablesDefinition(self.df)
        self.df.vd = self.vd
        self.of = OperatingFunctions(self.vd)
        self.smx_l_nside = []
        self.smx_l_pside = []
        
        self._smx_lock = threading.Lock()
        self._execute_lock = threading.Lock()
        
        self.step_times = {
            "power_on_emu": 2,
            "full_sync": 28,
            "turn_hv_on": 2,
            "read_lv_bc": 1,
            "std_config": 6,
            "read_asic_id": 1,
            "set_Trim_default": 65,
            "read_lv_ac": 10,
            "read_emu": 1,
            "check_vddm_temp": 3,
            "set_trim_calib": 69,
            "check_trim": 7200,
            "get_vrefs": 250,
            "set_calib_par": 1,
            "get_trim": 10800,
            "turn_hv_off": 6,
            "conn_check": 8,
            "reg_config_stress": 10,
            "iv_meas": 3,
            "set_mbias": 2,
            "long_run": 40
        }

    def execute_tests(self, module, sn_nside, sn_pside, slc_nside, slc_pside, emu, tests_values, s_size,
                      s_qgrade, asic_nside_values, asic_pside_values, suid, lv_nside_12_checked,
                      lv_pside_12_checked, lv_nside_18_checked, lv_pside_18_checked, module_files, calib_path,
                      update_progress, update_test_label, update_emu_values, update_vddm, update_temp,
                      update_feb_nside, update_feb_pside, update_calib_path, update_save_path, tab_id,
                      check_continue=None):
        
        if not self._execute_lock.acquire(blocking=False):
            raise Exception(f"Another test is already running in this tab (Tab {tab_id})")
        
        emu_id = emu
        
        if check_continue is None:
            check_continue = lambda: True
        
        if not emu_lock.acquire_emu(emu_id, tab_id, timeout=30):
            self._execute_lock.release()
            raise Exception(f"Could not acquire lock for {emu_id} in Tab {tab_id}")
        
        try:
            self.vd.setValues(module, emu, module_files, calib_path)
            self.vd.selected_tests(tests_values)
            self.vd.selected_asics(asic_nside_values, asic_pside_values)
            
            local_cal_asic_list_nside = self.vd.cal_asic_list_nside.copy()
            local_cal_asic_list_pside = self.vd.cal_asic_list_pside.copy()
            
            def get_valid_selections():
                with self._smx_lock:
                    n_length = len(self.smx_l_nside)
                    p_length = len(self.smx_l_pside)
                    
                    valid_nside_indices = [i for i in local_cal_asic_list_nside if 0 <= i < n_length]
                    valid_pside_indices = [i for i in local_cal_asic_list_pside if 0 <= i < p_length]
                    
                    log.info(f"Tab {tab_id}: smx_l_nside length: {n_length}, valid indices: {valid_nside_indices}")
                    log.info(f"Tab {tab_id}: smx_l_pside length: {p_length}, valid indices: {valid_pside_indices}")
                    
                    selected_smx_l_nside = [self.smx_l_nside[i] for i in valid_nside_indices]
                    selected_smx_l_pside = [self.smx_l_pside[i] for i in valid_pside_indices]
                    
                    return selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices
            
            module_sn = 'na'
            module_str = []
            nfails = 0
            
            total_time = sum(self.step_times.get(step, 5) for step in self.vd.test_list)
            accumulated_progress = 0
            
            while(module_sn == 'na' and nfails < 3):
                module_str.extend(self.df.check_moduleId(module, s_size, s_qgrade))
                module_sn = module_str[0]
                if (module_sn == 'na'):
                    module_str.clear()
                    nfails+=1       
                if (nfails ==3):
                    print("Multiple fails on Writing Module ID. It should contain A or B in the second-to-last position. Please check the Module's information")
                    sys.exit()
                else:
                    pass

            # self.vd.module_dir = vd.module_path + "/" + str(vd.ladder_sn) + "/" + str(module_sn)
            # self.vd.module_sn_tmp = self.df.initWorkingDirectory(self.vd.module_dir, module_sn)
            print(self.vd.module_dir)
            pscan_dir = self.df.making_pscan_dir(self.vd.module_dir)
            trim_dir = self.df.making_trim_dir(self.vd.module_dir)
            #trim_dir = self.vd.calibration_data_path + "/" + str(self.vd.ladder_sn) + "/" + str(module_sn) + "/trim_files/"
            update_calib_path(self.vd.calibration_data_path + "/" + str(self.vd.ladder_sn) + "/" + str(module_sn) + "/trim_files")
            update_save_path(str(self.vd.ladder_sn) + "/" + str(module_sn))
            print(trim_dir)
            conn_check_dir = self.df.making_conn_check_dir(self.vd.module_dir)
            # Setting logging directory
            fm.set_logging_details(self.vd.module_dir)


            # Step 0: --------------- Initiazlizing data & log files -----------------

            info = "TEST_CENTER: {}".format(self.df.read_test_center())
            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
            self.df.write_log_file(self.vd.module_dir, module_sn, info)
            info = "OPERATOR_ID: {}".format(self.df.read_operator_id())
            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
            self.df.write_log_file(self.vd.module_dir, module_sn, info)

            info = "MODULE ID: \t{}".format(module_sn)
            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
            self.df.write_log_file(self.vd.module_dir, module_sn, info)
            info = "SENSOR_SIZE [mm]: \t{}".format(module_str[1])
            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
            self.df.write_log_file(self.vd.module_dir, module_sn, info)
            info = "SENSOR_QGRADE: \t{}".format(module_str[2])
            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
            self.df.write_log_file(self.vd.module_dir, module_sn, info)

            # Step 1.1: -------------- Turning ON LV for N & P-side -------------------
            #powerOn_lv('N')
            #powerOn_lv('P')
            #time.sleep(5)
            #lv_nside_bc = pt.reading_lv('N')
            #lv_pside_bc = pt.reading_lv('P')

            # Step 1.2: ---------------- Setting active downlinks ---------------------
            # Setting active downlinks according to the module type.
            # Since N-side should be connected on the slot 0 of the EMU_FMC, the active downlinks
            # can be determined for this configuration by knowing the Module ID. The Module ID
            # contains the P-side FEB type

            active_downlinks = []

            active_downlinks_map = {
                "EMU_236": [0,1,2,3],     # R- module 0, 1  
                "EMU_235": [0,1,2,3],     # R-module 2, 3
                "EMU_233": [0,1],         # R-module 4
                "EMU_245": [1,2,3,4],     # L-module 0, 1  
                "EMU_243": [1,2,3,4],     # L-module 2, 3
                "EMU_242": [1,2],         # L-module 4
                "EMU_238": [0,1,2,3],
                "EMU_234": [0,1,2,3],
                "EMU_213": [0,1,2,3],
            }
            
            if emu in active_downlinks_map:
                if (module_sn[-2:-1] == 'A'):
                    active_downlinks.append(0)
                    active_downlinks.append(3)
                elif (module_sn[-2:-1] == 'B'):
                    active_downlinks.append(1)
                    active_downlinks.append(2)
                else:
                    for i in range(0,4):
                        active_downlinks.append(i)
                #active_downlinks.extend(active_downlinks_map[emu])

            # Setp 2: ------------------ Checking the FEBs ID -------------------------
            # System exit if nfails = 3
            feb_nside ='na'
            nfails = 0
            if (nfails < 3):
                while(feb_nside == 'na'):
                    feb_nside = sn_nside
                    if(feb_nside == 'na'):
                        nfails+=1
            else:
                sys.exit()
            info = "FEB_SN_N:\t {}".format(feb_nside) 
            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)

            feb_pside ='na'
            nfails = 0
            if (nfails < 3):
                while(feb_pside =='na'):
                    feb_pside = sn_pside
                    if (feb_pside =='na'):
                        nfails+=1
            else:
                sys.exit()    
            info = "FEB_SN_P:\t {}".format(feb_pside)
            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)

            # TEMP_ARR. Fix HV readout
            hv_current_n = slc_nside
            info = "I_SENSOR_150V_N: {} [uA]".format(hv_current_n)
            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)

            hv_current_p = slc_pside
            info = "I_SENSOR_150V_P: {} [uA]".format(hv_current_p)
            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
            
            cal_asic_list_nside = []
            cal_asic_list_pside = []
            
            if hasattr(self.vd, 'stored_vddm_values'):
                self.vd.stored_vddm_values = {'N': [], 'P': []}

            # RUNNING TEST SEQUENCE
            # -------------------------------------------
            for i, test_step in enumerate(self.vd.test_list):
                if not check_continue():
                    update_test_label("*** TEST EXECUTION STOPPED ***")
                    return
                
                update_test_label(f"Executing: {test_step}")
                step_percentage = (self.step_times.get(test_step, 5) / total_time) * 100
                
                if (test_step == "power_on_emu"):
                    log.info(" ------------------- POWERING UP EMU BOARD ---------------------- ")
                    info = "-->> POWERING UP EMU BOARD"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Step 1: -------------- Turning ON LV for EMU board -------------------
                    pt.powerOn_EMU(self.vd.emu_channel)
                    #time.sleep(10)
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return

                elif (test_step =="full_sync"):
                    log.info(" ------------------- RUNNING SYNCHRONIZATION ---------------------- ")
                    info = "-->> RUNNING SYNCHRONIZATION"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 2: -------- Starting with connection and synchronization ----------- 
                    try:
                        # Step 2: -------- Starting with connection and synchronization ----------- 
                        info = "EMU_BOARD_SN: {}".format(emu)
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        info = "SENSOR UNIQUE ID: {}".format(suid)
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        
                        log.info(f"Tab {tab_id}: Starting general_sync with emu={emu}, active_downlinks={active_downlinks}")
                        smx_l = ct.general_sync(emu, active_downlinks)
                        log.info(f"Tab {tab_id}: Completed general_sync, got smx_l of length {len(smx_l) if smx_l else 0}")
                        
                        # 2.1 Determining the number of ASICs per side
                        n_asic_all = ct.scanning_asics(smx_l)
                        log.info(f"Tab {tab_id}: scanning_asics returned {n_asic_all}")
                        
                        # 2.2 Assigning the ASICs according to polarities
                        n_asics = n_asic_all[0] if n_asic_all and len(n_asic_all) > 0 else 0
                        p_asics = n_asic_all[1] if n_asic_all and len(n_asic_all) > 1 else 0
                        
                        log.info(f"Tab {tab_id}: n_asics={n_asics}, p_asics={p_asics}")
                        
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, "")
                        info = "No_SYNC_N:\t {}".format(n_asics)
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        info = "No_SYNC_P:\t {}".format(p_asics)
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        
                        if (n_asics != 0 and len(active_downlinks) > 1):
                            info = "DWN_LINK_N: {}".format(active_downlinks[1])
                        else:
                            info = "DWN_LINK_N: -1"
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        
                        if (p_asics != 0 and len(active_downlinks) > 0):
                            info = "DWN_LINK_P: {}".format(active_downlinks[0])
                        else:
                            info = "DWN_LINK_P: -1"
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        
                        # 2.3 Distributing the ASICs in arrays according to operational polarity 
                        # Temp: ASICs asigned for module. M0
                        with self._smx_lock:
                            if smx_l is not None:
                                end_idx = min(n_asics + p_asics, len(smx_l))
                                start_idx = min(n_asics, len(smx_l))
                                self.smx_l_pside = smx_l[start_idx:end_idx] if start_idx < end_idx else []
                                self.smx_l_nside = smx_l[0:start_idx] if start_idx > 0 else []
                                log.info(f"Tab {tab_id}: Assigned smx_l_nside (len={len(self.smx_l_nside)}) and smx_l_pside (len={len(self.smx_l_pside)})")
                            else:
                                log.warning(f"Tab {tab_id}: smx_l is None, cannot assign smx_l_nside and smx_l_pside")
                                self.smx_l_pside = []
                                self.smx_l_nside = []
                        
                        info = "<<-- FINISHED SYNCHRONIZATION"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in full_sync: {str(e)}")
                        with self._smx_lock:
                            if not hasattr(self, 'smx_l_nside') or self.smx_l_nside is None:
                                self.smx_l_nside = []
                            if not hasattr(self, 'smx_l_pside') or self.smx_l_pside is None:
                                self.smx_l_pside = []
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                
                if not check_continue():
                    update_test_label("*** TEST EXECUTION STOPPED ***")
                    return

                elif(test_step == "turn_hv_on"):
                    log.info(" ---------------------------- TURNING ON HIGH VOLTAGE -------------------------------- ")
                    info = "-->> TURNING ON HIGH VOLTAGE FOR THE Si SENSOR"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    hv_current_n, hv_current_p = pt.powerON_hv(self.vd.hv_n_channel, self.vd.hv_p_channel, self.vd.bias_voltage)
                    info = "I_SENSOR_150V_N: {} [uA]".format(hv_current_n)
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    info = "I_SENSOR_150V_P: {} [uA]".format(hv_current_p)
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    info = "<<-- FINISHED BIASING THE Si SENSOR"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                
                elif (test_step =="read_lv_bc"):
                    log.info(" ---------------------- READING LV VALUES BEFORE CONFIGURATION------------------------- ")
                    info = "-->> READING LV VALUES BEFORE CONFIGURATION"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 4: --------------- Measuring LV before configuration ---------------
                    info = ""
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    
                    if lv_nside_12_checked or lv_nside_18_checked:
                        info = "LV_BEF_CONFIG_N"
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        lv_nside_bc = pt.reading_lv('N', self.vd.emu_channel, read_12v=lv_nside_12_checked, read_18v=lv_nside_18_checked)
                        update_feb_nside(lv_nside_bc[0], lv_nside_bc[1], lv_nside_bc[2], lv_nside_bc[3])
                        
                        if lv_nside_12_checked:
                            info = "FEB N-side:\t{}\tLV_1.2_BC_N [V]:\t{}\tI_1.2_BC_N [A]:\t{}".format(feb_nside, lv_nside_bc[0], lv_nside_bc[1])
                            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        
                        if lv_nside_18_checked:
                            info = "FEB N-side:\t{}\tLV_1.8_BC_N [V]:\t{}\tI_1.8_BC_N [A]:\t{}".format(feb_nside, lv_nside_bc[2], lv_nside_bc[3])
                            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    
                    else:
                        update_feb_nside(0.0, 0.0, 0.0, 0.0)
                        
                    if lv_pside_12_checked or lv_pside_18_checked:
                        info = "LV_BEF_CONFIG_P"
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        lv_pside_bc = pt.reading_lv('P', self.vd.emu_channel, read_12v=lv_pside_12_checked, read_18v=lv_pside_18_checked)
                        update_feb_pside(lv_pside_bc[0], lv_pside_bc[1], lv_pside_bc[2], lv_pside_bc[3])
                        
                        if lv_pside_12_checked:
                            info = "FEB P-side:\t{}\tLV_1.2_BC_P [V]:\t{}\tI_1.2_BC_P [A]:\t{}".format(feb_pside, lv_pside_bc[0], lv_pside_bc[1])
                            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        
                        if lv_pside_18_checked:
                            info = "FEB P-side:\t{}\tLV_1.8_BC_P [V]:\t{}\tI_1.8_BC_P [A]:\t{}".format(feb_pside, lv_pside_bc[2], lv_pside_bc[3])
                            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    
                    else:
                        update_feb_pside(0.0, 0.0, 0.0, 0.0)
                    
                    info = "<<-- FINISHED READING LV VALUES BEFORE CONFIGURATION"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return
                    
                elif (test_step =="read_lv_ac"):
                    log.info(" ---------------------- READING LV VALUES AFTER CONFIGURATION ------------------------- ")
                    info = "-->> READING LV VALUES AFTER CONFIGURATION"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 7: --------------- Measuring LV after  configuration ---------------
                    info = ""
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    
                    if lv_nside_12_checked or lv_nside_18_checked:
                        info = "LV_AFT_CONFIG_N"
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        #time.sleep(10)
                        lv_nside_ac = pt.reading_lv('N', self.vd.emu_channel, read_12v=lv_nside_12_checked, read_18v=lv_nside_18_checked)
                        update_feb_nside(lv_nside_ac[0], lv_nside_ac[1], lv_nside_ac[2], lv_nside_ac[3])
                        
                        if lv_nside_12_checked:
                            info = "FEB N-side:\t{}\tLV_1.2_AC_N [V]:\t{}\tI_1.2_AC_N [A]:\t{}".format(feb_nside, lv_nside_ac[0], lv_nside_ac[1])
                            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                            
                        if lv_nside_18_checked:
                            info = "FEB N-side:\t{}\tLV_1.8_AC_N [V]:\t{}\tI_1.8_AC_N [A]:\t{}".format(feb_nside, lv_nside_ac[2], lv_nside_ac[3])
                            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    else:
                        update_feb_pside(0.0, 0.0, 0.0, 0.0)
                    
                    if lv_pside_12_checked or lv_pside_18_checked:
                        info = "LV_AFT_CONFIG_P"
                        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                        lv_pside_ac = pt.reading_lv('P', self.vd.emu_channel, read_12v=lv_pside_12_checked, read_18v=lv_pside_18_checked)
                        update_feb_pside(lv_pside_ac[0], lv_pside_ac[1], lv_pside_ac[2], lv_pside_ac[3])
                        
                        if lv_pside_12_checked:
                            info = "FEB P-side:\t{}\tLV_1.2_AC_P [V]:\t{}\tI_1.2_AC_P [A]:\t{}".format(feb_pside, lv_pside_ac[0], lv_pside_ac[1])
                            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                            
                        if lv_pside_18_checked:
                            info = "FEB P-side:\t{}\tLV_1.8_AC_P [V]:\t{}\tI_1.8_AC_P [A]:\t{}".format(feb_pside, lv_pside_ac[2], lv_pside_ac[3])
                            self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    
                    else:
                        update_feb_pside(0.0, 0.0, 0.0, 0.0)
                        
                    info = "<<-- FINISHED READING LV VALUES AFTER CONFIGURATION"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return
                    
                elif (test_step =="read_emu"):
                    log.info(" ---------------------- READING EMU VALUES ------------------------- ")
                    info = "-->> READING EMU VALUES"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    info = ""
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    emu_values = pt.reading_lv_emu(self.vd.emu_channel)
                    info = "EMU_V [V]: {}".format(emu_values[0])
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    info = "EMU_I [A]: {}".format(emu_values[1])
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    update_emu_values(emu_values[0], emu_values[1])
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return

                elif (test_step =="std_config"):
                    log.info(" ------------- LOADING STANDARD CONFIGURATION --------------------- ")
                    info = "-->> LOADING STANDARD CONFIGURATION"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Setp 5: --------------- Setting the standard ASIC configuration ---------
                    try:
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        if selected_smx_l_nside:
                            self.of.load_STD_Config(selected_smx_l_nside, 'N', feb_nside)
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side SMX elements to configure")
                            
                        if selected_smx_l_pside:
                            self.of.load_STD_Config(selected_smx_l_pside, 'P', feb_pside)
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side SMX elements to configure")
                            
                        info = "<<-- FINISHED LOADING STANDARD CONFIGURATION"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in std_config: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return

                elif (test_step =="read_asic_id"):
                    log.info("----------------------- READING ASICs ID -------------------------- ")
                    info = "-->> READING ASICs ID"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 8: ----------------------- Reading ASIC ID -------------------------
                    try:
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        if selected_smx_l_nside:
                            self.of.read_asicIDs_FEB(selected_smx_l_nside, 'N', feb_nside)
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side SMX elements to read")
                            
                        if selected_smx_l_pside:
                            self.of.read_asicIDs_FEB(selected_smx_l_pside, 'P', feb_pside)
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side SMX elements to read")
                            
                        info = "<<-- FINISHED READING ASICs ID"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in read_asic_id: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return

                elif (test_step =="set_Trim_default"):
                    log.info("---------------- LOADING DEFAULT TRIM VALUES ---------------------- ")
                    info = "-->> LOADING DEFAULT TRIM VALUES"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    #Function
                    # Step 6: --------------- Loading the default trim on the ASICs -----------
                    try:
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        if selected_smx_l_nside:
                            self.of.set_Trim_default(selected_smx_l_nside, 'N', feb_nside, valid_nside_indices)
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side SMX elements for set_Trim_default")
                            
                        if selected_smx_l_pside:
                            self.of.set_Trim_default(selected_smx_l_pside, 'P', feb_pside, valid_pside_indices)
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side SMX elements for set_Trim_default")
                            
                        info = "<<-- FINISHED LOADING DEFAULT TRIM VALUES"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in set_Trim_default: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return

                elif (test_step =="check_vddm_temp"):
                    log.info("-------------- READING VDDM & TEMPERATURE ------------------------- ")
                    info = "-->> READING VDDM & TEMPERATURE"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 9: -------------------- Reading VVDM & TEMP ------------------------
                    try:
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        if selected_smx_l_nside:
                            self.of.read_VDDM_TEMP_FEB(selected_smx_l_nside, "N", feb_nside)
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side SMX elements for check_vddm_temp")
                            
                        if selected_smx_l_pside:
                            self.of.read_VDDM_TEMP_FEB(selected_smx_l_pside, "P", feb_pside)
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side SMX elements for check_vddm_temp")
                        
                        log.info("BEFORE GET_VDDM_VALUES:")
                        has_stored = hasattr(self.vd, "stored_vddm_values")
                        log.info(f"Has stored VDDM values: {has_stored}")
                        if has_stored:
                            log.info(f"Stored N-side values: {self.vd.stored_vddm_values['N']}")
                            log.info(f"Stored P-side values: {self.vd.stored_vddm_values['P']}")
                        
                        nside_index = [i for i in local_cal_asic_list_nside]
                        pside_index = [i for i in local_cal_asic_list_pside]
                        
                        update_vddm(nside_index, self.vd.stored_vddm_values.get("N", []), 
                                pside_index, self.vd.stored_vddm_values.get("P", []))
                        
                        update_temp(nside_index, self.vd.stored_temp_values.get("N", []), 
                                pside_index, self.vd.stored_temp_values.get("P", []))
                        
                        info = "<<-- FINISHED READING VDDM & TEMPERATURE"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in check_vddm_temp: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return
                
                elif (test_step =="get_vrefs"):
                    log.info("-------------- FINDING VREF_P, VREF_N & THR@_GLB FOR CALIBRATION ------------------------- ")
                    info = "-->> FINDING VREF_P, VREF_N & THR@_GLB FOR CALIBRATION"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 10: ----------------- SCAN VREF_P, N & THR2_GLB --------------------
                    # 10.1 Scanning ADC and FAST discriminator potentials beforte calibration
                    # define default cal settings just in case
                    try:
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        cal_set_nside = None
                        cal_set_pside = None
                        
                        if selected_smx_l_nside:
                            cal_set_nside = self.of.scan_VrefP_N_Thr2glb(
                                selected_smx_l_nside, 'N', feb_nside, valid_nside_indices, 
                                self.vd.npulses, self.vd.test_ch, self.vd.amp_cal_min, 
                                self.vd.amp_cal_max, self.vd.amp_cal_fast, self.vd.vref_t
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side SMX elements for get_vrefs")
                            
                        if selected_smx_l_pside:
                            cal_set_pside = self.of.scan_VrefP_N_Thr2glb(
                                selected_smx_l_pside, 'P', feb_pside, valid_pside_indices, 
                                self.vd.npulses, self.vd.test_ch, self.vd.amp_cal_min, 
                                self.vd.amp_cal_max, self.vd.amp_cal_fast, self.vd.vref_t
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side SMX elements for get_vrefs")
                        
                        info = "<<-- FINISHED FINDING VREF_P, VREF_N & THR@_GLB FOR CALIBRATION"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in get_vrefs: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return
                
                elif (test_step =="set_calib_par"):
                    log.info("-------------- SETTING THE CALIBRATION PARAMETERS ------------------------- ")
                    info = "--> SETTING THE CALIBRATION PARAMETERS"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 10.2: --------- Printing calibration settings ----------------------
                    try:
                        if 'cal_set_nside' not in locals() or cal_set_nside is None:
                            log.warning(f"Tab {tab_id}: Missing cal_set_nside for set_calib_par")
                            cal_set_nside = []
                        
                        if 'cal_set_pside' not in locals() or cal_set_pside is None:
                            log.warning(f"Tab {tab_id}: Missing cal_set_pside for set_calib_par")
                            cal_set_pside = []
                        
                        self.of.print_cal_settings('N', cal_set_nside, valid_nside_indices)
                        self.of.print_cal_settings('P', cal_set_pside, valid_pside_indices)
                        
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        if selected_smx_l_nside and cal_set_nside:
                            self.of.writing_cal_settings(selected_smx_l_nside, 'N', feb_nside, cal_set_nside, valid_nside_indices)
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side elements for set_calib_par")
                        
                        if selected_smx_l_pside and cal_set_pside:
                            self.of.writing_cal_settings(selected_smx_l_pside, 'P', feb_pside, cal_set_pside, valid_pside_indices)
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side elements for set_calib_par")
                        
                        info = "<<-- FINISHED SETTING THE CALIBRATION PARAMETERS"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in set_calib_par: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return

                elif (test_step =="get_trim"):
                    log.info("-------------- CALIBRATING THE MODULE ------------------------- ")
                    info = "-->> CALIBRATING THE MODULE"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 11: ------------------ Calibrating the Module ---------------------
                    try:
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        if selected_smx_l_nside:
                            self.of.calib_FEB(
                                selected_smx_l_nside, trim_dir, 'N', feb_nside, valid_nside_indices, 
                                self.vd.npulses, self.vd.amp_cal_min, self.vd.amp_cal_max, 
                                self.vd.amp_cal_fast, much_mode_on=0
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side SMX elements for get_trim")
                        
                        if selected_smx_l_pside:
                            self.of.calib_FEB(
                                selected_smx_l_pside, trim_dir, 'P', feb_pside, valid_pside_indices, 
                                self.vd.npulses, self.vd.amp_cal_min, self.vd.amp_cal_max, 
                                self.vd.amp_cal_fast, much_mode_on=0
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side SMX elements for get_trim")
                        
                        info = "<<-- FINISHED CALIBRATING THE MODULE"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in get_trim: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return
                        
                elif (test_step =="set_trim_calib"):
                    log.info("---------------- SETTING THE CALIBRATION TRIM ----------------------------- ")
                    info = "--> SETTING THE CALIBRATION TRIM"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 12: ----------------- Setting Calibration Trim --------------------
                    try:
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        if selected_smx_l_nside:
                            self.of.set_trim_calib(
                                selected_smx_l_nside, trim_dir, 'N', feb_nside, 
                                valid_nside_indices, much_mode_on=0
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side SMX elements for set_trim_calib")
                        
                        if selected_smx_l_pside:
                            self.of.set_trim_calib(
                                selected_smx_l_pside, trim_dir, 'P', feb_pside, 
                                valid_pside_indices, much_mode_on=0
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side SMX elements for set_trim_calib")
                        
                        info = "<<-- FINISHED SETTING THE CALIBRATION TRIM"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in set_trim_calib: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return
                
                elif (test_step =="check_trim"):
                    log.info("-------------- MEASURING ENC AND CHECKING CALIBRATION ------------------------- ")
                    info = "--> MEASURING ENC AND CHECKING CALIBRATION"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    # Step 12: ------------------- ENC & Checking Trim ----------------------- 
                    try:
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        if selected_smx_l_nside:
                            self.of.check_trim(
                                selected_smx_l_nside, pscan_dir, 'N', feb_nside, valid_nside_indices, 
                                self.vd.disc_list, self.vd.vp_min, self.vd.vp_max, 
                                self.vd.vp_step, self.vd.npulses
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side SMX elements for check_trim")
                        
                        if selected_smx_l_pside:
                            self.of.check_trim(
                                selected_smx_l_pside, pscan_dir, 'P', feb_pside, valid_pside_indices, 
                                self.vd.disc_list, self.vd.vp_min, self.vd.vp_max, 
                                self.vd.vp_step, self.vd.npulses
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side SMX elements for check_trim")
                        
                        info = "<<-- FINISHED MEASURING ENC AND CHECKING CALIBRATION"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in check_trim: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return

                elif (test_step == "turn_hv_off"):
                    log.info(" --------------------------- TURNING OFF HIGH VOLTAGE -------------------------------- ")
                    info = "-->> TURNING OFF HIGH VOLTAGE FOR THE Si SENSOR"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    flag_hv_off = 0
                    while( flag_hv_off == 0):
                        if (pt.powerOff_hv(self.vd.hv_n_channel, self.vd.hv_p_channel) == True):
                            info = "<<-- HV Si SENSOR is OFF"
                            self.df.write_log_file(self.vd.module_dir, module_sn, info)
                            flag_hv_off = 1
                        else:
                            log.info("MODULE HV STILL ON")
                            #time.sleep(60)
                    info = "<<-- FINISHED TURNING OFF HV FOR Si SENSOR"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return

                elif (test_step =="conn_check"):
                    log.info("-------------- CHECKING CHANNELS' CONNECTIVITY ------------------------- ")
                    info = "--> CHECKING CHANNELS' CONNECTIVITY"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function
                    try:
                        selected_smx_l_nside, selected_smx_l_pside, valid_nside_indices, valid_pside_indices = get_valid_selections()
                        
                        if selected_smx_l_nside:
                            self.of.connection_check(
                                selected_smx_l_nside, conn_check_dir, 'N', feb_nside, 
                                valid_nside_indices, nloops, self.vd.vref_t_low
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid N-side SMX elements for conn_check")
                        
                        if selected_smx_l_pside:
                            self.of.connection_check(
                                selected_smx_l_pside, conn_check_dir, 'P', feb_pside, 
                                valid_pside_indices, nloops, self.vd.vref_t_low
                            )
                        else:
                            log.warning(f"Tab {tab_id}: No valid P-side SMX elements for conn_check")
                        
                        info = "<<-- FINISHED CHECKING CHANNELS' CONNECTIVITY"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in conn_check: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return

                elif(test_step == "long_run"):
                    log.info("-------------- CHECKING ENC LONG RUN STABILITYY ------------------------- ")
                    info = "--> CHECKING ENC LONG RUN STABILITY "
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    # Function                                                                                                                                                                                 
                    try:
                        self.vd.vref_t_low = 118
                        nloops_local = 50
                        long_run_cal_asic_list_nside = [2]
                        long_run_cal_asic_list_pside = [2]
                        
                        with self._smx_lock:
                            n_length = len(self.smx_l_nside)
                            p_length = len(self.smx_l_pside)
                            
                            valid_nside_indices = [i for i in long_run_cal_asic_list_nside if 0 <= i < n_length]
                            valid_pside_indices = [i for i in long_run_cal_asic_list_pside if 0 <= i < p_length]
                            
                            selected_smx_l_nside = [self.smx_l_nside[i] for i in valid_nside_indices]
                            selected_smx_l_pside = [self.smx_l_pside[i] for i in valid_pside_indices]
                        
                        for n in range(0, nloops_local):
                            if not check_continue():
                                update_test_label("*** TEST EXECUTION STOPPED IN LONG RUN ***")
                                return
                            
                            if selected_smx_l_nside:
                                self.of.read_VDDM_TEMP_FEB(selected_smx_l_nside, 'N', feb_nside)
                            
                            if selected_smx_l_pside:
                                self.of.read_VDDM_TEMP_FEB(selected_smx_l_pside, 'P', feb_pside)
                            
                            info = f"--> RUN {n} of CHECKING ENC LONG RUN STABILITY"
                            log.info(info)
                            self.df.write_log_file(self.vd.module_dir, module_sn, info)
                        
                        info = "<<-- FINISHED ENC LONG RUN STABILITYY"
                        self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    except Exception as e:
                        log.error(f"Tab {tab_id}: Error in long_run: {str(e)}")
                    
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return
                    
                elif(test_step == "set_lv_off"):
                    log.info("-------------- SETTING LV OFF. FINALIZING TESTS ------------------------- ")
                    info = "--> SETTING OFF LV N"
                    self.df.write_log_file(self.vd.module_dir, module_sn, info)
                    pt.powerOff_lv('P')
                    #time.sleep(15)
                    flag_off = 0
                    while(flag_off!= 1):
                        pt.powerOff_lv('N')
                        #time.sleep(15)
                        lv_nside_end = pt.reading_lv('N')
                        if (lv_nside_end[0] == 0 and lv_nside_end[2] == 0):
                            info = "<<-- N-side FEB is OFF. LV_12_END_N: \t{}\t LV_18_END_N: \t{}".format(lv_nside_end[0], lv_nside_end[2])
                            log.info(info)
                            self.df.write_log_file(self.vd.module_dir, module_sn, info)
                            flag_off = 1
                            
                    accumulated_progress += step_percentage
                    update_progress(accumulated_progress)
                    
                    if not check_continue():
                        update_test_label("*** TEST EXECUTION STOPPED ***")
                        return
                                    
                else:
                    if (test_step[0] == '#'):
                        log.info("----------------------- SKIPPING TEST: %s -------------------------- ", test_step)
                    
            update_progress(100)
            update_test_label("")
        
        finally:
            emu_lock.release_emu(emu_id, tab_id)
            self._execute_lock.release()
                    
    def write_observations(self, observations):
        info = "OBSERVATIONS: {}".format(observations)
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
        
    def set_lv_off(self, side_type, volt_type, emu_channel):
        log.info("-------------- SETTING LV OFF. FINALIZING TESTS ------------------------- ")
        info = "--> SETTING OFF LV N"
        result = pt.powerOff_lv(side_type, volt_type, emu_channel)
                    
        info = f"<<-- {side_type}-side {volt_type}V LV OFF result: {result}"
        log.info(info)
        
    def set_lv_on(self, side_type, volt_type, emu_channel):
        log.info("-------------- SETTING LV ON ------------------------- ")
        info = "--> SETTING ON LV N"
        result = pt.powerOn_lv(side_type, volt_type, emu_channel)
                    
        info = f"<<-- {side_type}-side {volt_type}V LV ON result: {result}"
        log.info(info)
