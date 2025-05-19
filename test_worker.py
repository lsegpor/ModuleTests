from PyQt5.QtCore import pyqtSignal, QObject, QTimer

class TestWorker(QObject):
    progressSignal = pyqtSignal(int)
    infoSignal = pyqtSignal(str)
    emuSignal = pyqtSignal(str, str)
    vddmSignal = pyqtSignal(list, list, list, list)
    tempSignal = pyqtSignal(list, list, list, list)
    febnsideSignal = pyqtSignal(float, float, float, float)
    febpsideSignal = pyqtSignal(float, float, float, float)
    calibSignal = pyqtSignal(str)
    savepathSignal = pyqtSignal(str)
    finishedSignal = pyqtSignal(bool, str)
    
    def __init__(self, main_logic, params, tab_num):
        super().__init__()
        self.main = main_logic
        self.params = params
        self.tab_num = tab_num
        self.stop_requested = False
        self.stop_timer = None
        
    def request_stop(self):
        self.stop_requested = True
        self.infoSignal.emit("*** TEST EXECUTION STOPPED ***")
        
        self.stop_timer = QTimer()
        self.stop_timer.setSingleShot(True)
        self.stop_timer.timeout.connect(self._force_finish)
        self.stop_timer.start(100)
        
    def _force_finish(self):
        self.finishedSignal.emit(False, "Tests stopped by user") 
        
    def run(self): 
        try:
            main_instance = self.main
            
            if self.stop_requested:
                self.finishedSignal.emit(False, "Tests stopped by user")
                return
            
            (module, sn_nside, sn_pside, slc_nside, slc_pside, emu, test_values, s_size, s_qgrade,
             asic_nside_values, asic_pside_values, suid, lv_nside_12_checked, lv_pside_12_checked,
             lv_nside_18_checked, lv_pside_18_checked, module_files, calib_path) = self.params
            
            def update_progress(value):
                if self.stop_requested:
                    return
                self.progressSignal.emit(value)
                
            def update_test_label(text):
                if self.stop_requested:
                    return
                self.infoSignal.emit(text)
                
            def update_emu_values(v_value, i_value):
                if self.stop_requested:
                    return
                self.emuSignal.emit(v_value, i_value)
                
            def update_vddm(n_idx, n_val, p_idx, p_val):
                if self.stop_requested:
                    return
                self.vddmSignal.emit(n_idx, n_val, p_idx, p_val)
                
            def update_temp(n_idx, n_val, p_idx, p_val):
                if self.stop_requested:
                    return
                self.tempSignal.emit(n_idx, n_val, p_idx, p_val)
                
            def update_feb_nside(v12_val, i12_val, v18_val, i18_val):
                if self.stop_requested:
                    return
                self.febnsideSignal.emit(v12_val, i12_val, v18_val, i18_val)
                
            def update_feb_pside(v12_val, i12_val, v18_val, i18_val):
                if self.stop_requested:
                    return
                self.febpsideSignal.emit(v12_val, i12_val, v18_val, i18_val)
                
            def update_calib_path(text):
                if self.stop_requested:
                    return
                self.calibSignal.emit(text)
            
            def update_save_path(text):
                if self.stop_requested:
                    return
                self.savepathSignal.emit(text)
                
            check_stop = lambda: not self.stop_requested
            
            self.main.execute_tests(
                module, sn_nside, sn_pside, slc_nside, slc_pside, emu, 
                test_values, s_size, s_qgrade, asic_nside_values, asic_pside_values, suid,
                lv_nside_12_checked, lv_pside_12_checked, lv_nside_18_checked, lv_pside_18_checked,
                module_files, calib_path, update_progress, update_test_label, update_emu_values,
                update_vddm, update_temp, update_feb_nside, update_feb_pside, update_calib_path,
                update_save_path, self.tab_num, check_stop,
            )
            
            if self.stop_requested:
                pass
            else:
                self.finishedSignal.emit(True, "")
            
        except Exception as e:
            print(f"Error in test for tab {self.tab_num}: {str(e)}")
            import traceback
            traceback.print_exc()
            if not self.stop_requested:
                self.finishedSignal.emit(False, str(e))
