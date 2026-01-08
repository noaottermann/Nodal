import sys

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QAction, QToolBar, QStatusBar, QLabel, QMessageBox, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from utils.translator import Translator

class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application ElectricSystemLab
    """

    def __init__(self, model=None):
        super().__init__()
        self.model = model
        self.custom_actions = {}
        # Position x, y, Largeur, Hauteur
        self.init_ui_structure()
        self.retranslateUi()

    def init_ui_structure(self):
        """Construction des éléments graphiques"""
        # Window size and position
        primary_screen = QApplication.primaryScreen()
        if primary_screen is not None:
            screen_geometry = primary_screen.availableGeometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
        else:
            # Fallback values if no screen is available
            screen_width = 1024
            screen_height = 768
        width = int(screen_width * 0.8)
        height = int(screen_height * 0.8)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.setGeometry(x, y, width, height)
        
        # Setup
        self.create_actions()
        self.setup_menus()
        self.setup_toolbar()

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Placeholder layout
        layout = QVBoxLayout(self.central_widget)
        self.canvas_label = QLabel("Canvas Placeholder")
        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_label.setStyleSheet("background-color: #f0f0f0; font-size: 20px; color: #888;")
        layout.addWidget(self.canvas_label)

    def create_actions(self):
        """Crée toutes les actions de la fenêtre principale"""
        def make_action(key, shortcut=None, slot=None):
            action = QAction('', self)
            if shortcut:
                action.setShortcut(shortcut)
            if slot:
                action.triggered.connect(slot)
            # The action is stored in the dictionary with its translation key as its ID
            self.custom_actions[key] = action
            return action
        
        # File Actions
        make_action("action_new_file", "Ctrl+N", self.on_new_file)
        make_action("action_new_window", "Ctrl+Shift+N", self.on_new_window)
        make_action("action_open", "Ctrl+O", self.on_open_file)
        make_action("action_save", "Ctrl+S", self.on_save_file)
        make_action("action_save_as", "Ctrl+Shift+S", self.on_save_as)
        make_action("action_import", None, self.on_import)
        make_action("action_export", None, self.on_export)
        make_action("action_history", None, self.on_version_history)
        make_action("action_quit", "Ctrl+Q", self.close)

    def setup_menus(self):
        """Crée les menus de la fenêtre principale"""
        menubar = self.menuBar()

        # Menus
        self.menu_file = menubar.addMenu('')
        self.menu_edit = menubar.addMenu('')
        self.menu_view = menubar.addMenu('')
        self.menu_options = menubar.addMenu('')
        self.menu_simulation = menubar.addMenu('')
        
        # File Menu
        self.menu_file.addAction(self.custom_actions["action_new_file"])
        self.menu_file.addAction(self.custom_actions["action_new_window"])
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.custom_actions["action_open"])
        self.menu_recent_files = self.menu_file.addMenu('') 
        # Placeholder
        self.placeholder_recent_files = QAction("example.json", self)
        self.menu_recent_files.addAction(self.placeholder_recent_files)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.custom_actions["action_save"])
        self.menu_file.addAction(self.custom_actions["action_save_as"])
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.custom_actions["action_import"])
        self.menu_file.addAction(self.custom_actions["action_export"])
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.custom_actions["action_history"])
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.custom_actions["action_quit"])

    def setup_toolbar(self):
        toolbar = QToolBar("Barre d'outils principale")
        self.addToolBar(toolbar)
        
        toolbar.addAction("Undo")
        toolbar.addAction("Redo")
        toolbar.addSeparator()
        toolbar.addAction("Zoom In")
        toolbar.addAction("Zoom Out")
        toolbar.addAction("Zoom 1:1")

    def retranslateUi(self):
        """Met à jour tous les textes"""
        self.setWindowTitle(Translator.tr("app_title"))
        
        # Menus
        self.menu_file.setTitle(Translator.tr("menu_file"))
        self.menu_edit.setTitle(Translator.tr("menu_edit"))
        self.menu_view.setTitle(Translator.tr("menu_view"))
        self.menu_options.setTitle(Translator.tr("menu_options"))
        self.menu_simulation.setTitle(Translator.tr("menu_simulation"))
        self.menu_recent_files.setTitle(Translator.tr("menu_recent_files"))

        # Automatic update of all stored actions
        # The self.custom_actions dictionary contains {“translation_key”: QActionObject}
        for key, action in self.custom_actions.items():
            action.setText(Translator.tr(key))

        self.status_bar.showMessage(Translator.tr("status_ready"))

    def change_language(self, lang):
        """Change la langue et rafraîchit l'interface"""
        if Translator.load_language(lang):
            self.retranslateUi()
        else:
            QMessageBox.warning(self, "Error", f"Unable to load language '{lang}'.")

    # Action Handlers
    def on_new_file(self):
        print("New File")

    def on_new_window(self):
        print("New Window")

    def on_open_file(self):
        print("Open File")

    def on_save_file(self):
        print("Save File")

    def on_save_as(self):
        print("Save As")

    def on_import(self):
        print("Import")

    def on_export(self):
        print("Export")

    def on_version_history(self):
        print("History")