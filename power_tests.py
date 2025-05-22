import time
import sys
import os
import logging
import subprocess
sys.path.append('../../autogen/agwb/python/')
from smx_tester import *
import re

class PowerTests:

    log = logging.getLogger()

    def reading_lv(pol_usr, emu_channel, read_12v=True, read_18v=True):
        # Function to read the voltage and current of the FEB
        # LV mapping                                                                                                                     
        # LV channels vs FEB                                                                                                             
        # u904 ................ 1.2 V LDOs N-side                                                                                        
        # u905 ................ 1.8 V LDOs N-side                                                                                        
        # u906 ................ 1.2 V LDOs P-side                                                                                        
        # u907 ................ 1.8 V LDOs P-side                                                                                        

        pol = pol_usr
        lv_12 = 0.0
        i_12 = 0.0
        lv_18 = 0.0
        i_18 = 0.0
        
        febs_channels = []
        if (emu_channel == "u200" or emu_channel == "EMU_238"):
            febs_channels = ["u400", "u401", "u402", "u403"]
        elif (emu_channel == "u201" or emu_channel == "EMU_213"):
            febs_channels = ["u404", "u405", "u406", "u407"]
        elif (emu_channel == "u202" or emu_channel == "EMU_234"):
            febs_channels = ["u500", "u501", "u502", "u503"]
        else:
            febs_channels = ["u204", "u205", "u206", "u207"]

        if (pol == 'N' or pol == '0'):
            #reading LV in channels u904 and u905
            print("Reading LV for N-side (electrons polarity):")
            #Reading Voltage and current values and writting them in a file
            if read_12v:
               #cmd_12 = "ssh cbm@cbmflib01 ./mpod_lab2021/lab21_mpod02_u204 voltage"
                cmd_12 = f"./../../../lv/mpod_hhlab_2024/lab24_mpod02_{febs_channels[0]} voltage"
                output_12 = subprocess.check_output(cmd_12, shell=True, text=True)
                values_12 = re.findall(r'[0-9]+[.][0-9]+', output_12)
                if len(values_12) == 2:
                    lv_12 = round(float(values_12[0]), 2)
                    i_12 = round(float(values_12[1]), 2)
                    
            if read_18v:        
                #cmd_18 = "ssh cbm@cbmflib01 ./mpod_lab2021/lab21_mpod02_u205 voltage"
                cmd_18 = f"./../../../lv/mpod_hhlab_2024/lab24_mpod02_{febs_channels[1]} voltage"
                output_18 = subprocess.check_output(cmd_18, shell=True, text=True)
                values_18 = re.findall(r'[0-9]+[.][0-9]+', output_18)
                    
                if len(values_18) == 2:
                    lv_18 = round(float(values_18[0]), 2)
                    i_18 = round(float(values_18[1]), 2)
                    
        elif(pol == 'P' or pol == '1'):
            print("Reading LV for P-side (holes polarity):")
            #Reading Voltage and current values and writting them in a file
            if read_12v:
                #cmd_12 = "ssh cbm@cbmflib01 ./mpod_lab2021/lab21_mpod02_u206 voltage"
                cmd_12 = f"./../../../lv/mpod_hhlab_2024/lab24_mpod02_{febs_channels[2]} voltage"
                output_12 = subprocess.check_output(cmd_12, shell=True, text=True)
                values_12 = re.findall(r'[0-9]+[.][0-9]+', output_12)
                if len(values_12) == 2:
                    lv_12 = round(float(values_12[0]), 2)
                    i_12 = round(float(values_12[1]), 2)
                    
            if read_18v:        
                #cmd_18 = "ssh cbm@cbmflib01 ./mpod_lab2021/lab21_mpod02_u207 voltage"
                cmd_18 = f"./../../../lv/mpod_hhlab_2024/lab24_mpod02_{febs_channels[3]} voltage"
                output_18 = subprocess.check_output(cmd_18, shell=True, text=True)
                values_18 = re.findall(r'[0-9]+[.][0-9]+', output_18)
                    
                if len(values_18) == 2:
                    lv_18 = round(float(values_18[0]), 2)
                    i_18 = round(float(values_18[1]), 2)
                    
        else:
            log.error("Please, indicate a polarity for reading the corresponding LV potentials, in the following way:")
            log.error("N or 0 for n-side, 0 for electrons polarity")
            log.error("P or 1 for p-side, 1 for holes polarity")
            sys.exit()
        
        # Print results
        print("LV values: ")
        if (pol == 'N' or pol == '0'):
            print("LV_12_N [V]: " + str(lv_12) + " I_12_N [A]: " + str(i_12))
            print("LV_18_N [V]: " + str(lv_18) + " I_18_N [A]: " + str(i_18))
        else:
            print("LV_12_P [V]: " + str(lv_12) + " I_12_P [A]: " + str(i_12))
            print("LV_18_P [V]: " + str(lv_18) + " I_18_P [A]: " + str(i_18))
            
        return (lv_12, i_12, lv_18, i_18)
    
    def read_one_lv(pol_usr, volt_type, emu_channel):
        febs_channels = []
        
        if emu_channel == "EMU_238":
            febs_channels = ["u400", "u401", "u402", "u403"]
        elif emu_channel == "EMU_213":
            febs_channels = ["u404", "u405", "u406", "u407"]
        elif emu_channel == "EMU_234":
            febs_channels = ["u500", "u501", "u502", "u503"]
        else:
            febs_channels = ["u204", "u205", "u206", "u207"]

        channel_idx = -1
        if pol_usr == 'N' or pol_usr == '0':
            if volt_type == '1.2':
                channel_idx = 0
                print(f"Reading LV 1.2V for N-side using channel {febs_channels[channel_idx]}")
            elif volt_type == '1.8':
                channel_idx = 1
                print(f"Reading LV 1.8V for N-side using channel {febs_channels[channel_idx]}")
        elif pol_usr == 'P' or pol_usr == '1':
            if volt_type == '1.2':
                channel_idx = 2
                print(f"Reading LV 1.2V for P-side using channel {febs_channels[channel_idx]}")
            elif volt_type == '1.8':
                channel_idx = 3
                print(f"Reading LV 1.8V for P-side using channel {febs_channels[channel_idx]}")
        else:
            log.error("Please, indicate a polarity for setting ON the corresponding LV potentials, in the following way:")
            log.error("N or 0 for n-side, 0 for electrons polarity")
            log.error("P or 1 for p-side, 1 for holes polarity")
            return None
        
        if channel_idx == -1:
            log.error(f"Invalid voltage type: {volt_type}. Must be '1.2' or '1.8'")
            return None
        
        cmd = f"./../../../lv/mpod_hhlab_2024/lab24_mpod02_{febs_channels[channel_idx]} voltage"
        output = subprocess.check_output(cmd, shell=True, text=True)
        values = re.findall(r'[0-9]+[.][0-9]+', output)
        if len(values) == 2:
            lv = round(float(values[0]), 2)
            i = round(float(values[1]), 2)
        
        # Print results
        print("LV values: ")
        print("LV [V]: " + str(lv) + " I [A]: " + str(i))
            
        return (lv, i)
    
    def powerOff_lv(pol_usr, volt_type, emu_channel):
        febs_channels = []
        
        if emu_channel == "EMU_238":
            febs_channels = ["u400", "u401", "u402", "u403"]
        elif emu_channel == "EMU_213":
            febs_channels = ["u404", "u405", "u406", "u407"]
        elif emu_channel == "EMU_234":
            febs_channels = ["u500", "u501", "u502", "u503"]
        else:
            febs_channels = ["u204", "u205", "u206", "u207"]

        channel_idx = -1
        if pol_usr == 'N' or pol_usr == '0':
            if volt_type == '1.2':
                channel_idx = 0
                print(f"Turning OFF LV 1.2V for N-side using channel {febs_channels[channel_idx]}")
            elif volt_type == '1.8':
                channel_idx = 1
                print(f"Turning OFF LV 1.8V for N-side using channel {febs_channels[channel_idx]}")
        elif pol_usr == 'P' or pol_usr == '1':
            if volt_type == '1.2':
                channel_idx = 2
                print(f"Turning OFF LV 1.2V for P-side using channel {febs_channels[channel_idx]}")
            elif volt_type == '1.8':
                channel_idx = 3
                print(f"Turning OFF LV 1.8V for P-side using channel {febs_channels[channel_idx]}")
        else:
            log.error("Please, indicate a polarity for setting OFF the corresponding LV potentials, in the following way:")
            log.error("N or 0 for n-side, 0 for electrons polarity")
            log.error("P or 1 for p-side, 1 for holes polarity")
            return None
        
        if channel_idx == -1:
            log.error(f"Invalid voltage type: {volt_type}. Must be '1.2' or '1.8'")
            return None
        
        os.system(f"./../../../lv/mpod_hhlab_2024/lab24_mpod02_{febs_channels[channel_idx]} off")
        
        time.sleep(5)
        
        read_12v = volt_type == '1.2'
        read_18v = volt_type == '1.8'
        
        pol = 'N' if pol_usr in ['N', '0'] else 'P'
        
        lv_values = PowerTests.reading_lv(pol, emu_channel, read_12v, read_18v)
        
        if pol == 'N':
            if volt_type == '1.2':
                print(f"After power off command - LV_12_N [V]: {lv_values[0]} I_12_N [A]: {lv_values[1]}")
            else:
                print(f"After power off command - LV_18_N [V]: {lv_values[2]} I_18_N [A]: {lv_values[3]}")
        else:
            if volt_type == '1.2':
                print(f"After power off command - LV_12_P [V]: {lv_values[0]} I_12_P [A]: {lv_values[1]}")
            else:
                print(f"After power off command - LV_18_P [V]: {lv_values[2]} I_18_P [A]: {lv_values[3]}")
        
        if volt_type == '1.2' and lv_values[0] == 0:
            print(f"Successfully turned OFF {volt_type}V for {pol}-side")
        elif volt_type == '1.8' and lv_values[2] == 0:
            print(f"Successfully turned OFF {volt_type}V for {pol}-side")
        else:
            if volt_type == '1.2':
                log.warning(f"Failed to turn OFF {volt_type}V for {pol}-side. Current value: {lv_values[0]}")
            else:
                log.warning(f"Failed to turn OFF {volt_type}V for {pol}-side. Current value: {lv_values[2]}")

    def powerOn_lv(pol_usr, volt_type, emu_channel):
        febs_channels = []
        
        if emu_channel == "EMU_238":
            febs_channels = ["u400", "u401", "u402", "u403"]
        elif emu_channel == "EMU_213":
            febs_channels = ["u404", "u405", "u406", "u407"]
        elif emu_channel == "EMU_234":
            febs_channels = ["u500", "u501", "u502", "u503"]
        else:
            febs_channels = ["u204", "u205", "u206", "u207"]

        channel_idx = -1
        if pol_usr == 'N' or pol_usr == '0':
            if volt_type == '1.2':
                channel_idx = 0
                print(f"Turning ON LV 1.2V for N-side using channel {febs_channels[channel_idx]}")
            elif volt_type == '1.8':
                channel_idx = 1
                print(f"Turning ON LV 1.8V for N-side using channel {febs_channels[channel_idx]}")
        elif pol_usr == 'P' or pol_usr == '1':
            if volt_type == '1.2':
                channel_idx = 2
                print(f"Turning ON LV 1.2V for P-side using channel {febs_channels[channel_idx]}")
            elif volt_type == '1.8':
                channel_idx = 3
                print(f"Turning ON LV 1.8V for P-side using channel {febs_channels[channel_idx]}")
        else:
            log.error("Please, indicate a polarity for setting ON the corresponding LV potentials, in the following way:")
            log.error("N or 0 for n-side, 0 for electrons polarity")
            log.error("P or 1 for p-side, 1 for holes polarity")
            return None
        
        if channel_idx == -1:
            log.error(f"Invalid voltage type: {volt_type}. Must be '1.2' or '1.8'")
            return None
        
        os.system(f"./../../../lv/mpod_hhlab_2024/lab24_mpod02_{febs_channels[channel_idx]} on")
        
        time.sleep(5)
        
        read_12v = volt_type == '1.2'
        read_18v = volt_type == '1.8'
        
        pol = 'N' if pol_usr in ['N', '0'] else 'P'
        
        lv_values = PowerTests.reading_lv(pol, emu_channel, read_12v, read_18v)
        
        if pol == 'N':
            if volt_type == '1.2':
                print(f"After power on command - LV_12_N [V]: {lv_values[0]} I_12_N [A]: {lv_values[1]}")
            else:
                print(f"After power on command - LV_18_N [V]: {lv_values[2]} I_18_N [A]: {lv_values[3]}")
        else:
            if volt_type == '1.2':
                print(f"After power on command - LV_12_P [V]: {lv_values[0]} I_12_P [A]: {lv_values[1]}")
            else:
                print(f"After power on command - LV_18_P [V]: {lv_values[2]} I_18_P [A]: {lv_values[3]}")
        
        if volt_type == '1.2' and lv_values[0] == 0:
            print(f"Successfully turned ON {volt_type}V for {pol}-side")
        elif volt_type == '1.8' and lv_values[2] == 0:
            print(f"Successfully turned ON {volt_type}V for {pol}-side")
        else:
            if volt_type == '1.2':
                log.warning(f"Failed to turn ON {volt_type}V for {pol}-side. Current value: {lv_values[0]}")
            else:
                log.warning(f"Failed to turn ON {volt_type}V for {pol}-side. Current value: {lv_values[2]}")

    def reading_lv_emu(emu_channel):                                                                                        
        print("Reading EMU values:")
        cmd = f"./../../../lv/mpod_hhlab_2024/lab24_mpod02_{emu_channel} voltage"
        output = subprocess.check_output(cmd, shell=True, text=True)
        
        values = re.findall(r'[0-9]+[.][0-9]+', output)
        
        if len(values) == 2:
            lv_emu = round(float(values[0]), 6)
            i_emu = round(float(values[1]), 6)
        else: 
            lv_emu = 0.000000
            i_emu = 0.000000

        print("EMU values: ", values)
        print("LV_EMU [V]: " + str(lv_emu) + " I_EMU [A]: " +str(i_emu))

        return (lv_emu, i_emu)

    def powerOn_EMU(lv_channel):
        # Function to Turn On EMU. According to the argument, the corresponding side is powered ON
        # Function to read the voltage and current of the FEB
        # LV mapping                                                                                                                     
        # LV channels vs FEB                                                                                                             
        # u800 ................ EMU_213                                                                                        
        # u801 ................ EMU_234                                                                                         
        # u802 ................ EMU_238
            
        log.info("Turning ON LV channel %s for EMU", lv_channel)
        #Reading Voltage and current values and writting them in a file
        command = "./../../../lv/mpod_hhlab_2024/lab24_mpod02_{} on".format(lv_channel)
        os.system(command)
        time.sleep(15)
        command = "./../../../lv/mpod_hhlab_2024/lab24_mpod02_{} status".format(lv_channel)
        os.system(command)

    def powerON_hv(hv_n_channel, hv_p_channel, bias_voltage):
        # Function to Turn ON HV. According to the argument, the corresponding voltage is provided
        # HV mapping                                                                                                                     
        # HV channels vs SETUP                                                                                                             
        # u118 ................ N-side (Positive)    SETUP_0                                                                                        
        # u119 ................ P-side (Negativo)                                                                                        

        # u120 ................ N-side (Positive)    SETUP_1                                                                             
        # u121 ................ P-side (Negativo)
        
        # u118 ................ N-side (Positive)    SETUP_2                                                                                
        # u119 ................ P-side (Negativo)                                                                                        

        # Initizalizing the HV channels. Setting Output voltage = 0
        command = "ssh cbm@cbmflib01 snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 10.203.0.64 outputVoltage.{} F {}".format(hv_n_channel, 0)
        os.system(command)
        command = "ssh cbm@cbmflib01 snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 10.203.0.64 outputVoltage.{} F {}".format(hv_p_channel, 0)
        os.system(command)
        # Turning on the channels:
        command = "ssh cbm@cbmflib01 snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 10.203.0.64 outputSwitch.{} i 1".format(hv_n_channel)
        os.system(command)
        command = "ssh cbm@cbmflib01 snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 10.203.0.64 outputSwitch.{} i 1".format(hv_p_channel)
        os.system(command)
        #Ramping up the HV, up to the bias_voltage.
        #Symmetric mode:
        for hv in range(0, bias_voltage, 5):
            # n-side
            command = "ssh cbm@cbmflib01 snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 10.203.0.64 outputVoltage.{} F {}".format(hv_n_channel, hv)
            os.system(command)
            # p-side
            hv *=(-1)
            command = "ssh cbm@cbmflib01 snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 10.203.0.64 outputVoltage.{} F {}".format(hv_p_channel, hv)
            os.system(command)
            time.sleep(10)
        #reading HV currents @ the biasing voltage
        command = "ssh cbm@cbmflib01 snmpget -v 2c -m +WIENER-CRATE-MIB -c public 10.203.0.64 outputMeasurementCurrent.{} | grep -Eo '[0-9]+([.][0-9]+)'".format(hv_n_channel)
        hv_i_nside = subprocess.check_output(command, shell = True)
        hv_i_nside = hv_i_nside.decode("utf-8").strip()
        hv_i_nside = 1000000*float(hv_i_nside)
        command = "ssh cbm@cbmflib01 snmpget -v 2c -m +WIENER-CRATE-MIB -c public 10.203.0.64 outputMeasurementCurrent.{} | grep -Eo '[0-9]+([.][0-9]+)'".format(hv_p_channel)
        hv_i_pside = subprocess.check_output(command, shell = True)
        hv_i_pside = hv_i_pside.decode("utf-8").strip()
        hv_i_pside = 1000000*float(hv_i_pside)
        
        log.info("N-side: {} uA".format(hv_i_nside))
        log.info("P-side: {} uA".format(hv_i_pside))

        return (hv_i_nside, hv_i_pside) 
   
    def powerOff_hv(hv_n_channel, hv_p_channel):
        # Function to Turn ON HV. According to the argument, the corresponding voltage is provided
        # HV mapping                                                                                                                     
        # HV channels vs SETUP                                                                                                             
        # u118 ................ N-side (Positive)    SETUP_0                                                                                        
        # u119 ................ P-side (Negativo)                                                                                        

        # u120 ................ N-side (Positive)    SETUP_1                                                                             
        # u121 ................ P-side (Negativo)
        
        # u118 ................ N-side (Positive)    SETUP_2                                                                                
        # u119 ................ P-side (Negativo)                                                                                        
        thr_v_off = 5                                # Voltage threshold to consider a channel off
        
        # Turning off the channels:
        command = "ssh cbm@cbmflib01 snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 10.203.0.64 outputSwitch.{} i 0".format(hv_n_channel)
        os.system(command)
        command = "ssh cbm@cbmflib01 snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 10.203.0.64 outputSwitch.{} i 0".format(hv_p_channel)
        os.system(command)
        time.sleep(180)
        
        # reading voltage after OFF 
        command = "ssh cbm@cbmflib01 snmpget -v 2c -m +WIENER-CRATE-MIB -c public 10.203.0.64 outputMeasurementTerminalVoltage.{} | grep -Eo '[0-9]+([.][0-9]+)'".format(hv_n_channel)
        hv_v_nside = subprocess.check_output(command, shell = True)
        hv_v_nside = hv_v_nside.decode("utf-8").strip()
        hv_v_nside = float(hv_v_nside)
        command = "ssh cbm@cbmflib01 snmpget -v 2c -m +WIENER-CRATE-MIB -c public 10.203.0.64 outputMeasurementTerminalVoltage.{} | grep -Eo '[0-9]+([.][0-9]+)'".format(hv_p_channel)
        hv_v_pside = subprocess.check_output(command, shell = True)
        hv_v_pside = hv_v_pside.decode("utf-8").strip()
        hv_v_pside = float(hv_v_pside)
        
        if (hv_v_nside < thr_v_off and hv_v_pside < thr_v_off):
            return True
        else:
            return False
