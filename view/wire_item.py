from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsRectItem, QGraphicsItem
from PyQt5.QtGui import QPen, QColor, QBrush, QPainterPath, QPainterPathStroker
from PyQt5.QtCore import Qt, QPointF, QLineF

class WireHandle(QGraphicsRectItem):
    def __init__(self, parent_wire):
        # Centered 8x8 square
        super().__init__(-4, -4, 8, 8, parent=parent_wire)
        self.parent_wire = parent_wire
        
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 1))
        
        self.setFlags(QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(2)  # Always on top of the wire
        self.setCursor(Qt.PointingHandCursor)
        self.setVisible(False)
        
        # Drag state
        self._is_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            # Capture the mouse to keep receiving move events
            event.accept() 
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            # Mouse position
            mouse_scene_pos = self.mapToScene(event.pos())
            
            # Snapping
            target_pos = self.scene().get_snapped_position(mouse_scene_pos)
            target_pos = QPointF(*target_pos)

            # Convert to parent-local coordinates
            new_pos_in_parent = self.parentItem().mapFromScene(target_pos)
            
            # Apply move
            self.setPos(new_pos_in_parent)
            
            # Update visuals
            self.parent_wire.update_line_visuals()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            # End of move: let the scene finalize snapping and model updates
            self.scene().handle_wire_move(self.parent_wire)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class WireItem(QGraphicsLineItem):
    def __init__(self, wire_model):
        super().__init__()
        self.wire = wire_model
        
        self.setPen(QPen(Qt.black, 2))
        self.setFlags(QGraphicsItem.ItemIsSelectable | 
                      QGraphicsItem.ItemIsMovable | 
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(0)  # Wire below handles
        
        self.handle_a = WireHandle(self)
        self.handle_b = WireHandle(self)
        
        self.refresh_geometry()

    def refresh_geometry(self):
        """
        Reset the wire and handles from model coordinates.
        """
        if not self.wire.node_a or not self.wire.node_b:
            return

        # Reset parent to absolute origin
        self.prepareGeometryChange()
        self.setPos(0, 0)

        # Absolute coordinates
        p1 = QPointF(*self.wire.node_a.position)
        p2 = QPointF(*self.wire.node_b.position)

        # Place elements at those coordinates
        self.handle_a.setPos(p1)
        self.handle_b.setPos(p2)
        self.setLine(QLineF(p1, p2))

    def update_line_visuals(self):
        """Update only the line between the handles."""
        self.setLine(QLineF(self.handle_a.pos(), self.handle_b.pos()))

    def shape(self):
        """Return a thicker hit area to make wire selection easier."""
        path = QPainterPath()
        path.moveTo(self.line().p1())
        path.lineTo(self.line().p2())
        stroker = QPainterPathStroker()
        stroker.setWidth(12)
        return stroker.createStroke(path)

    def _node_shared_with_dipole(self, node, model):
        """Return True if the node is referenced by any dipole."""
        if node is None:
            return False
        for dipole in model.dipoles.values():
            if dipole.node_a is node or dipole.node_b is node:
                return True
        return False

    def apply_scene_delta(self, delta, detach_shared_nodes=False, moved_node_ids=None):
        """Move a wire via its nodes, with optional endpoint snapping."""
        scene = self.scene()
        if scene is None:
            return
        model = scene.model
        if model is None:
            return
        if not self.wire.node_a or not self.wire.node_b:
            return

        shared_a = self._node_shared_with_dipole(self.wire.node_a, model)
        shared_b = self._node_shared_with_dipole(self.wire.node_b, model)

        if detach_shared_nodes:
            if shared_a:
                ax, ay = self.wire.node_a.position
                self.wire.node_a = model.create_node(ax, ay)
                shared_a = False
            if shared_b:
                bx, by = self.wire.node_b.position
                self.wire.node_b = model.create_node(bx, by)
                shared_b = False

        ax, ay = self.wire.node_a.position
        bx, by = self.wire.node_b.position

        if moved_node_ids is None:
            moved_node_ids = set()

        # If nodes were detached, endpoints can snap independently
        # Otherwise, attached endpoints must be driven by moved dipoles
        should_snap_endpoints = detach_shared_nodes

        node_a_id = id(self.wire.node_a)
        if node_a_id not in moved_node_ids:
            if shared_a and not detach_shared_nodes:
                # Keep attachment: the selected dipole updates this node
                moved_node_ids.add(node_a_id)
            else:
                ax += delta.x()
                ay += delta.y()
                if should_snap_endpoints:
                    snapped_a = scene.get_snapped_position(QPointF(ax, ay))
                    self.wire.node_a.position = (snapped_a[0], snapped_a[1])
                else:
                    self.wire.node_a.position = (ax, ay)
                moved_node_ids.add(node_a_id)

        node_b_id = id(self.wire.node_b)
        if node_b_id not in moved_node_ids:
            if shared_b and not detach_shared_nodes:
                # Keep attachment, the selected dipole updates this node
                moved_node_ids.add(node_b_id)
            else:
                bx += delta.x()
                by += delta.y()
                if should_snap_endpoints:
                    snapped_b = scene.get_snapped_position(QPointF(bx, by))
                    self.wire.node_b.position = (snapped_b[0], snapped_b[1])
                else:
                    self.wire.node_b.position = (bx, by)
                moved_node_ids.add(node_b_id)

        self.refresh_geometry()

    def itemChange(self, change, value):
        # Position snapping
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            grid_size = self.scene().GRID_SIZE
            x = round(new_pos.x() / grid_size) * grid_size
            y = round(new_pos.y() / grid_size) * grid_size
            return QPointF(x, y)

        # Selection visuals
        if change == QGraphicsItem.ItemSelectedChange:
            # Avoid unnecessary itemChange churn
            is_selected = bool(value)
            if self.handle_a.isVisible() != is_selected:
                self.handle_a.setVisible(is_selected)
                self.handle_b.setVisible(is_selected)
                
                pen = self.pen()
                if is_selected:
                    pen.setColor(QColor("#0078d7"))
                    pen.setStyle(Qt.DashLine)
                    self.setZValue(1) 
                else:
                    pen.setColor(Qt.black)
                    pen.setStyle(Qt.SolidLine)
                    self.setZValue(0)
                self.setPen(pen)

        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        """Finalize a full-wire drag."""
        super().mouseReleaseEvent(event)
        
        # If the whole wire moved
        if self.pos().manhattanLength() > 0.1:
             if self.scene():
                 self.scene().handle_wire_move(self)