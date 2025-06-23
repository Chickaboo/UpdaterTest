import sys
from PyQt6 import QtWidgets
from gui.mainwindow import SwissTournamentApp
import logging
import requests

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # Optionally load stylesheet
    try:
        with open("styles.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Could not load stylesheet: {e}")
    try: 
        # Try to apply a modern style if available
        available_styles = QtWidgets.QStyleFactory.keys()
        if "Fusion" in available_styles:
            app.setStyle("WindowsVista")
        elif "WindowsVista" in available_styles and sys.platform == "win32": # Windows specific
            app.setStyle("WindowsVista")
        # Add other preferred styles if needed
    except Exception as e: 
        logging.warning(f"Could not set preferred application style: {e}")

    window = SwissTournamentApp()
    window.show()
    sys.exit(app.exec())
