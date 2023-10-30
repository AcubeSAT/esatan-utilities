import logging
import sys

from PySide6.QtWidgets import QApplication

from GUI import UtilsGUI
from IOutils import read_config
from paths import get_path

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%d-%b-%y %H:%M:%S'
    )
    logging.info("Logger initialized.")

    RELATIVE_PATHS = False
    CONFIG = read_config(get_path("config", RELATIVE_PATHS))
    if not CONFIG:
        logging.error("Loading the configuration file failed.")
        exit(1)
    logging.info("Configuration file loaded successfully.")

    WINDOW_CONFIG = CONFIG.window
    app = QApplication([])

    logging.info("Starting main window.")
    window = UtilsGUI()
    window.resize(
        WINDOW_CONFIG["dimension"]["width"],
        WINDOW_CONFIG["dimension"]["height"]
    )
    window.show()
    logging.info("Window rendered successfully.")

    sys.exit(app.exec())
