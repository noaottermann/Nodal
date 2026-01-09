from PyQt5.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QStyle
from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QPainterPath

from model.components import Resistor, VoltageSourceDC, VoltageSourceAC, Capacitor, Inductor

class ComponentItem(QGraphicsItem):
    """
    Classe de base graphique pour tous les dipôles
    """

    def __init__(self, component_model):
        super().__init__()
        self.component = component_model
        
        # Interaction settings
        self.setFlags(QGraphicsItem.ItemIsMovable | 
                      QGraphicsItem.ItemIsSelectable | 
                      QGraphicsItem.ItemSendsGeometryChanges)
        
        # Position et rotation initiales
        x, y = self.component.position
        self.setPos(x, y)
        self.setRotation(self.component.rotation)

        # Standard dimensions
        self.width = 60
        self.height = 40
        
        # Tooltip
        self.setToolTip(f"{self.component.name} (ID: {self.component.id})")

    def boundingRect(self):
        """
        Définit la zone rectangulaire interactive du composant
        """
        margin = 5
        return QRectF(-self.width/2 - margin, -self.height/2 - margin, self.width + 2*margin, self.height + 2*margin)

    def itemChange(self, change, value):
        """
        Méthode appelée par Qt quand l'état de l'item change
        """
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Mise à jour des coordonnées dans le modèle
            new_pos = value
            self.component.position = (new_pos.x(), new_pos.y())
        return super().itemChange(change, value)

    def paint(self, painter, option, widget=None):
        """
        Dessine le cadre de sélection et appelle le dessin spécifique
        """
        painter.setRenderHint(QPainter.Antialiasing)
        is_selected = option.state & QStyle.State_Selected
        if is_selected:
            pen = QPen(Qt.DashLine)
            pen.setColor(QColor("#0078d7"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(self.boundingRect())
        self.draw_symbol(painter)
        self.draw_labels(painter)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.red)
        painter.drawEllipse(QPointF(-30, 0), 2, 2)
        painter.setBrush(Qt.black)
        painter.drawEllipse(QPointF(30, 0), 2, 2)

    def draw_labels(self, painter):
        """Affiche le nom et la valeur principale"""
        painter.setPen(QColor("black"))
        font = QFont("Arial", 8)
        painter.setFont(font)

        name_rect = QRectF(-30, -35, 60, 15)
        painter.drawText(name_rect, Qt.AlignCenter, self.component.name)
        
        value_text = self.get_value_text()
        val_rect = QRectF(-30, 20, 60, 15)
        painter.drawText(val_rect, Qt.AlignCenter, value_text)

    def draw_symbol(self, painter):
        """À override par les classes filles"""
        pass

    def get_value_text(self):
        """À override pour afficher la bonne unité"""
        return ""

# Dessin des symboles

class ResistorItem(ComponentItem):
    def draw_symbol(self, painter):
        pen = QPen(QColor("black"), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Style Européen (Rectangle)
        # Lignes de connexion
        painter.drawLine(-30, 0, -15, 0) # Gauche
        painter.drawLine(15, 0, 30, 0)   # Droite
        
        # Le corps (Rectangle)
        rect = QRectF(-15, -8, 30, 16)
        painter.drawRect(rect)
    
    def get_value_text(self):
        # On accède aux propriétés spécifiques du modèle
        if hasattr(self.component, 'resistance'):
            return f"{self.component.resistance} Ω"
        return ""

class VoltageSourceItem(ComponentItem):
    def draw_symbol(self, painter):
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Lignes
        painter.drawLine(-30, 0, -15, 0)
        painter.drawLine(15, 0, 30, 0)
        
        # Cercle
        painter.drawEllipse(QPointF(0, 0), 15, 15)
        
        # Symboles +/- ou ~
        painter.setPen(QPen(Qt.black, 1))
        
        if isinstance(self.component, VoltageSourceDC):
            # Ligne verticale pour le +
            painter.drawLine(-8, -5, -8, 5)
            painter.drawLine(-11, 0, -5, 0)
        elif isinstance(self.component, VoltageSourceAC):
            # Tilde (~)
            path = QPainterPath()
            path.moveTo(-7, 2)
            path.cubicTo(-2, -5, 2, 5, 7, -2)
            painter.drawPath(path)

    def get_value_text(self):
        if isinstance(self.component, VoltageSourceDC):
            return f"{self.component.dc_voltage} V"
        elif isinstance(self.component, VoltageSourceAC):
            return f"{self.component.amplitude} V"
        return ""

class CapacitorItem(ComponentItem):
    def draw_symbol(self, painter):
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        
        # Lignes
        painter.drawLine(-30, 0, -5, 0)
        painter.drawLine(5, 0, 30, 0)
        
        # Plaques verticales
        painter.drawLine(-5, -12, -5, 12)
        painter.drawLine(5, -12, 5, 12)

    def get_value_text(self):
        return f"{self.component.capacitance} F"

class InductorItem(ComponentItem):
    def draw_symbol(self, painter):
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Lignes
        painter.drawLine(-30, 0, -15, 0)
        painter.drawLine(15, 0, 30, 0)
        
        # Arches
        painter.drawArc(-15, -5, 10, 10, 0, 180 * 16)
        painter.drawArc(-5, -5, 10, 10, 0, 180 * 16)
        painter.drawArc(5, -5, 10, 10, 0, 180 * 16)

    def get_value_text(self):
        return f"{self.component.inductance} H"

def create_component_item(component_model):
    """
    Fonction utilitaire qui retourne la bonne classe graphique 
    en fonction de l'objet modèle fourni.
    """
    if isinstance(component_model, Resistor):
        return ResistorItem(component_model)
    elif isinstance(component_model, (VoltageSourceDC, VoltageSourceAC)):
        return VoltageSourceItem(component_model)
    elif isinstance(component_model, Capacitor):
        return CapacitorItem(component_model)
    elif isinstance(component_model, Inductor):
        return InductorItem(component_model)
    else:
        # Fallback pour composants inconnus
        return ComponentItem(component_model)