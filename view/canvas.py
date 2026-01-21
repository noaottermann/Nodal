import math
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QRectF, QLineF
from PyQt5.QtGui import QPainter, QPen, QColor, QTransform

# Import du modèle et des éléments graphiques
from model.components import Resistor, VoltageSourceDC, VoltageSourceAC, Capacitor, Inductor
from model.node import Node
from view.grid import Grid
from .component_item import create_component_item
from .wire_item import WireItem

class CircuitView(QGraphicsView):
    """
    Widget qui affiche la scène du circuit
    """
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.set_tool_mode("pointer")
        
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.centerOn(0, 0)
        
        # Variables pour le déplacement manuel
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0

    def set_tool_mode(self, tool_name):
        """Configure le comportement de la souris selon l'outil"""
        if tool_name == "pointer":
            # Clic gauche sélectionne, Clic-glissé fait un rectangle
            self.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            # Mode dessin
            self.setDragMode(QGraphicsView.NoDrag)

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
        
    def mousePressEvent(self, event):
        # Clic molette
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start_x = event.x()
            self._pan_start_y = event.y()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            # On remet le curseur normal
            self.setCursor(Qt.ArrowCursor) 
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            # Calcul du déplacement de la souris
            dx = event.x() - self._pan_start_x
            dy = event.y() - self._pan_start_y
            
            self._pan_start_x = event.x()
            self._pan_start_y = event.y()
            
            # On déplace les scrollbars invisibles pour fai
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - dx)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - dy)
            event.accept()
        else:
            super().mouseMoveEvent(event)

class CircuitScene(QGraphicsScene):
    """
    La scène qui contient tous les objets graphiques et gère la logique d'édition
    """
    # Grid settings
    GRID_SIZE = 20

    def __init__(self, model):
        super().__init__()
        self.model = model
  
        limit = 1000000 
        self.setSceneRect(-limit, -limit, limit * 2, limit * 2)
        
        self.grid = Grid(grid_size=20)
        
        self.current_tool = "pointer"

        # Variables temporaires pour dessiner des fils
        self.drawing_wire = False
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
    
    def get_snapped_position(self, scene_pos):
        """
        Retourne les coordonnées (x, y) aimantées
        Priorité 1 : Un noeud existant
        Priorité 2 : La grille
        """
        # Seuil d'aimantation
        THRESHOLD = 15.0
        
        mx, my = scene_pos.x(), scene_pos.y()
        
        closest_node_pos = None
        min_dist = float('inf')

        # Trouve le noeud le plus proche
        for node in self.model.nodes.values():
            nx, ny = node.position
            # Calcul de distance
            dist = ((mx - nx)**2 + (my - ny)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest_node_pos = (nx, ny)

        if closest_node_pos and min_dist < THRESHOLD:
            print(f"[Snap] Aimanté sur le noeud à {closest_node_pos}")
            return closest_node_pos
        
        return self.snap_to_grid(scene_pos)

    def mousePressEvent(self, event):
        """Gère le clic souris selon l'outil sélectionné"""
        
        # Position exacte du clic
        scene_pos = event.scenePos()
        # Position avec quadrillage
        grid_x, grid_y = self.get_snapped_position(scene_pos)

        # Left click
        if event.button() == Qt.LeftButton:
            if self.current_tool == "pointer":
                super().mousePressEvent(event)
            elif self.current_tool == "wire":
                self.start_wire_drawing(grid_x, grid_y)
                event.accept()
            else:
                self.add_component_at(self.current_tool, grid_x, grid_y)
                event.accept()
                if self.current_tool == "pointer":
                    super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Gère le déplacement de la souris"""
        super().mouseMoveEvent(event)

        if self.current_tool == "wire" and self.drawing_wire and self.temp_wire_item:
            new_pos = event.scenePos()
            grid_x, grid_y = self.get_snapped_position(new_pos)
            
            # Mise à jour visuelle de la ligne
            line = self.temp_wire_item.line()
            line.setP2(QPointF(grid_x, grid_y))
            self.temp_wire_item.setLine(line)

    def mouseReleaseEvent(self, event):
        """Action quand on lâche le clic gauche"""
        if event.button() == Qt.LeftButton:
            
            if self.current_tool == "wire" and self.drawing_wire:
                # Fin du fil
                scene_pos = event.scenePos()
                grid_x, grid_y = self.get_snapped_position(scene_pos)
                self.finish_wire_drawing(grid_x, grid_y)
                event.accept()
                
            else:
                super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

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
        elif tool_type == "source_ac":
            dipole = VoltageSourceAC(d_id, node_a, node_b, x, y, name=f"V{d_id}")
        elif tool_type == "capacitor":
            dipole = Capacitor(d_id, node_a, node_b, x, y, name=f"C{d_id}")
        elif tool_type == "inductor":
            dipole = Inductor(d_id, node_a, node_b, x, y, name=f"L{d_id}")

        if dipole:
            self.model.add_dipole(dipole)

            item = create_component_item(dipole)
            self.addItem(item)

    def start_wire_drawing(self, x, y):
        """Initialise le mode dessin de fil"""
        self.drawing_wire = True
        self.start_pos = (x, y)
        
        # Création visuelle du fil temporaire
        self.temp_wire_item = QGraphicsLineItem(x, y, x, y)
        pen = QPen(Qt.gray, 2, Qt.DashLine)
        self.temp_wire_item.setPen(pen)
        self.addItem(self.temp_wire_item)

    def finish_wire_drawing(self, x, y):
        """Valide le fil et l'ajoute au modèle"""
        
        start_x, start_y = self.start_pos
        
        # Nettoyage du visuel temporaire
        self.removeItem(self.temp_wire_item)
        self.temp_wire_item = None
        self.drawing_wire = False
        
        # On ne crée pas de fil de longueur nulle
        if start_x == x and start_y == y:
            return

        # Modèle
        # Trouver ou créer le Node de départ
        node_a = self.model.get_node_at(start_x, start_y)
        if not node_a:
            node_a = self.model.create_node(start_x, start_y)
            
        # Trouver ou créer le Node d'arrivée
        node_b = self.model.get_node_at(x, y)
        if not node_b:
            node_b = self.model.create_node(x, y)

        # Créer le Wire dans le modèle
        try:
            wire = self.model.create_wire(node_a, node_b)
            
            # Créer le Wire visuel final
            wire_item = WireItem(wire)
            self.addItem(wire_item)
            
        except Exception as e:
            print(f"[Erreur] Impossible de créer le fil : {e}")

    def cancel_wire_drawing(self):
        """Annule l'opération en cours"""
        if self.temp_wire_item:
            self.removeItem(self.temp_wire_item)
            self.temp_wire_item = None
        self.drawing_wire = False

    def delete_selection(self):
        """Supprime tous les items sélectionnés"""
        for item in self.selectedItems():
            # Supprime du modèle
            # On vérifie si l'item est un ComponentItem
            if hasattr(item, 'component'):
                dipole_id = item.component.id
                # On supprime dans le dictionnaire du modèle
                self.model.remove_dipole(dipole_id)
            
            # Supprime de la scène
            self.removeItem(item)

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