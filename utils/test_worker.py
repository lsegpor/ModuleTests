from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QCoreApplication
import os
import psutil
import time
import sys
import traceback

class TestWorker(QObject):
    progressSignal = pyqtSignal(int)
    infoSignal = pyqtSignal(str)
    logSignal = pyqtSignal(str, str)
    emuSignal = pyqtSignal(float, float)
    vddmSignal = pyqtSignal(list, list, list, list)
    tempSignal = pyqtSignal(list, list, list, list)
    febnsideSignal = pyqtSignal(float, float, float, float, str)
    febpsideSignal = pyqtSignal(float, float, float, float, str)
    calibSignal = pyqtSignal(str)
    savepathSignal = pyqtSignal(str)
    efuseidWarningSignal = pyqtSignal(list, list, str, str)
    uplinksWarningSignal = pyqtSignal(int)
    finishedSignal = pyqtSignal(bool, str)
    
    def __init__(self, main_logic, params, tab_num):
        super().__init__()
        self.main = main_logic
        self.params = params
        self.tab_num = tab_num
        self.stop_requested = False
        self.stop_timer = None
        self.subprocess_list = []
        self.pid_file = f"/tmp/module_test_tab_{tab_num}.pid"
        self.step_times = None
        self.current_test_list = None
        
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
            
    def __del__(self):
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except:
            pass
        
    def log_message(self, message, level="INFO"):
        self.logSignal.emit(message, level)
        
    def _kill_subprocesses(self):
        try:
            for process in self.subprocess_list:
                if process and hasattr(process, 'poll') and process.poll() is None:
                    try:
                        process.terminate()
                        time.sleep(0.1)
                        if process.poll() is None:
                            process.kill()
                    except:
                        pass
            
            current_pid = os.getpid()
            current_process = psutil.Process(current_pid)
            
            children = current_process.children(recursive=True)
            
            for child in children:
                try:
                    child.terminate()
                except:
                    pass
                    
            gone, still_alive = psutil.wait_procs(children, timeout=0.5)
            
            for child in still_alive:
                try:
                    child.kill()
                except:
                    pass
        except Exception as e:
            self.log_message(f"Tab {self.tab_num}: Error stopping processes: {str(e)}", "ERROR")
    
    def _force_finish(self):
        self.finishedSignal.emit(False, "Tests stopped by user")
        
    def request_stop(self):
        self.stop_requested = True
        self.infoSignal.emit("*** TEST EXECUTION STOPPED ***")
        
        self._kill_subprocesses()
        
        self.stop_timer = QTimer()
        self.stop_timer.setSingleShot(True)
        self.stop_timer.timeout.connect(self._force_finish)
        self.stop_timer.start(100)
        
    def update_granular_progress(self, base_progress, current_step, total_steps, test_name="get_vrefs"):
        if self.stop_requested:
            return
        
        if not self.step_times or not self.current_test_list:
            self.progressSignal.emit(int(base_progress))
            return
        
        try:
            test_duration = self.step_times.get(test_name, 250)
            total_time = sum(self.step_times.get(step, 5) for step in self.current_test_list)
            test_percentage = (test_duration / total_time) * 100
            
            if total_steps > 0:
                internal_progress = (current_step / total_steps) * test_percentage
            else:
                internal_progress = 0
            
            total_progress = base_progress + internal_progress
            
            print(f"Granular Progress [{test_name}] - Base: {base_progress:.1f}%, "
                f"Current: {current_step}/{total_steps}, "
                f"Internal: {internal_progress:.1f}%, "
                f"Total: {total_progress:.1f}%")
            
            self.progressSignal.emit(int(min(total_progress, 100)))
            
            if hasattr(self, 'detailedProgressSignal'):
                self.detailedProgressSignal.emit({
                    'test_name': test_name,
                    'current_step': current_step,
                    'total_steps': total_steps,
                    'base_progress': base_progress,
                    'total_progress': total_progress
                })
        
        except Exception as e:
            self.log_message(f"Tab {self.tab_num}: Error calculating granular progress: {e}", "ERROR")
            self.progressSignal.emit(int(base_progress))
    
    def set_test_info(self, step_times, test_list):
        self.step_times = step_times
        self.current_test_list = test_list
        self.log_message(f"Tab {self.tab_num}: Test info set - step_times keys: {list(step_times.keys())}, test_list: {test_list}", "INFO")
        
    def run(self): 
        from emu_ladder.python.module_tests.utils.console_widget import UniversalOutputCapture
    
        capture = UniversalOutputCapture(self.tab_num, self.logSignal)
        
        with capture:
            try:
                self.log_message(f"Starting test execution for Setup {self.tab_num}", "INFO")
                
                if self.stop_requested:
                    self.finishedSignal.emit(False, "Tests stopped by user")
                    return
                
                (module, sn_nside, sn_pside, slc_nside, slc_pside, emu, test_values, s_size, s_qgrade,
                asic_nside_values, asic_pside_values, suid, lv_nside_12_checked, lv_pside_12_checked,
                lv_nside_18_checked, lv_pside_18_checked, module_files, calib_path) = self.params
                
                self.log_message(f"Module: {module}, EMU: {emu}", "INFO")
                self.log_message(f"FEB N-side: {sn_nside}, FEB P-side: {sn_pside}", "INFO")
                
                def check_continue():
                    QCoreApplication.processEvents()
                    return not self.stop_requested
                
                def update_progress(value):
                    if self.stop_requested:
                        return
                    self.progressSignal.emit(value)
                    self.log_message(f"Progress: {value:.1f}%", "DEBUG")
                    
                def update_test_label(text):
                    if self.stop_requested:
                        return
                    self.infoSignal.emit(text)
                    self.log_message(text, "INFO")
                    
                def update_emu_values(v_value, i_value):
                    if self.stop_requested:
                        return
                    self.emuSignal.emit(v_value, i_value)
                    self.log_message(f"EMU Values - V: {v_value}, I: {i_value}", "DEBUG")
                    
                def update_vddm(n_idx, n_val, p_idx, p_val):
                    if self.stop_requested:
                        return
                    self.vddmSignal.emit(n_idx, n_val, p_idx, p_val)
                    
                def update_temp(n_idx, n_val, p_idx, p_val):
                    if self.stop_requested:
                        return
                    self.tempSignal.emit(n_idx, n_val, p_idx, p_val)
                    
                def efuse_warning(efuse_str, efuse_int, pol, feb):
                    if self.stop_requested:
                        return
                    self.efuseidWarningSignal.emit(efuse_str, efuse_int, pol, feb)

                def uplinks_warning(length):
                    if self.stop_requested:
                        return
                    self.uplinksWarningSignal.emit(length)
                    
                def uplinks_warning(length):
                    if self.stop_requested:
                        return
                    self.uplinksWarningSignal.emit(length)
                    
                def update_feb_nside(v12_val, i12_val, v18_val, i18_val, test):
                    if self.stop_requested:
                        return
                    self.febnsideSignal.emit(v12_val, i12_val, v18_val, i18_val, test)
                    
                def update_feb_pside(v12_val, i12_val, v18_val, i18_val, test):
                    if self.stop_requested:
                        return
                    self.febpsideSignal.emit(v12_val, i12_val, v18_val, i18_val, test)
                    
                def update_calib_path(text):
                    if self.stop_requested:
                        return
                    self.calibSignal.emit(text)
                    self.log_message(f"Calibration path updated: {text}", "INFO")
                
                def update_save_path(text):
                    if self.stop_requested:
                        return
                    self.savepathSignal.emit(text)
                    self.log_message(f"Save path updated: {text}", "INFO")
                
                self.main.execute_tests(
                    module, sn_nside, sn_pside, slc_nside, slc_pside, emu, 
                    test_values, s_size, s_qgrade, asic_nside_values, asic_pside_values, suid,
                    lv_nside_12_checked, lv_pside_12_checked, lv_nside_18_checked, lv_pside_18_checked,
                    module_files, calib_path, update_progress, update_test_label, update_emu_values,
                    update_vddm, update_temp, efuse_warning, uplinks_warning, update_feb_nside,
                    update_feb_pside, update_calib_path, update_save_path, self.tab_num,
                    check_continue, self
                )
                
                if self.stop_requested:
                    self.log_message("Test execution stopped by user", "WARNING")
                else:
                    self.log_message("Test execution completed successfully", "SUCCESS")
                    self.finishedSignal.emit(True, "")
                
            except Exception as e:
                error_msg = f"Error in test for tab {self.tab_num}: {str(e)}"
                self.log_message(error_msg, "ERROR")
                print(error_msg)
                traceback.print_exc()
                if not self.stop_requested:
                    self.finishedSignal.emit(False, str(e))
