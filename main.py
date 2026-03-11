"""Application entry point."""

import sys

from PyQt5.QtWidgets import QApplication

from model.circuit import Circuit
from view.main_window import MainWindow
from utils.translator import Translator

def main():
    """Create the Qt application and show the main window"""
    app = QApplication(sys.argv)

    Translator.load_language("fr")

    circuit = Circuit()
    
    window = MainWindow(model=circuit)
    
    window.showMaximized()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()