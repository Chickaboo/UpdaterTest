import logging
import sys
import random
from PyQt6 import QtCore
from PyQt6.QtCore import QDateTime
from core.constants import APP_NAME

# --- Logging Setup ---
# Setup logging to file and console
log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO) # Set minimum level

# File Handler
try:
    # Attempt to create a log file in the user's home directory or a temp directory
    log_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.AppDataLocation)
    if not log_dir:
        log_dir = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.TempLocation)
    if log_dir:
        log_path = QtCore.QDir(log_dir).filePath("gambit_pairing.log")
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
        print(f"Logging to: {log_path}") # Inform user where logs are
    else:
        print("Warning: Could not determine writable location for log file.")
except Exception as e:
    print(f"Warning: Could not create log file handler: {e}")


# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# --- Utility Functions ---
def generate_id(prefix: str = "item_") -> str:
    """Generates a simple unique ID."""
    return f"{prefix}{random.randint(100000, 999999)}_{int(QDateTime.currentMSecsSinceEpoch())}"