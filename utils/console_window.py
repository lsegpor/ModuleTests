from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ConsoleWindow(QMainWindow):
    
    def __init__(self, tab_num, parent=None):
        super().__init__(parent)
        self.tab_num = tab_num
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"Console - Setup {self.tab_num}")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"Console Output - Setup {self.tab_num}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMaximumWidth(80)
        self.clear_btn.clicked.connect(self.clear_console)
        header_layout.addWidget(self.clear_btn)
        
        self.save_btn = QPushButton("Save Log")
        self.save_btn.setMaximumWidth(80)
        self.save_btn.clicked.connect(self.save_log)
        header_layout.addWidget(self.save_btn)
        
        layout.addLayout(header_layout)
        
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 12px;
                border: 1px solid #555;
                padding: 10px;
            }
        """)
        layout.addWidget(self.console_text)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Ready - Setup {self.tab_num}")
    
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
        
        self.console_text.append(formatted_message)
        
        scrollbar = self.console_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        line_count = self.console_text.document().lineCount()
        self.status_bar.showMessage(f"Setup {self.tab_num} - {line_count} lines")
    
    def clear_console(self):
        self.console_text.clear()
        self.append_log(f"Console cleared", "INFO")
    
    def save_log(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            f"Save Console Log - Setup {self.tab_num}",
            f"setup_{self.tab_num}_console.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                plain_text = self.console_text.toPlainText()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Console Log - Setup {self.tab_num}\n")
                    f.write("=" * 50 + "\n")
                    f.write(plain_text)
                
                self.append_log(f"Log saved to: {filename}", "SUCCESS")
                
            except Exception as e:
                self.append_log(f"Error saving log: {str(e)}", "ERROR")
    
    def closeEvent(self, event):
        self.hide()
        event.ignore()

class ConsoleManager:
    
    def __init__(self):
        self.console_windows = {}
    
    def get_console_window(self, tab_num, parent=None):
        if tab_num not in self.console_windows:
            self.console_windows[tab_num] = ConsoleWindow(tab_num, parent)
        
        return self.console_windows[tab_num]
    
    def show_console(self, tab_num, parent=None):
        console_window = self.get_console_window(tab_num, parent)
        console_window.show()
        console_window.raise_()
        console_window.activateWindow()
        return console_window
    
    def hide_console(self, tab_num):
        if tab_num in self.console_windows:
            self.console_windows[tab_num].hide()
    
    def add_log(self, tab_num, message, level="INFO"):
        if tab_num in self.console_windows:
            self.console_windows[tab_num].append_log(message, level)
    
    def clear_console(self, tab_num):
        if tab_num in self.console_windows:
            self.console_windows[tab_num].clear_console()
