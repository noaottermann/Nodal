import math
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QRectF, QLineF
from PyQt5.QtGui import QPainter, QPen, QColor, QTransform

# Import du modèle et des éléments graphiques
from model.components import Resistor, VoltageSourceDC, VoltageSourceAC, Capacitor, Inductor
from model.node import Node
from .component_item import create_component_item

class CircuitView(QGraphicsView):
    """
    Widget qui affiche la scène du circuit
    """
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.centerOn(0, 0)

    def wheelEvent(self, event):
        """Ctrl + Molette"""
        if event.modifiers() & Qt.ControlModifier:
            zoom_in_factor = 1.25
            zoom_out_factor = 1 / zoom_in_factor

            # Sens de la molette
            if event.angleDelta().y() > 0:
                zoom_factor = zoom_in_factor
            else:
                zoom_factor = zoom_out_factor

            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)

class CircuitScene(QGraphicsScene):
    """
    La scène qui contient tous les objets graphiques et gère la logique d'édition
    """
    # Grid settings
    GRID_SIZE = 20

    def __init__(self, model):
        super().__init__()
        self.model = model
        
        # TODO faire en sorte que la scène soit infinie ou semi-infinie
        self.setSceneRect(-2000, -2000, 4000, 4000)
        
        self.current_tool = "pointer"
        
        # Variables temporaires pour dessiner des fils
        self.temp_wire_line = None
        self.start_node = None

    def set_tool(self, tool_name):
        """Change l'outil actif"""
        self.current_tool = tool_name

    def drawBackground(self, painter, rect):
        """Dessine une grille de points pour aider à l'alignement"""
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        # On calcule les points visibles pour ne pas tout dessiner
        left = int(rect.left()) - (int(rect.left()) % self.GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % self.GRID_SIZE)
        
        points = []
        for x in range(left, int(rect.right()), self.GRID_SIZE):
            for y in range(top, int(rect.bottom()), self.GRID_SIZE):
                points.append(QPointF(x, y))
        
        painter.drawPoints(points)

    def snap_to_grid(self, pos):
        """Arrondit une position x,y au point de grille le plus proche"""
        x = round(pos.x() / self.GRID_SIZE) * self.GRID_SIZE
        y = round(pos.y() / self.GRID_SIZE) * self.GRID_SIZE
        return x, y

    def mousePressEvent(self, event):
        """Gère le clic souris selon l'outil sélectionné"""
        
        # Position exacte du clic
        scene_pos = event.scenePos()
        # Position avec quadrillage
        grid_x, grid_y = self.snap_to_grid(scene_pos)

        # Left click
        if event.button() == Qt.LeftButton:
            if self.current_tool == "pointer":
                super().mousePressEvent(event)
            elif self.current_tool == "wire":
                # Logique fil
                # TODO: implémenter la création de Node et Wire
                super().mousePressEvent(event)
            elif self.current_tool in ["resistor", "source_dc"]:
                self.add_component_at(self.current_tool, grid_x, grid_y)
        else:
            super().mousePressEvent(event)

    def add_component_at(self, tool_type, x, y):
        """Crée un composant"""
        node_a = self.model.create_node(x - 30, y)
        node_b = self.model.create_node(x + 30, y)
        
        dipole = None
        d_id = self.model.get_next_dipole_id()

        # 2. Création de l'objet Modèle
        if tool_type == "resistor":
            dipole = Resistor(d_id, node_a, node_b, x, y, name=f"R{d_id}")
        elif tool_type == "source_dc":
            dipole = VoltageSourceDC(d_id, node_a, node_b, x, y, name=f"V{d_id}")

        if dipole:
            self.model.add_dipole(dipole)

            item = create_component_item(dipole)
            self.addItem(item)

    def refresh_from_model(self):
        """
        Vide la scène et la reconstruit entièrement depuis le modèle
        """
        self.clear()
        
        # On parcourt les dipôles du modèle
        for dipole in self.model.dipoles.values():
            item = create_component_item(dipole)
            self.addItem(item)
            
        # TODO: parcourir et dessiner les fils
        # for wire in self.model.wires.values():