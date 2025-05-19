import sys
import logging
from datetime import datetime
sys.path.append('../../autogen/agwb/python/')
from smx_tester import *
#from directory_files import self.vd.module_dir, self.df.write_data_file, self.df.write_log_file, self.vd.module_sn_tmp, self.vd.module_sn, self.vd.feb_type_sw_A, self.vd.feb_type_sw_B
from directory_files import DirectoryFiles

class OperatingFunctions: 
    
    def __init__(self, vd):
        self.vd = vd
        self.df=DirectoryFiles(self.vd)

    log = logging.getLogger()

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

              
    def read_VDDM_TEMP_FEB(self, smx_l_side, pol, feb_type):
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
        self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp,header_line)

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)

        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                if (smx.address == asic_sw):
                    asic_vddm = smx.read_vddm()
                    #asic_vddm_src = smx.read_diag("Vddm")
                    asic_temp = smx.read_temp()
                    #asic_temp_src = smx.read_diag("Temp")
                    if pol == "N" or pol == "0":
                        self.vd.stored_vddm_values["N"].append(asic_vddm[1])
                        self.vd.stored_temp_values["N"].append(asic_temp[1])
                    else:
                        self.vd.stored_vddm_values["P"].append(asic_vddm[1])
                        self.vd.stored_temp_values["P"].append(asic_temp[1])
                    info = "{} \t\t {} \t\t {} \t\t\t {} \t {:.1f} \t\t\t {:.1f} \t {:.1f}".format(feb_type, pol_str, smx.address, asic_vddm[0], asic_vddm[1], asic_temp[0], asic_temp[1])
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp,info)
                    log.info(info)
                else:
                    pass
                
        log.info(f"VDDM VALUES AFTER {pol} READING:")
        log.info(f"Stored N-side values: {self.vd.stored_vddm_values['N']}")
        log.info(f"Stored P-side values: {self.vd.stored_vddm_values['P']}")
                
        return 0
    
    def load_STD_Config(self, smx_l_side, pol, feb_type):
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

        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                if (smx.address == asic_sw):
                    header_line  = "--> SETTING STANDARD CONFIGURATION for ASIC with HW address {} and polarity {}".format(smx.address,pol_str)
                    log.info(header_line)
                    smx.write_def_ana_reg(smx.address, pol_calib )
                    smx.read_reg_all(compFlag = False)
                else:
                    pass
        return 0
         
    def set_Trim_default(self, smx_l_side, pol, feb_type, cal_asic_list):
        feb_type_sw = []
        if (pol == 'N' or pol == '0'):
            pol_str = 'N-side'
        else:
            pol_str = 'P-side'

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)

        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    header_line  = "--> SETTING DEFAULT TRIM for ASIC with HW address {} and polarity {}".format(smx.address, pol_str)
                    log.info(header_line)
                    smx.set_trim_default(128,36)
                else:
                    #info = "--> NO SETTING DEFAULT TRIM for ASIC with HW ADDRESS {} in {}".format(asic_hw_addr, pol_str)
                    #log.info(info)
                    pass
        return 0
     
    def scan_VrefP_N_Thr2glb(self, smx_l_side, pol, feb_type, cal_asic_list, npulses = 100, test_ch = 64, amp_cal_min = 30, amp_cal_max = 247, amp_cal_fast = 30, vref_t = 118):
        smx_cnt = 0
        feb_type_sw = []
        #cal_set_asic = [0 for n_asics in len(smx_l_side)[0 for vref in range(3)]]
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

        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    header_line  = "--> SCANNING VREF_P,N & THR2_GLB for ASIC with HW address {} and polarity {}".format(smx.address, pol_str)
                    log.info(header_line)
                    cal_set_asic.append(smx.vrefpn_scan(pol_calib, test_ch, npulses, amp_cal_min, amp_cal_max, amp_cal_fast, vref_t))
                else:
                    #info = "--> NO SCANNING VREF_P/N & THR2_GLB FOR ASIC with HW ADDRESS {} in {}".format(asic_hw_addr, pol_str)
                    #log.info(info)
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
    def calib_FEB(self, smx_l_side, trim_dir, pol, feb_type, cal_asic_list, npulses = 40, amp_cal_min = 30, amp_cal_max = 247, amp_cal_fast = 30, much_mode_on = 0):
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
        # definition of the final trim array
        trim_final = [[0 for d in range(32)] for ch in range(128)]    
        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)

        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
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
                    smx.get_trim_adc_SA(pol_calib, trim_final, 40, amp_cal_min, amp_cal_max, much_mode_on)
                    #smx.get_trim_adc(pol_calib, trim_final, 40, amp_cal_min, amp_cal_max,vref_t,  much_mode_on)
                    smx.get_trim_fast(pol_calib, trim_final, npulses, amp_cal_fast, much_mode_on)
                    # Writing calibration file
                    smx.write_trim_file(filename_trim, pol_calib, trim_final, amp_cal_min, amp_cal_max, amp_cal_fast, much_mode_on)
                    info = "CAL_ASIC_HW_ADDR_{}: {}.txt".format(asic_hw_addr,filename_str)
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    self.df.write_log_file(self.vd.module_dir, self.vd.module_sn, info)            
                else:
                    #info = "SKIP_ASIC_HW_ADDR_{}".format(asic_hw_addr)
                    #log.info(info)
                    #self.df.write_log_file(self.vd.module_dir, self.vd.module_sn, info)
                    pass
        return 0

    def set_trim_calib(self, smx_l_side, trim_dir, pol, feb_type, cal_asic_list, much_mode_on = 0):
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

        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    asic_hw_addr = smx.address
                    # Setting the TRIM calibration values                                                                                                                  
                    info = "--> SETTING TRIM CALIBRATION VALUES FOR ASIC with HW ADDRESS {} in {}".format(asic_hw_addr, pol_str)
                    log.info(info)
                    # Elements for the trim file
                    asic_id_str = smx.read_efuse_str()
                    smx.set_trim(trim_dir, pol_calib, asic_id_str)
                else:
                    pass
        return 0

    def check_trim(self, smx_l_side, pscan_dir, pol, feb_type, cal_asic_list, disc_list = [5,10,16,24,30,31], vp_min = 0, vp_max = 255, vp_step = 1, npulses = 100):
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

        if (feb_type[-2:-1] == "A"):
            feb_type_sw.extend(self.vd.feb_type_sw_A)
        else:
            feb_type_sw.extend(self.vd.feb_type_sw_B)

        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                asic_hw_addr = smx.address
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    # Checking ENC and calibration results for an ASIC                                                                                                     
                    info = "PSCAN_ASIC_HW_ADDR_{}: {}".format(asic_hw_addr, pol_str)
                    log.info(info)
                    # Elements for the pscan file                                                                                                                          
                    asic_id_str = smx.read_efuse_str()
                    pscan_filename = smx.check_trim_red(pscan_dir, pol_calib, asic_id_str, disc_list, vp_min, vp_max, vp_step, npulses)
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

    def connection_check(self, smx_l_side, conn_check_dir, pol, feb_type, cal_asic_list, nloops = 5, vref_t = 108):
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

        log.info("FEB type: {}".format(feb_type[-2:-1]))
        for asic_sw in feb_type_sw:
            for smx in smx_l_side:
                #asic_hw_addr = smx.address
                if ((smx.address == asic_sw) and (smx.address in cal_asic_list)):
                    # Checking ENC and calibration results for an ASIC     
                    info = "CONN-CHECK_ASIC_HW_ADDR_{}: {}".format(smx.address, pol_str)
                    log.info(info)
                    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                    self.df.write_log_file(self.vd.module_dir, self.vd.module_sn, info)
                    # Elements for the connection check file                                                                                                                     
                    #asic_id_str = smx.read_efuse_str()
                    smx.connection_check(conn_check_dir, pol_calib, nloops, vref_t)
                else:
                    pass
                #    info = "SKIP_CONN_ASIC_HW_ADDR_{}".format(asic_hw_addr)
                #    log.info(info)
                #    self.df.write_data_file(self.vd.module_dir, self.vd.module_sn_tmp, info)
                #    self.df.write_log_file(self.vd.module_dir, self.vd.module_sn, info)
        return 0