import math

from PyQt5.QtWidgets import QGraphicsItem, QStyle, QApplication
from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QPainterPath

from model.components import Resistor, VoltageSourceDC, VoltageSourceAC, Capacitor, Inductor

class ComponentItem(QGraphicsItem):
    """
    Base graphics item for all dipoles.
    """

    def __init__(self, component_model):
        super().__init__()
        self.component = component_model

        self._press_scene_pos = None
        self._drag_started = False
        self._is_rotating = False
        self._rotate_start_angle = 0.0
        self._rotate_start_rotation = 0.0
        
        # Interaction settings
        self.setFlags(
            QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        
        # Initial position and rotation
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
        Define the interactive rectangular area for the component.
        """
        margin = 5
        return QRectF(-self.width/2 - margin, -self.height/2 - margin, self.width + 2*margin, self.height + 2*margin)

    def shape(self):
        """Use a tighter shape so clicks in empty space don't grab the item."""
        path = QPainterPath()
        path.addRect(QRectF(-self.width / 2, -self.height / 2, self.width, self.height))
        return path

    def itemChange(self, change, value):
        # Snapping
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            grid_size = self.scene().GRID_SIZE
            x = round(new_pos.x() / grid_size) * grid_size
            y = round(new_pos.y() / grid_size) * grid_size  
            snapped_pos = QPointF(x, y)
            self.scene().update_wires_connected_to(self.component, snapped_pos, self.rotation())
            return snapped_pos

        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        """
        Called when the component is released after a move.
        """
        if self._is_rotating and event.button() == Qt.RightButton:
            self._is_rotating = False
            if self.scene():
                self.scene().handle_component_move(self)
            event.accept()
            return
        super().mouseReleaseEvent(event)

        self._drag_started = False
        self._press_scene_pos = None
        
        # Ask the scene to update connections
        if self.scene():
            self.scene().handle_component_move(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            center = self.mapToScene(QPointF(0, 0))
            dx = event.scenePos().x() - center.x()
            dy = event.scenePos().y() - center.y()
            self._rotate_start_angle = math.degrees(math.atan2(dy, dx))
            self._rotate_start_rotation = self.rotation()
            self._is_rotating = True
            if self.scene() and hasattr(self.scene(), "_push_undo_snapshot"):
                self.scene()._push_undo_snapshot()
            event.accept()
            return
        self._press_scene_pos = event.scenePos()
        self._drag_started = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_rotating:
            center = self.mapToScene(QPointF(0, 0))
            dx = event.scenePos().x() - center.x()
            dy = event.scenePos().y() - center.y()
            current_angle = math.degrees(math.atan2(dy, dx))
            delta = current_angle - self._rotate_start_angle
            new_rotation = (self._rotate_start_rotation + delta) % 360
            self.setRotation(new_rotation)
            self.component.rotation = float(new_rotation)
            if self.scene():
                self.scene().update_wires_connected_to(self.component, self.pos(), new_rotation)
            event.accept()
            return
        if not self._drag_started and self._press_scene_pos is not None:
            drag_distance = (event.scenePos() - self._press_scene_pos).manhattanLength()
            if drag_distance < QApplication.startDragDistance():
                event.ignore()
                return
            self._drag_started = True

        super().mouseMoveEvent(event)

    def update_model_nodes(self):
        """
        Recompute node A and B positions from the component center and rotation.
        """
        # Component center
        cx, cy = self.pos().x(), self.pos().y()
        rotation = self.rotation()
        
        # Standard terminal offset from the center
        offset = 30
        
        # Trigonometric calculation
        rad = math.radians(rotation)
        dx = offset * math.cos(rad)
        dy = offset * math.sin(rad)
        
        # Update node coordinates
        self.component.node_a.position = (cx - dx, cy - dy)
        
        self.component.node_b.position = (cx + dx, cy + dy)
        
        # Update dipole position
        self.component.position = (cx, cy)

    def paint(self, painter, option, widget=None):
        """
        Draw selection bounds and the specific symbol.
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
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.red)
        painter.drawEllipse(QPointF(-30, 0), 2, 2)
        painter.setBrush(Qt.black)
        painter.drawEllipse(QPointF(30, 0), 2, 2)


    def draw_labels(self, painter):
        """Draw the name and primary value."""
        painter.setPen(QColor("black"))
        font = QFont("Arial", 8)
        painter.setFont(font)

        name_rect = QRectF(-30, -35, 60, 15)
        painter.drawText(name_rect, Qt.AlignCenter, self.component.name)
        
        value_text = self.get_value_text()
        val_rect = QRectF(-30, 20, 60, 15)
        painter.drawText(val_rect, Qt.AlignCenter, value_text)

    def draw_symbol(self, painter):
        """Override in subclasses to draw the symbol."""
        pass

    def get_value_text(self):
        """Override to provide the displayed unit/value."""
        return ""

# Symbol drawing

class ResistorItem(ComponentItem):
    def draw_symbol(self, painter):
        pen = QPen(QColor("black"), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # European style (rectangle)
        # Connection lines
        painter.drawLine(-30, 0, -15, 0)  # Left
        painter.drawLine(15, 0, 30, 0)    # Right
        
        # Body (rectangle)
        rect = QRectF(-15, -8, 30, 16)
        painter.drawRect(rect)
    
    def get_value_text(self):
        # Access model-specific properties
        if hasattr(self.component, 'resistance'):
            return f"{self.component.resistance} Ω"
        return ""

class VoltageSourceItem(ComponentItem):
    def draw_symbol(self, painter):
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Lines
        painter.drawLine(-30, 0, -15, 0)
        painter.drawLine(15, 0, 30, 0)
        
        # Circle
        painter.drawEllipse(QPointF(0, 0), 15, 15)
        
        # Symbols +/- or ~
        painter.setPen(QPen(Qt.black, 1))
        
        if isinstance(self.component, VoltageSourceDC):
            # Vertical line for +
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
        
        # Lines
        painter.drawLine(-30, 0, -5, 0)
        painter.drawLine(5, 0, 30, 0)
        
        # Vertical plates
        painter.drawLine(-5, -12, -5, 12)
        painter.drawLine(5, -12, 5, 12)

    def get_value_text(self):
        return f"{self.component.capacitance} F"

class InductorItem(ComponentItem):
    def draw_symbol(self, painter):
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Lines
        painter.drawLine(-30, 0, -15, 0)
        painter.drawLine(15, 0, 30, 0)
        
        # Arcs
        painter.drawArc(-15, -5, 10, 10, 0, 180 * 16)
        painter.drawArc(-5, -5, 10, 10, 0, 180 * 16)
        painter.drawArc(5, -5, 10, 10, 0, 180 * 16)

    def get_value_text(self):
        return f"{self.component.inductance} H"

def create_component_item(component_model):
    """
    Helper that returns the proper graphics item for a model object.
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
        # Fallback for unknown components
        return ComponentItem(component_model)