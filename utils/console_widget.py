import sys
import logging
import threading
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ConsoleWidget(QTextEdit):
    
    def __init__(self, tab_num):
        super().__init__()
        self.tab_num = tab_num
        self.setup_ui()
        self.setup_logger()
        
    def setup_ui(self):
        self.setReadOnly(True)
        self.setMaximumHeight(250)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 11px;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
    def setup_logger(self):
        self.logger = logging.getLogger(f"tab_{self.tab_num}")
        self.logger.setLevel(logging.INFO)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        handler = ConsoleHandler(self)
        formatter = logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        self.logger.propagate = False
    
    def append_log(self, message, level="INFO"):
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        
        color_map = {
            "INFO": "#00ff00",
            "ERROR": "#ff4444",
            "WARNING": "#ffaa00",
            "DEBUG": "#aaaaaa",
            "SUCCESS": "#44ff44"
        }
        
        color = color_map.get(level.upper(), "#00ff00")
        
        formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
        
        if QThread.currentThread() == QCoreApplication.instance().thread():
            self.append(formatted_message)
            self.auto_scroll()
        else:
            QMetaObject.invokeMethod(
                self, 
                "append_log_threadsafe", 
                Qt.QueuedConnection,
                Q_ARG(str, formatted_message)
            )
    
    @pyqtSlot(str)
    def append_log_threadsafe(self, formatted_message):
        self.append(formatted_message)
        self.auto_scroll()
        
    def auto_scroll(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_console(self):
        self.clear()
        self.append_log(f"Console cleared for Setup {self.tab_num}", "INFO")

class ConsoleHandler(logging.Handler):
    
    def __init__(self, console_widget):
        super().__init__()
        self.console_widget = console_widget
        
    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname
            self.console_widget.append_log(msg, level)
        except:
            self.handleError(record)

class TabLogger:
    
    def __init__(self, tab_num, console_widget):
        self.tab_num = tab_num
        self.console_widget = console_widget
        self.logger = console_widget.logger
        
    def info(self, message):
        self.logger.info(f"[Setup {self.tab_num}] {message}")
        
    def error(self, message):
        self.logger.error(f"[Setup {self.tab_num}] {message}")
        
    def warning(self, message):
        self.logger.warning(f"[Setup {self.tab_num}] {message}")
        
    def success(self, message):
        self.console_widget.append_log(f"[Setup {self.tab_num}] {message}", "SUCCESS")
        
    def debug(self, message):
        self.logger.debug(f"[Setup {self.tab_num}] {message}")

class PrintCapture:
    
    def __init__(self, tab_logger):
        self.tab_logger = tab_logger
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def __enter__(self):
        sys.stdout = self
        sys.stderr = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def write(self, text):
        if text and text.strip():
            self.tab_logger.info(text.strip())
    
    def flush(self):
        pass

class UniversalOutputCapture:
    
    def __init__(self, tab_num, log_signal):
        self.tab_num = tab_num
        self.log_signal = log_signal
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.original_print = print
        
    def __enter__(self):
        sys.stdout = OutputInterceptor(self.original_stdout, self.log_signal, self.tab_num, "INFO")
        sys.stderr = OutputInterceptor(self.original_stderr, self.log_signal, self.tab_num, "ERROR")
        
        def captured_print(*args, **kwargs):
            import io
            string_io = io.StringIO()
            kwargs_copy = kwargs.copy()
            kwargs_copy['file'] = string_io
            self.original_print(*args, **kwargs_copy)
            output = string_io.getvalue()
            
            if output.strip():
                self.log_signal.emit(output.strip(), "INFO")
            
            self.original_print(*args, **kwargs)
        
        import builtins
        builtins.print = captured_print
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        import builtins
        builtins.print = self.original_print

class OutputInterceptor:
    
    def __init__(self, original, log_signal, tab_num, level):
        self.original = original
        self.log_signal = log_signal
        self.tab_num = tab_num
        self.level = level
        
    def write(self, text):
        if text and text.strip():
            self.log_signal.emit(text.strip(), self.level)
        
        self.original.write(text)
        self.original.flush()
    
    def flush(self):
        self.original.flush()
    
    def __getattr__(self, name):
        return getattr(self.original, name)
