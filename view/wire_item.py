from PyQt5.QtWidgets import QGraphicsLineItem, QStyleOptionGraphicsItem, QStyle
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt, QLineF

class WireItem(QGraphicsLineItem):
    """
    Représentation graphique d'un fil électrique
    Relie visuellement deux coordonnées
    """
    def __init__(self, wire_model):
        super().__init__()
        self.wire = wire_model
        
        # Style du fil
        self.setPen(QPen(Qt.black, 2))
        
        # On rend le fil sélectionnable
        self.setFlags(QGraphicsLineItem.ItemIsSelectable)
        
        # Initialisation de la position
        self.update_position()

    def update_position(self):
        """Met à jour les coordonnées de la ligne graphique depuis le modèle"""
        if self.wire.node_a and self.wire.node_b:
            x1, y1 = self.wire.node_a.position
            x2, y2 = self.wire.node_b.position
            self.setLine(QLineF(x1, y1, x2, y2))

    def paint(self, painter, option, widget):
        """Change la couleur du fil si sélectionné"""
        # On applique le style de base
        painter.setPen(self.pen())
        
        # Si sélectionné, on change la couleur
        if option.state & QStyle.State_Selected:
            pen = QPen(QColor("#0078d7"), 3)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            
        painter.drawLine(self.line())