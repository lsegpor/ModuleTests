import sys
import logging
sys.path.append('../../autogen/agwb/python/')
from smx_tester import *

class VariablesDefinition:
    
    def __init__(self, df):
        self.df = df
        self.module_sn = ""
        self.ladder_sn = ""
        self.module_dir = ""
        self.calibration_data_path = ""
        self.module_sn_tmp = ""
        self.emu = ""
        self.test_list = []
        self.observations = ""
        self.cal_asic_list_nside = []
        self.cal_asic_list_pside = []
        self.initialized = True
        self.emu_channel = ""
        self.stored_vddm_values = { "N": [], "P": [] }
        self.stored_temp_values = { "N": [], "P": [] }
        self.measured_asic_addresses = { "N": [], "P": [] }
        self.log = logging.getLogger()

    #["EMU_213"]     # List of EMU boards used during the test
    #emu_list = ["EMU_236"]
    # Ladder name or module path
    # module_path  = "ladder_files"
    
    def setValues(self, module, emu, module_dir, calib):
        self.module_sn, self.ladder_sn = self.df.read_moduleId(module)
        self.module_dir = str(module_dir) + "/" + str(self.ladder_sn) + "/" + str(self.module_sn)
        self.module_sn_tmp = self.df.initWorkingDirectory(self.module_dir, self.module_sn)
        self.calibration_data_path = str(calib)
        self.emu = emu
        
        if emu == "EMU_238":
            self.emu_channel = "u200"
        elif emu == "EMU_213":
            self.emu_channel = "u201"
        elif emu == "EMU_234":
            self.emu_channel = "u202"
        else:
            self.emu_channel = "u907"
        
    def set_observations(self, observations):
        self.observations = observations
    
    def selected_asics(self, asic_nside_values, asic_pside_values):
        self.cal_asic_list_nside = []
        self.cal_asic_list_pside = []
        for i, is_selected in enumerate(asic_nside_values):
            if is_selected == 1:
                self.cal_asic_list_nside.append(i)

        for i, is_selected in enumerate(asic_pside_values):
            if is_selected == 1:
                self.cal_asic_list_pside.append(i)

    # List of ASICs HW address to be tested in case the 
    #cal_asic_list = [0, 1, 2, 3, 4, 5, 6, 7]
    #cal_asic_list_nside = [0, 1, 2, 3, 4, 5, 6, 7]
    #cal_asic_list_nside = []
    #cal_asic_list_pside = [0, 1, 2, 3, 4, 5, 6, 7]
    #cal_asic_list_pside = [4,5,6,7]
    #smx_l_short = smx_l[0:1]
    #smx_cnt = 0
    hv_n_channel = 'u118'
    hv_p_channel = 'u119'
    bias_voltage = 80                                # Symmetric bias voltage. +/- 75V 


    # Operating variables GetVrefs paramaters
    npulses = 100
    test_ch = 64
    # Global variables used everywhere
    feb_type_sw_B = [1, 0, 3, 2, 5, 4, 7, 6]
    feb_type_sw_A = [7, 6, 5, 4, 3, 2, 1, 0]
    # Global variables, used only during the get_trim function
    # Calibration settings:  ADC Disc 30 -> amp_cal_min, ADC Disc 0 -> amp_cal_max, FAST Disc -> amp_cal_fast
    amp_cal_min = 30
    amp_cal_max = 247
    amp_cal_fast = 30
    vref_t = 118                    # Vrf_T value  = 54 in the largest VRef_T range. To detemrine calib par and to calibrate ADC
    # Check Trim Parameters
    disc_list = [5,10,16,24,30,31]
    #disc_list = [24,25,27,29,30,31]
    vp_min = 0
    #vp_max = 100
    vp_max = 255
    vp_step = 1
    # Connection check Parameters
    vref_t_low = 102                # Low ADC threshold to count noise hits in the discriminators 
    nloops = 5                      # Number of loops to count noise hits in discriminators
            
    #Lists of subsequences for module tests
    # ------------------------------------------------------------------------------------------------------------------
    # Possible test sequences.

    test_list_init = ["power_on_emu", "read_emu", "full_sync","#turn_hv_on", "read_lv_bc"]
    test_list_comm = ["std_config","read_asic_id","set_trim_default", "read_lv_ac", "check_vddm_temp"]
    test_list_calib = ["set_trim_default", "get_vrefs", "set_calib_par", "get_trim", "read_lv_ac", "check_vddm_temp"]
    test_list_check = ["set_trim_calib", "check_trim", "read_lv_ac", "check_vddm_temp", "#turn_hv_off"]
    test_list_c_check = ["#set_trim_calib", "read_lv_ac", "check_vddm_temp", "#turn_hv_off","conn_check"]
    test_list_stress = ["#reg_config_stress", "#iv_meas", "#set_mbias", "long_run"]
    #test_list_rdata = []
    #test_list_sysoff = ["#set_lv_off", "#set_hv_off"]
    
    def selected_tests(self, tests):
        
        self.test_list = []
        
        self.test_list.extend(self.test_list_init)
        
        test_options = [
            self.test_list_comm,
            self.test_list_calib,
            self.test_list_check,
            self.test_list_c_check,
            self.test_list_stress
        ]
            
        for i, is_selected in enumerate(tests):
            if is_selected == 1:
                self.test_list.extend(test_options[i])

    # Add the list of test to perfrom
    #test_list.extend(test_list_init)
    #test_list.extend(test_list_comm)
    #test_list.extend(test_list_calib)
    #test_list.extend(test_list_check)
    #test_list.extend(test_list_stress)
