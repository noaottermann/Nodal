import sys

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QAction, QToolBar, QStatusBar, QMessageBox, QApplication, QShortcut
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QKeySequence
from utils.translator import Translator
from view.canvas import CircuitView, CircuitScene
from view.components_panel import ComponentsPanel

class MainWindow(QMainWindow):
    """
    Main window of Nodal
    """
    def __init__(self, model=None):
        super().__init__()
        self.model = model
        self.custom_actions = {}
        # Position x, y, Largeur, Hauteur
        self.init_ui_structure()
        self.retranslateUi()

    def init_ui_structure(self):
        """Create the main UI structure"""
        self._configure_window_geometry()
        
        # Setup
        self.create_actions()
        self.create_shortcuts()
        self.setup_menus()
        self.setup_toolbar()

        # Status bar
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Central widget
        self._setup_central_widget()

    def _configure_window_geometry(self):
        primary_screen = QApplication.primaryScreen()
        if primary_screen is not None:
            screen_geometry = primary_screen.availableGeometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
        else:
            screen_width = 1024
            screen_height = 768
        width = int(screen_width * 0.8)
        height = int(screen_height * 0.8)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.setGeometry(x, y, width, height)

    def _setup_central_widget(self):
        self.scene = CircuitScene(self.model)
        self.view = CircuitView(self.scene)

        self.components_panel = ComponentsPanel()
        self.components_panel.setMinimumWidth(200)
        self.components_panel.setMaximumWidth(300)
        self.components_panel.tool_selected.connect(self.set_tool)

        central_widget = QWidget()
        central_layout = QHBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.components_panel)
        central_layout.addWidget(self.view, 1)
        self.setCentralWidget(central_widget)
        
        # Set initial focus to the circuit view instead of search bar
        self.view.setFocus()

    def create_actions(self):
        """Create all actions for the main window"""
        self._create_file_actions()
        self._create_edit_actions()
        self._create_view_actions()
        self._create_options_actions()

    def _make_action(self, key, shortcut=None, slot=None):
        action = QAction('', self)
        if shortcut:
            action.setShortcut(shortcut)
        if slot:
            action.triggered.connect(slot)
        # The action is stored in the dictionary with its translation key as its ID
        self.custom_actions[key] = action
        return action

    def _create_file_actions(self):
        self._make_action("action_new_file", "Ctrl+N", self.on_new_file)
        self._make_action("action_new_window", "Ctrl+Shift+N", self.on_new_window)
        self._make_action("action_open", "Ctrl+O", self.on_open_file)
        self._make_action("action_save", "Ctrl+S", self.on_save_file)
        self._make_action("action_save_as", "Ctrl+Shift+S", self.on_save_as)
        self._make_action("action_import", None, self.on_import)
        self._make_action("action_export", None, self.on_export)
        self._make_action("action_history", None, self.on_version_history)
        self._make_action("action_quit", "Ctrl+Q", self.close)

    def _create_edit_actions(self):
        self._make_action("action_select_all", "Ctrl+A", self.on_select_all)
        self._make_action("action_select_none", "Ctrl+D", self.on_select_none)
        self._make_action("action_select_invert", "Ctrl+I", self.on_select_invert)
        self._make_action("action_filter_nodes", None, self.on_filter_nodes)
        self._make_action("action_filter_wires", None, self.on_filter_wires)
        self._make_action("action_filter_sources", None, self.on_filter_sources)
        self._make_action("action_filter_resistors", None, self.on_filter_resistors)
        self._make_action("action_filter_capacitors", None, self.on_filter_capacitors)
        self._make_action("action_filter_inductors", None, self.on_filter_inductors)
        self._make_action("action_filter_add", None, self.on_filter_add)

        self._make_action("action_invert_x", None, self.on_invert_x)
        self._make_action("action_invert_y", None, self.on_invert_y)
        self._make_action("action_invert_xy", None, self.on_invert_xy)

        self._make_action("action_align_left", None, self.on_align_left)
        self._make_action("action_align_right", None, self.on_align_right)
        self._make_action("action_align_top", None, self.on_align_top)
        self._make_action("action_align_bottom", None, self.on_align_bottom)
        self._make_action("action_distribute_horiz", None, self.on_distribute_horiz)
        self._make_action("action_distribute_vertic", None, self.on_distribute_vertic)

        self._make_action("action_group", None, self.on_group_items)
        self._make_action("action_ungroup", None, self.on_ungroup_items)
        self._make_action("action_clean", None, self.on_clean_canvas)

    def _create_view_actions(self):
        self._make_action("action_toggle_grid", None, self.on_toggle_grid)
        self._make_action("action_snap_grid", None, self.on_snap_grid)
        self._make_action("action_grid_size", None, self.on_grid_size)

        self._make_action("action_show_labels", None, self.on_toggle_labels)
        self._make_action("action_show_nodes", None, self.on_toggle_nodes)
        self._make_action("action_show_wire_dir", None, self.on_toggle_wire_dir)

        self._make_action("action_center_select", None, self.on_center_selection)
        self._make_action("action_reset_zoom", None, self.on_reset_zoom)
        self._make_action("action_fullscreen", None, self.on_toggle_fullscreen)
        self._make_action("action_highlight_short", None, self.on_highlight_short_circuit)
        self._make_action("action_show_components", None, self.on_toggle_view_components)
        self._make_action("action_show_sim", None, self.on_toggle_view_simulation)
        self._make_action("action_show_graphs", None, self.on_toggle_view_graphs)
        self._make_action("action_show_examples", None, self.on_toggle_view_examples)
        self._make_action("action_show_toolbar", None, self.on_toggle_view_toolbar)
        self._make_action("action_theme_dark", None, self.set_dark_mode)
        self._make_action("action_theme_light", None, self.set_light_mode)

    def _create_options_actions(self):
        self._make_action("action_auto_save_int", None, lambda: print("Auto-save Int"))
        self._make_action("action_toggle_auto_save", None, lambda: print("Toggle Auto-save"))
        self._make_action("action_lang_fr", None, self.set_lang_fr)
        self._make_action("action_lang_en", None, self.set_lang_en)
        self._make_action("action_restore_session", None, self.on_restore_session)

        self._make_action("action_unit_si", None, self.on_set_unit_si)
        self._make_action("action_unit_eng", None, self.on_set_unit_eng)
        self._make_action("action_unit_compact", None, self.on_set_unit_compact)

        self._make_action("action_precision", None, self.on_set_precision)
        self._make_action("action_sci_notation", None, self.on_toggle_sci_notation)
        self._make_action("action_cross_cursor", None, self.on_toggle_cross_cursor)
        self._make_action("action_enable_anim", None, self.on_toggle_animations)
        self._make_action("action_allow_overlap", None, self.on_toggle_overlap)
        self._make_action("action_disable_editing", None, self.on_toggle_editing)
        self._make_action("action_conv_current", None, self.on_toggle_conv_current)

        self._make_action("action_grid_export", None, self.on_toggle_grid_export)
        self._make_action("action_sim_export", None, self.on_toggle_sim_export)
        self._make_action("action_bg_color", None, self.on_change_bg_color)
        self._make_action("action_keybinds", None, self.on_show_keybinds)

        self._make_action("action_color_pos", None, self.on_set_color_positive)
        self._make_action("action_color_neg", None, self.on_set_color_negative)
        self._make_action("action_color_neu", None, self.on_set_color_neutral)
        self._make_action("action_color_sel", None, self.on_set_color_selected)
        self._make_action("action_color_cur", None, self.on_set_color_current)

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
        
        self._setup_file_menu()
        self._setup_edit_menu()
        self._setup_view_menu()
        self._setup_options_menu()
        # Simulation Menu

    def _setup_file_menu(self):
        self.menu_file.addAction(self.custom_actions["action_new_file"])
        self.menu_file.addAction(self.custom_actions["action_new_window"])
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.custom_actions["action_open"])
        self.menu_recent_files = self.menu_file.addMenu('') 
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

    def _setup_edit_menu(self):
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
        self.menu_edit.addSeparator()
        
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.custom_actions["action_invert_x"])
        self.menu_edit.addAction(self.custom_actions["action_invert_y"])
        self.menu_edit.addAction(self.custom_actions["action_invert_xy"])
        
        self.menu_edit.addSeparator() 

        self.menu_align = self.menu_edit.addMenu('') 
        self.menu_align.addAction(self.custom_actions["action_align_left"])
        self.menu_align.addAction(self.custom_actions["action_align_right"])
        self.menu_align.addAction(self.custom_actions["action_align_top"])
        self.menu_align.addAction(self.custom_actions["action_align_bottom"])
        self.menu_align.addSeparator()
        self.menu_align.addAction(self.custom_actions["action_distribute_horiz"])
        self.menu_align.addAction(self.custom_actions["action_distribute_vertic"])
        
        self.menu_edit.addSeparator() 
        self.menu_edit.addAction(self.custom_actions["action_group"])
        self.menu_edit.addAction(self.custom_actions["action_ungroup"])
        
        self.menu_edit.addSeparator() 
        self.menu_edit.addAction(self.custom_actions["action_clean"])

    def _setup_view_menu(self):
        self.menu_view.addAction(self.custom_actions["action_toggle_grid"])
        self.menu_view.addAction(self.custom_actions["action_snap_grid"])
        self.menu_view.addAction(self.custom_actions["action_grid_size"])
        self.menu_view.addSeparator()
        
        self.menu_view.addAction(self.custom_actions["action_show_labels"])
        self.menu_view.addAction(self.custom_actions["action_show_nodes"])
        self.menu_view.addAction(self.custom_actions["action_show_wire_dir"])
        self.menu_view.addSeparator()

        self.menu_theme = self.menu_view.addMenu('')
        self.menu_theme.addAction(self.custom_actions["action_theme_dark"])
        self.menu_theme.addAction(self.custom_actions["action_theme_light"])

        self.menu_view.addAction(self.custom_actions["action_center_select"])
        self.menu_view.addAction(self.custom_actions["action_reset_zoom"])
        self.menu_view.addAction(self.custom_actions["action_fullscreen"])
        self.menu_view.addSeparator()

        self.menu_show_hide = self.menu_view.addMenu('')
        self.menu_show_hide.addAction(self.custom_actions["action_show_components"])
        self.menu_show_hide.addAction(self.custom_actions["action_show_sim"])
        self.menu_show_hide.addAction(self.custom_actions["action_show_graphs"])
        self.menu_show_hide.addAction(self.custom_actions["action_show_examples"])
        self.menu_show_hide.addAction(self.custom_actions["action_show_toolbar"])
        
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.custom_actions["action_highlight_short"])

    def _setup_options_menu(self):
        self.menu_options.addAction(self.custom_actions["action_auto_save_int"])
        self.menu_options.addAction(self.custom_actions["action_toggle_auto_save"])
        self.menu_lang = self.menu_options.addMenu('') 
        self.menu_lang.addAction(self.custom_actions["action_lang_fr"])
        self.menu_lang.addAction(self.custom_actions["action_lang_en"])
        self.menu_options.addAction(self.custom_actions["action_restore_session"])
        self.menu_options.addSeparator()
        
        self.menu_units = self.menu_options.addMenu('')
        self.menu_units.addAction(self.custom_actions["action_unit_si"])
        self.menu_units.addAction(self.custom_actions["action_unit_eng"])
        self.menu_units.addAction(self.custom_actions["action_unit_compact"])
        
        self.menu_options.addSeparator()
        self.menu_options.addAction(self.custom_actions["action_precision"])
        self.menu_options.addAction(self.custom_actions["action_sci_notation"])
        self.menu_options.addAction(self.custom_actions["action_cross_cursor"])
        self.menu_options.addAction(self.custom_actions["action_enable_anim"])
        self.menu_options.addAction(self.custom_actions["action_allow_overlap"])
        self.menu_options.addAction(self.custom_actions["action_disable_editing"])
        self.menu_options.addAction(self.custom_actions["action_conv_current"])
        self.menu_options.addSeparator()
        
        self.menu_options.addAction(self.custom_actions["action_grid_export"])
        self.menu_options.addAction(self.custom_actions["action_sim_export"])
        self.menu_options.addSeparator()
        
        self.menu_options.addAction(self.custom_actions["action_bg_color"])
        self.menu_options.addAction(self.custom_actions["action_keybinds"])

        self.menu_colors = self.menu_options.addMenu('')
        self.menu_colors.addAction(self.custom_actions["action_color_pos"])
        self.menu_colors.addAction(self.custom_actions["action_color_neg"])
        self.menu_colors.addAction(self.custom_actions["action_color_neu"])
        self.menu_colors.addAction(self.custom_actions["action_color_sel"])
        self.menu_colors.addAction(self.custom_actions["action_color_cur"])


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
        self._retranslate_menus()
        self._retranslate_actions()
        self.status_bar.showMessage(Translator.tr("status_ready"))

    def _retranslate_menus(self):
        self.menu_file.setTitle(Translator.tr("menu_file"))
        self.menu_edit.setTitle(Translator.tr("menu_edit"))
        self.menu_view.setTitle(Translator.tr("menu_view"))
        self.menu_options.setTitle(Translator.tr("menu_options"))
        self.menu_simulation.setTitle(Translator.tr("menu_simulation"))

        self.menu_recent_files.setTitle(Translator.tr("menu_recent_files"))
        self.menu_selection_filter.setTitle(Translator.tr("menu_selection_filter"))
        self.menu_align.setTitle(Translator.tr("menu_align"))
        self.menu_show_hide.setTitle(Translator.tr("menu_show_hide"))
        self.menu_units.setTitle(Translator.tr("menu_units"))
        self.menu_colors.setTitle(Translator.tr("menu_colors"))
        self.menu_lang.setTitle(Translator.tr("action_language"))
        self.menu_theme.setTitle(Translator.tr("menu_theme"))

    def _retranslate_actions(self):
        # Le dictionnaire self.custom_actions contient {"cle_traduction": QAction}
        for key, action in self.custom_actions.items():
            action.setText(Translator.tr(key))

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

    def on_invert_x(self):
        print("Action: Inverser X")

    def on_invert_y(self):
        print("Action: Inverser Y")

    def on_invert_xy(self):
        print("Action: Inverser XY")

    def on_align_left(self):
        print("Action: Aligner à gauche")

    def on_align_right(self):
        print("Action: Aligner à droite")

    def on_align_top(self):
        print("Action: Aligner en haut")

    def on_align_bottom(self):
        print("Action: Aligner en bas")

    def on_distribute_horiz(self):
        print("Action: Distribuer horizontalement")

    def on_distribute_vertic(self):
        print("Action: Distribuer verticalement")

    def on_group_items(self):
        print("Action: Grouper les éléments")

    def on_ungroup_items(self):
        print("Action: Dégrouper les éléments")

    def on_clean_canvas(self):
        print("Action: Nettoyer le canvas")

    # View Actions
    def on_toggle_grid(self):
        print("Action: Afficher/Masquer la grille")

    def on_snap_grid(self):
        print("Action: Activer/Désactiver l'aimantation")

    def on_grid_size(self):
        print("Action: Modifier la taille de la grille")

    def on_toggle_labels(self):
        print("Action: Afficher/Masquer les étiquettes")

    def on_toggle_nodes(self):
        print("Action: Afficher/Masquer les IDs des nœuds")

    def on_toggle_wire_dir(self):
        print("Action: Afficher/Masquer la direction du courant")

    def on_center_selection(self):
        print("Action: Centrer la vue sur la sélection")

    def on_reset_zoom(self):
        print("Action: Réinitialiser le zoom")

    def on_toggle_fullscreen(self):
        print("Action: Basculer le mode plein écran")

    def on_highlight_short_circuit(self):
        print("Action: Surligner les courts-circuits")

    def on_toggle_view_components(self):
        if hasattr(self, "components_panel"):
            is_visible = self.components_panel.isVisible()
            self.components_panel.setVisible(not is_visible)

    def on_toggle_view_simulation(self):
        print("Fenêtre: Simulation")

    def on_toggle_view_graphs(self):
        print("Fenêtre: Graphiques")

    def on_toggle_view_examples(self):
        print("Fenêtre: Exemples")

    def on_toggle_view_toolbar(self):
        print("Fenêtre: Barre d'outils")

    # Options Actions

    def on_set_autosave_interval(self):
        print("Option: Réglage de l'intervalle de sauvegarde")

    def on_toggle_autosave(self):
        print("Option: Basculer la sauvegarde automatique")

    def on_set_language(self, lang):
        self.change_language(lang)

    def set_lang_fr(self):
        self.change_language("fr")

    def set_lang_en(self):
        self.change_language("en")

    def on_restore_session(self):
        print("Option: Restaurer la session au démarrage")

    def on_set_unit_si(self):
        print("Unités: Passage au système SI")

    def on_set_unit_eng(self):
        print("Unités: Passage au système Ingénierie")

    def on_set_unit_compact(self):
        print("Unités: Passage au mode Compact")

    def on_set_precision(self):
        print("Option: Réglage de la précision")

    def on_toggle_sci_notation(self):
        print("Option: Notation scientifique ON/OFF")

    def on_toggle_cross_cursor(self):
        print("Option: Curseur en croix ON/OFF")

    def on_toggle_animations(self):
        print("Option: Animations ON/OFF")

    def on_toggle_overlap(self):
        print("Option: Chevauchement ON/OFF")

    def on_toggle_editing(self):
        print("Option: Verrouillage de l'édition")

    def on_toggle_conv_current(self):
        print("Option: Sens du courant")

    def on_toggle_grid_export(self):
        print("Export: Grille incluse/exclue")

    def on_toggle_sim_export(self):
        print("Export: Données de sim incluses/exclues")

    def on_change_bg_color(self):
        print("Interface: Changement couleur de fond")

    def on_show_keybinds(self):
        print("Fenêtre: Liste des raccourcis")

    def on_set_color_positive(self):
        print("Couleur: Positif")

    def on_set_color_negative(self):
        print("Couleur: Négatif")

    def on_set_color_neutral(self):
        print("Couleur: Neutre")

    def on_set_color_selected(self):
        print("Couleur: Sélection")

    def on_set_color_current(self):
        print("Couleur: Courant")

    def delete_selected_items(self):
        """Demande à la scène de supprimer ce qui est sélectionné"""
        # On vérifie que la scène existe
        if hasattr(self, 'scene'):
            self.scene.delete_selection()