import sys

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QAction, QToolBar, QStatusBar, QLabel, QMessageBox, QApplication, QShortcut
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from utils.translator import Translator
from view.canvas import CircuitView, CircuitScene

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
        self.create_shortcuts()
        self.setup_menus()
        self.setup_toolbar()

        # Status bar
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Central widget
        self.scene = CircuitScene(self.model)
        self.view = CircuitView(self.scene)
        self.setCentralWidget(self.view)

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

        # Edit Actions
        make_action("action_select_all", "Ctrl+A", self.on_select_all)
        make_action("action_select_none", "Ctrl+D", self.on_select_none)
        make_action("action_select_invert", "Ctrl+I", self.on_select_invert)
        make_action("action_filter_nodes", None, self.on_filter_nodes)
        make_action("action_filter_wires", None, self.on_filter_wires)
        make_action("action_filter_sources", None, self.on_filter_sources)
        make_action("action_filter_resistors", None, self.on_filter_resistors)
        make_action("action_filter_capacitors", None, self.on_filter_capacitors)
        make_action("action_filter_inductors", None, self.on_filter_inductors)
        make_action("action_filter_add", None, self.on_filter_add)

        # View Actions
        make_action("action_theme_dark", None, self.set_dark_mode)
        make_action("action_theme_light", None, self.set_light_mode)

        # Options Actions
        
        # Simulation Actions

    def set_dark_mode(self):
        self.change_theme("dark")

    def set_light_mode(self):
        self.change_theme("light")

    def change_theme(self, theme_name):
        if theme_name == "dark":
            self.setStyleSheet("QMainWindow { background-color: #2b2b2b; color: white; }")
            self.view.setBackgroundBrush(Qt.black)
        else:
            self.setStyleSheet("")
            self.view.setBackgroundBrush(Qt.white)

    def create_shortcuts(self):
        """Définit les raccourcis clavier globaux"""
        
        # Delete key
        self.shortcut_delete = QShortcut(QKeySequence("Del"), self)
        self.shortcut_delete.activated.connect(self.delete_selected_items)
        
        # Test keys
        self.shortcut_tool_pointer = QShortcut(QKeySequence("V"), self)
        self.shortcut_tool_pointer.activated.connect(lambda: self.set_tool("pointer"))
        self.shortcut_tool_wire = QShortcut(QKeySequence("W"), self)
        self.shortcut_tool_wire.activated.connect(lambda: self.set_tool("wire"))
        self.shortcut_tool_resistor = QShortcut(QKeySequence("R"), self)
        self.shortcut_tool_resistor.activated.connect(lambda: self.set_tool("resistor"))
        self.shortcut_tool_source_dc = QShortcut(QKeySequence("D"), self)
        self.shortcut_tool_source_dc.activated.connect(lambda: self.set_tool("source_dc"))
        self.shortcut_tool_source_ac = QShortcut(QKeySequence("A"), self)
        self.shortcut_tool_source_ac.activated.connect(lambda: self.set_tool("source_ac"))
        self.shortcut_tool_capacitor = QShortcut(QKeySequence("C"), self)
        self.shortcut_tool_capacitor.activated.connect(lambda: self.set_tool("capacitor"))
        self.shortcut_tool_inductor = QShortcut(QKeySequence("L"), self)
        self.shortcut_tool_inductor.activated.connect(lambda: self.set_tool("inductor"))

    def set_tool(self, tool_name):
        """Change l'outil"""
        
        # Scène
        if hasattr(self, 'scene'):
            self.scene.set_tool(tool_name)
            
        # Vue
        if hasattr(self, 'view'):
            self.view.set_tool_mode(tool_name)
            
        # Change le curseur
        if tool_name == "pointer":
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.CrossCursor)


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

        # Edit Menu
        self.menu_edit.addAction(self.custom_actions["action_select_all"])
        self.menu_edit.addAction(self.custom_actions["action_select_none"])
        self.menu_edit.addAction(self.custom_actions["action_select_invert"])
        self.menu_selection_filter = self.menu_edit.addMenu('')
        self.menu_selection_filter.addAction(self.custom_actions["action_filter_nodes"])
        self.menu_selection_filter.addAction(self.custom_actions["action_filter_wires"])
        self.menu_selection_filter.addAction(self.custom_actions["action_filter_sources"])
        self.menu_selection_filter.addAction(self.custom_actions["action_filter_resistors"])
        self.menu_selection_filter.addAction(self.custom_actions["action_filter_capacitors"])
        self.menu_selection_filter.addAction(self.custom_actions["action_filter_inductors"])
        self.menu_selection_filter.addAction(self.custom_actions["action_filter_capacitors"])
        self.menu_selection_filter.addAction(self.custom_actions["action_filter_add"])
        self.menu_file.addSeparator()

        # View Menu
        self.menu_theme = self.menu_view.addMenu('')
        self.menu_theme.addAction(self.custom_actions["action_theme_dark"])
        self.menu_theme.addAction(self.custom_actions["action_theme_light"])

        # Options Menu

        # Simulation Menu


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

        # File Menu
        self.menu_recent_files.setTitle(Translator.tr("menu_recent_files"))

        # Edit Menu
        self.menu_selection_filter.setTitle(Translator.tr("menu_selection_filter"))

        # Mise à jour automatique de toutes les actions stockées
        # Le dictionnaire self.custom_actions contient {"cle_traduction": QAction}
        for key, action in self.custom_actions.items():
            action.setText(Translator.tr(key))

        self.status_bar.showMessage(Translator.tr("status_ready"))

        self.menu_theme.setTitle(Translator.tr("menu_theme"))

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

    def on_select_all(self):
        print("Select All")

    def on_select_none(self):
        print("Select None")

    def on_select_invert(self):
        print("Invert Selection")

    # TODO peut-être regrouper ces fonctions de filtre dans une seule avec un paramètre ?
    def on_filter_nodes(self):
        print("Filter Nodes")

    def on_filter_wires(self):
        print("Filter Wires")

    def on_filter_sources(self):
        print("Filter Sources")
    
    def on_filter_resistors(self):
        print("Filter Resistors")

    def on_filter_capacitors(self):
        print("Filter Capacitors")

    def on_filter_inductors(self):
        print("Filter Inductors")

    def on_filter_add(self):
        print("Filter Add")

    def delete_selected_items(self):
        """Demande à la scène de supprimer ce qui est sélectionné"""
        # On vérifie que la scène existe
        if hasattr(self, 'scene'):
            self.scene.delete_selection()