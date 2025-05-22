import sys
import logging
import uhal
sys.path.append('../../autogen/agwb/python/')
# sys.path.append('../../agwb/')
import agwb
from smx_tester import *
import msts_defs as smc
import time
import traceback
from PyQt5.QtCore import QCoreApplication
import threading
import ctypes

class ConfigTests:

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

    def general_sync(self, emu, active_downlinks=None, check_continue=None):
        try:
            # Validate and ensure emu is a string
            if not isinstance(emu, str):
                self.log.error(f"emu parameter must be a string, got {type(emu)}: {emu}")
                return None
                
            # Validate active_downlinks parameter
            if active_downlinks is None:
                active_downlinks = [1, 2]
            elif not isinstance(active_downlinks, list):
                self.log.error(f"active_downlinks must be a list, got {type(active_downlinks)}: {active_downlinks}")
                return None
                
            self.log.info(f"Starting general_sync with emu={emu}, active_downlinks={active_downlinks}")
            
            if check_continue and not check_continue():
                self.log.info("general_sync aborted before initialization")
                return None
                
            # Open xml file with list of EMU devices
            manager = uhal.ConnectionManager("file://devices.xml")
            
            # Arrays to organize setup elements (FEBs)
            setup_elements = []
            emu_elements = []

            link_scan = True
            device_scan = True
            link_sync = True

            if check_continue and not check_continue():
                self.log.info("general_sync aborted before IPbusInterface initialization")
                return None
                
            try:
                # Initialize the interface with proper parameters
                ipbus_interface = IPbusInterface(manager, emu)
                agwb_top = agwb.top(ipbus_interface, 0)
                smx_tester = SmxTester(agwb_top, CLK_160)
            except Exception as e:
                self.log.error(f"Error initializing interfaces: {str(e)}")
                return None
            
            if check_continue and not check_continue():
                self.log.info("general_sync aborted before scan_setup")
                return None
                
            # Use run_with_timeout_and_interrupt for potentially long operations
            if hasattr(self, 'run_with_timeout_and_interrupt'):
                self.log.info(f"Running scan_setup with timeout and interrupt")
                setup_elements_tmp = self.run_with_timeout_and_interrupt(
                    smx_tester.scan_setup,
                    check_continue=check_continue,
                    timeout=None
                )
                
                if setup_elements_tmp is None:
                    if check_continue and not check_continue():
                        self.log.info("scan_setup was interrupted")
                        return None
                    else:
                        self.log.error("scan_setup failed")
                        return None
            else:
                try:
                    setup_elements_tmp = smx_tester.scan_setup()
                except Exception as e:
                    self.log.error(f"Error in scan_setup: {str(e)}")
                    return None
                
            self.log.info("setup_elements_tmp: %d", len(setup_elements_tmp))
            setup_elements.extend(setup_elements_tmp)
            emu_elements.extend([emu for i in range(len(setup_elements_tmp))])

            if check_continue and not check_continue():
                self.log.info("general_sync aborted before setup element processing")
                return None

            remove_list_01 = []
            remove_list_23 = []
            
            # Process and filter setup elements based on active_downlinks
            self.log.info(f"Filtering setup elements with active_downlinks={active_downlinks}")
            for se in list(setup_elements):
                self.log.info(f"SE:\t{se.downlink}\t\t{se.uplinks}  ({len(se.uplinks)})")
                if se.downlink not in active_downlinks:
                    setup_elements.remove(se)
                    self.log.info(f"Remove setup element for downlink no. {se.downlink} with uplinks {se.uplinks}")

            for se in setup_elements:
                self.log.info(f"Cleaned - SE:\t{se.downlink}\t\t{se.uplinks}  ({len(se.uplinks)})")

                for uplink in se.uplinks:
                    if se.downlink == 0 or se.downlink == 1:
                        if uplink > 15:
                            remove_list_01.append(uplink)
                            self.log.info("Uplink appended to remove list: {}".format(uplink))
                    else:
                        if uplink < 16:
                            remove_list_23.append(uplink)
                            self.log.info("Uplink appended to remove list: {}".format(uplink))
                if se.downlink == 0 or se.downlink == 1:
                    se.uplinks = [i for i in se.uplinks if i not in remove_list_01]
                else:
                    se.uplinks = [i for i in se.uplinks if i not in remove_list_23]
                self.log.info(f"Final List UPLINKS SE:\t{se.downlink}\t\t{se.uplinks}  ({len(se.uplinks)})")

            if check_continue and not check_continue():
                self.log.info("general_sync aborted before link scan")
                return None
                
            # Temporary workaround becase there are no independent elink clocks.
            # setup_elements = [setup_elements[0]]
            # smx_tester.elinks.disable_downlink_clock(4)

            if link_scan:
                for se in setup_elements:
                    if check_continue and not check_continue():
                        self.log.info(f"general_sync aborted during link scan at downlink {se.downlink}")
                        return None
                        
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        self.log.info(f"Running characterize_clock_phase with timeout and interrupt for downlink {se.downlink}")
                        result = self.run_with_timeout_and_interrupt(
                            se.characterize_clock_phase,
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            self.log.info(f"characterize_clock_phase was interrupted for downlink {se.downlink}")
                            return None
                    else:
                        se.characterize_clock_phase()
                        
                    self.log.info(f"post char clk phase\n {se}")
                    
                    if check_continue and not check_continue():
                        self.log.info(f"general_sync aborted after characterize_clock_phase for downlink {se.downlink}")
                        return None
                        
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        self.log.info(f"Running initialize_clock_phase with timeout and interrupt for downlink {se.downlink}")
                        result = self.run_with_timeout_and_interrupt(
                            se.initialize_clock_phase,
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            self.log.info(f"initialize_clock_phase was interrupted for downlink {se.downlink}")
                            return None
                    else:
                        se.initialize_clock_phase()
                        
                    self.log.info(f"post set\n {se}")

                for se in setup_elements:
                    if check_continue and not check_continue():
                        self.log.info(f"general_sync aborted during data phase scan at downlink {se.downlink}")
                        return None
                        
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        self.log.info(f"Running characterize_data_phases with timeout and interrupt for downlink {se.downlink}")
                        result = self.run_with_timeout_and_interrupt(
                            se.characterize_data_phases,
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            self.log.info(f"characterize_data_phases was interrupted for downlink {se.downlink}")
                            return None
                    else:
                        se.characterize_data_phases()
                        
                    self.log.info(f"post char data phase\n {se}")
                    
                    if check_continue and not check_continue():
                        self.log.info(f"general_sync aborted after characterize_data_phases for downlink {se.downlink}")
                        return None
                        
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        self.log.info(f"Running initialize_data_phases with timeout and interrupt for downlink {se.downlink}")
                        result = self.run_with_timeout_and_interrupt(
                            se.initialize_data_phases,
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            self.log.info(f"initialize_data_phases was interrupted for downlink {se.downlink}")
                            return None
                    else:
                        se.initialize_data_phases()
                        
                    self.log.info(f"post set\n {se}")

            if check_continue and not check_continue():
                self.log.info("general_sync aborted before device scan")
                return None

            if device_scan:        
                for se in setup_elements:
                    if check_continue and not check_continue():
                        self.log.info(f"general_sync aborted during device scan at downlink {se.downlink}")
                        return None
                        
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        self.log.info(f"Running scan_smx_asics_map with timeout and interrupt for downlink {se.downlink}")
                        result = self.run_with_timeout_and_interrupt(
                            se.scan_smx_asics_map,
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            self.log.info(f"scan_smx_asics_map was interrupted for downlink {se.downlink}")
                            return None
                    else:
                        se.scan_smx_asics_map()
                        
                    self.log.info(f"post scan map|n {se}")

            if check_continue and not check_continue():
                self.log.info("general_sync aborted before link sync")
                return None

            if link_sync:        
                for se in setup_elements:
                    if check_continue and not check_continue():
                        self.log.info(f"general_sync aborted during elink synchronization at downlink {se.downlink}")
                        return None
                        
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        self.log.info(f"Running synchronize_elink with timeout and interrupt for downlink {se.downlink}")
                        result = self.run_with_timeout_and_interrupt(
                            se.synchronize_elink,
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            self.log.info(f"synchronize_elink was interrupted for downlink {se.downlink}")
                            return None
                    else:
                        se.synchronize_elink()

                for se in setup_elements:
                    if check_continue and not check_continue():
                        self.log.info(f"general_sync aborted during write masks at downlink {se.downlink}")
                        return None
                        
                    if hasattr(self, 'run_with_timeout_and_interrupt'):
                        self.log.info(f"Running write_smx_elink_masks with timeout and interrupt for downlink {se.downlink}")
                        result = self.run_with_timeout_and_interrupt(
                            se.write_smx_elink_masks,
                            check_continue=check_continue,
                            timeout=None
                        )
                        
                        if result is None and check_continue and not check_continue():
                            self.log.info(f"write_smx_elink_masks was interrupted for downlink {se.downlink}")
                            return None
                    else:
                        se.write_smx_elink_masks()

            if check_continue and not check_continue():
                self.log.info("general_sync aborted before smx creation")
                return None

            smxes = []
            for se, emu_id in zip(setup_elements, emu_elements):
                if check_continue and not check_continue():
                    self.log.info(f"general_sync aborted during smx creation for downlink {se.downlink}")
                    return None
                    
                if hasattr(self, 'run_with_timeout_and_interrupt'):
                    self.log.info(f"Running smxes_from_setup_element with timeout and interrupt for downlink {se.downlink}")
                    smxes_tmp = self.run_with_timeout_and_interrupt(
                        smxes_from_setup_element,
                        args=(se,),
                        check_continue=check_continue,
                        timeout=None
                    )
                    
                    if smxes_tmp is None and check_continue and not check_continue():
                        self.log.info(f"smxes_from_setup_element was interrupted for downlink {se.downlink}")
                        return None
                else:
                    smxes_tmp = smxes_from_setup_element(se)
                    
                self.log.info("smxes_tmp: %d", len(smxes_tmp))
                try:
                    # Extract the numeric part from the EMU string (e.g., 234 from "EMU_234")
                    if isinstance(emu_id, str) and emu_id.startswith("EMU_"):
                        rob_value = int(emu_id[4:])
                    else:
                        # Fallback in case the expected format isn't found
                        self.log.warning(f"Unexpected EMU format: {emu_id}, using as is")
                        rob_value = emu_id
                        
                    for smx in smxes_tmp:
                        smx.rob = rob_value
                except (ValueError, IndexError) as e:
                    self.log.error(f"Error parsing EMU ID {emu_id}: {str(e)}")
                    # Continue with the process even if EMU ID parsing fails
                    
                smxes.extend(smxes_tmp)
        
            self.log.info("Number of setup elements: %d", len(setup_elements))
            self.log.info("Number of smx: %d", len(smxes))
            self.log.info("")
            return smxes
            
        except Exception as e:
            self.log.error(f"Error in general_sync: {str(e)}")
            import traceback
            self.log.error(traceback.format_exc())
            return None
    
    def scanning_asics(self, smx_l):
        # Function to find the number of ASICs per dwnlink or devices    
        n_asics = 0
        p_asics = 0
        for smx in smx_l:
            log.info("Asic (emu %d   downlink %d   hw_addr %d): ", smx.rob, smx.downlink, smx.address)
            smx.func_to_reg(smc.R_ACT)
            smx.write_reg_all()
            smx.read_reg_all(compFlag = False)
            if (smx.downlink == 1 or smx.downlink == 3):
                n_asics+=1
            else:
                p_asics+=1       
        return (n_asics, p_asics)
