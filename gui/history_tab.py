from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import QDateTime
import logging

class HistoryTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.history_view = QtWidgets.QPlainTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setToolTip("Log of pairings, results, and actions.")
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        self.history_view.setFont(font)
        self.main_layout.addWidget(self.history_view)

    def update_history_log(self, message: str):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.history_view.appendPlainText(f"[{timestamp}] {message}")
        logging.info(f"UI_LOG: {message}") # Distinguish from backend logging if needed

    def update_ui_state(self):
        pass
