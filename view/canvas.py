import math
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsRectItem, QApplication
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QTransform, QBrush

# Model and graphics items
from model.components import Resistor, VoltageSourceDC, VoltageSourceAC, Capacitor, Inductor
from .component_item import ComponentItem, create_component_item
from .wire_item import WireHandle, WireItem
from .components_panel import ComponentsListWidget

class CircuitView(QGraphicsView):
    """Graphics view that renders the circuit scene."""
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.set_tool_mode("pointer")
        
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.centerOn(0, 0)

        self.setAcceptDrops(True)

        self._ghost_preview = None
        self._ghost_tool_id = None
        
        # Manual panning state
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0

    def set_tool_mode(self, tool_name):
        """Configure mouse behavior based on the active tool."""
        if tool_name == "pointer":
            # Left click selects, drag draws a rubber band
            self.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            # Drawing mode
            self.setDragMode(QGraphicsView.NoDrag)

    def wheelEvent(self, event):
        """Ctrl + mouse wheel zooms the view."""
        if event.modifiers() & Qt.ControlModifier:
            zoom_in_factor = 1.25
            zoom_out_factor = 1 / zoom_in_factor

            # Wheel direction
            if event.angleDelta().y() > 0:
                zoom_factor = zoom_in_factor
            else:
                zoom_factor = zoom_out_factor

            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)
        
    def mousePressEvent(self, event):
        if self._handle_pan_press(event):
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._handle_pan_release(event):
            return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._handle_pan_move(event):
            return
        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        tool_name = self._drag_component_tool(event)
        if tool_name is None:
            super().dragEnterEvent(event)
            return
        self._ensure_ghost_preview(tool_name)
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        tool_name = self._drag_component_tool(event)
        if tool_name is None:
            super().dragMoveEvent(event)
            return
        self._ensure_ghost_preview(tool_name)
        self._update_ghost_position(event)
        event.acceptProposedAction()

    def dropEvent(self, event):
        tool_name = self._drag_component_tool(event)
        if tool_name is None:
            self._clear_ghost_preview()
            super().dropEvent(event)
            return

        self._drop_component_at(event, tool_name)
        self._clear_ghost_preview()
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._clear_ghost_preview()
        super().dragLeaveEvent(event)

    def _handle_pan_press(self, event):
        if event.button() != Qt.MiddleButton:
            return False
        self._is_panning = True
        self._pan_start_x = event.x()
        self._pan_start_y = event.y()
        self.setCursor(Qt.ClosedHandCursor)
        event.accept()
        return True

    def _handle_pan_release(self, event):
        if event.button() != Qt.MiddleButton:
            return False
        self._is_panning = False
        self.setCursor(Qt.ArrowCursor)
        event.accept()
        return True

    def _handle_pan_move(self, event):
        if not self._is_panning:
            return False
        dx = event.x() - self._pan_start_x
        dy = event.y() - self._pan_start_y
        self._pan_start_x = event.x()
        self._pan_start_y = event.y()
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - dx)
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - dy)
        event.accept()
        return True

    def _drag_component_tool(self, event):
        if not event.mimeData().hasFormat(ComponentsListWidget.MIME_TYPE):
            return None
        component_id = bytes(
            event.mimeData().data(ComponentsListWidget.MIME_TYPE)
        ).decode("utf-8")
        return self._component_id_to_tool(component_id)

    def _update_ghost_position(self, event):
        if self._ghost_preview is None:
            return
        scene_pos = self.mapToScene(event.pos())
        if hasattr(self.scene(), "get_snapped_position"):
            grid_x, grid_y = self.scene().get_snapped_position(scene_pos)
        else:
            grid_x, grid_y = scene_pos.x(), scene_pos.y()
        self._ghost_preview.setPos(grid_x, grid_y)

    def _drop_component_at(self, event, tool_name):
        scene_pos = self.mapToScene(event.pos())
        if hasattr(self.scene(), "get_snapped_position"):
            grid_x, grid_y = self.scene().get_snapped_position(scene_pos)
        else:
            grid_x, grid_y = scene_pos.x(), scene_pos.y()
        self.scene().add_component_at(tool_name, grid_x, grid_y)

    def _component_id_to_tool(self, component_id):
        if component_id.startswith("source_fake_"):
            return "source_dc"
        if component_id.startswith("passive_fake_"):
            return "resistor"
        if component_id.startswith("measurement_fake_"):
            return None

        return component_id

    def _ensure_ghost_preview(self, tool_name):
        if tool_name is None:
            self._clear_ghost_preview()
            return

        if self._ghost_preview is not None and self._ghost_tool_id == tool_name:
            return

        self._clear_ghost_preview()
        self._ghost_tool_id = tool_name

        ghost = QGraphicsRectItem(-30, -20, 60, 40)
        pen = QPen(QColor("#7a6a3a"), 2, Qt.DashLine)
        ghost.setPen(pen)
        ghost.setBrush(QBrush(Qt.NoBrush))
        ghost.setOpacity(0.7)
        ghost.setZValue(10)

        if self.scene() is not None:
            self.scene().addItem(ghost)
        self._ghost_preview = ghost

    def _clear_ghost_preview(self):
        if self._ghost_preview is None:
            self._ghost_tool_id = None
            return
        if self.scene() is not None:
            self.scene().removeItem(self._ghost_preview)
        self._ghost_preview = None
        self._ghost_tool_id = None

class CircuitScene(QGraphicsScene):
    """Scene that hosts items and handles editing logic."""
    # Grid settings
    GRID_SIZE = 20

    def __init__(self, model):
        super().__init__()
        self.model = model
  
        limit = 1000000 
        self.setSceneRect(-limit, -limit, limit * 2, limit * 2)
        
        self.current_tool = "pointer"

        # Temporary state for wire drawing
        self.drawing_wire = False
        self.temp_wire_item = None
        self.start_pos = (0, 0)
        self._group_move_active = False
        self._drag_started_on_item = False
        self._press_scene_pos = None
        self._suppress_move_until_release = False
        self._selection_snapshot = None

        # Undo state (stores full circuit snapshots before edits)
        self._undo_stack = []
        self._redo_stack = []
        self._max_undo_steps = 100
        self._component_classes = {
            "Resistor": Resistor,
            "VoltageSourceDC": VoltageSourceDC,
            "VoltageSourceAC": VoltageSourceAC,
            "Capacitor": Capacitor,
            "Inductor": Inductor,
        }

    def set_tool(self, tool_name):
        """Set the active tool name."""
        self.current_tool = tool_name

    def _push_undo_snapshot(self):
        """Store the current circuit state before a mutating action."""
        if self.model is None:
            return
        snapshot = self.model.to_json()
        if self._undo_stack and self._undo_stack[-1] == snapshot:
            return
        # New user edits invalidate redo history.
        self._redo_stack.clear()
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self._max_undo_steps:
            self._undo_stack.pop(0)

    def undo_last_action(self):
        """Restore the most recent snapshot from the undo stack."""
        if self.model is None or not self._undo_stack:
            return False

        current_snapshot = self.model.to_json()
        previous_snapshot = self._undo_stack.pop()
        self._redo_stack.append(current_snapshot)
        self.model.load_from_json(previous_snapshot, self._component_classes)
        self.refresh_from_model()

        # Reset transient interaction state after restore
        self.cancel_wire_drawing()
        self._reset_press_state()
        self.clearSelection()
        self._group_move_active = False
        return True

    def redo_last_action(self):
        """Reapply the most recently undone snapshot."""
        if self.model is None or not self._redo_stack:
            return False

        current_snapshot = self.model.to_json()
        next_snapshot = self._redo_stack.pop()
        self._undo_stack.append(current_snapshot)
        if len(self._undo_stack) > self._max_undo_steps:
            self._undo_stack.pop(0)

        self.model.load_from_json(next_snapshot, self._component_classes)
        self.refresh_from_model()

        self.cancel_wire_drawing()
        self._reset_press_state()
        self.clearSelection()
        self._group_move_active = False
        return True

    def drawBackground(self, painter, rect):
        """Draw the background point grid for alignment."""
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        
        # Only draw visible points
        left = int(rect.left()) - (int(rect.left()) % self.GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % self.GRID_SIZE)
        
        points = []
        for x in range(left, int(rect.right()), self.GRID_SIZE):
            for y in range(top, int(rect.bottom()), self.GRID_SIZE):
                points.append(QPointF(x, y))
        
        painter.drawPoints(points)

    def snap_to_grid(self, pos):
        """Round an (x, y) position to the nearest grid point."""
        gs = self.GRID_SIZE
        x = round(pos.x() / gs) * gs
        y = round(pos.y() / gs) * gs
        return x, y
    
    def get_snapped_position(self, scene_pos):
        """
        Return snapped (x, y) coordinates.
        Priority 1: existing node
        Priority 2: grid
        """
        # Snap threshold in scene units
        THRESHOLD = 15.0
        
        mx, my = scene_pos.x(), scene_pos.y()
        
        closest_node_pos = None
        min_dist = float('inf')

        # Find the closest node
        for node in self.model.nodes.values():
            nx, ny = node.position
            # Distance calculation
            dist = ((mx - nx)**2 + (my - ny)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest_node_pos = (nx, ny)

        if closest_node_pos and min_dist < THRESHOLD:
            return closest_node_pos
        
        return self.snap_to_grid(scene_pos)

    def mousePressEvent(self, event):
        scene_pos = event.scenePos()
        grid_x, grid_y = self._compute_press_grid(scene_pos)
        self._set_press_state(scene_pos, grid_x, grid_y)

        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        if self.current_tool == "pointer":
            if self._handle_pointer_press(event, scene_pos):
                return
            super().mousePressEvent(event)
            return

        if self._handle_tool_press(event, grid_x, grid_y):
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Ghost wire
        if self._handle_wire_preview_move(event):
            return
        
        # Group move
        if self._handle_group_move(event):
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle left-click release actions."""
        if event.button() != Qt.LeftButton:
            super().mouseReleaseEvent(event)
            return

        if self._handle_pointer_release(event):
            self._reset_press_state()
            return

        if self.current_tool == "wire" and self.drawing_wire:
            scene_pos = event.scenePos()
            grid_x, grid_y = self.get_snapped_position(scene_pos)
            self.finish_wire_drawing(grid_x, grid_y)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

        self._reset_press_state()

    def _compute_press_grid(self, scene_pos):
        grid_x, grid_y = self.get_snapped_position(scene_pos)
        if self.current_tool == "pointer":
            return self.snap_to_grid(scene_pos)
        return grid_x, grid_y

    def _set_press_state(self, scene_pos, grid_x, grid_y):
        self._press_scene_pos = scene_pos
        self._last_grid_pos = QPointF(grid_x, grid_y)
        self._group_move_active = False
        self._drag_started_on_item = False

    def _reset_press_state(self):
        self._drag_started_on_item = False
        self._press_scene_pos = None
        self._suppress_move_until_release = False
        if self._selection_snapshot is not None:
            for item in self._selection_snapshot:
                item.setSelected(True)
            self._selection_snapshot = None

    def _handle_pointer_press(self, event, scene_pos):
        item = self.itemAt(scene_pos, QTransform())
        if isinstance(item, WireHandle):
            parent = item.parentItem()
            if parent is not None:
                parent.setSelected(True)
            self._drag_started_on_item = False
            self._suppress_move_until_release = False
            return False
        if isinstance(item, WireItem):
            if item.isSelected() and len(self.selectedItems()) > 1:
                self._selection_snapshot = list(self.selectedItems())
                self._drag_started_on_item = True
                self._suppress_move_until_release = False
                event.accept()
                return True
            if not item.isSelected() and not (event.modifiers() & (Qt.ShiftModifier | Qt.ControlModifier)):
                self.clearSelection()
            item.setSelected(True)
            self._drag_started_on_item = True
            self._suppress_move_until_release = False
            return False
        if isinstance(item, ComponentItem):
            self._drag_started_on_item = True
            self._suppress_move_until_release = False
            return False
        if not (event.modifiers() & (Qt.ShiftModifier | Qt.ControlModifier)):
            self.clearSelection()
            self._suppress_move_until_release = True
        return False

    def _handle_tool_press(self, event, grid_x, grid_y):
        if self.current_tool == "wire":
            self.start_wire_drawing(grid_x, grid_y)
            event.accept()
            return True
        if self.current_tool in [
            "resistor",
            "source_dc",
            "source_ac",
            "capacitor",
            "inductor",
        ]:
            self.add_component_at(self.current_tool, grid_x, grid_y)
            event.accept()
            return True
        return False

    def _handle_wire_preview_move(self, event):
        if self.current_tool != "wire" or not self.drawing_wire or not self.temp_wire_item:
            return False
        new_pos = event.scenePos()
        grid_x, grid_y = self.get_snapped_position(new_pos)
        line = self.temp_wire_item.line()
        line.setP2(QPointF(grid_x, grid_y))
        self.temp_wire_item.setLine(line)
        super().mouseMoveEvent(event)
        return True

    def _handle_group_move(self, event):
        if self.current_tool != "pointer" or not self.selectedItems() or not (event.buttons() & Qt.LeftButton):
            return False
        if not self._drag_started_on_item:
            return False
        if self._suppress_move_until_release:
            return False
        if self._press_scene_pos is not None:
            drag_distance = (event.scenePos() - self._press_scene_pos).manhattanLength()
            if drag_distance < QApplication.startDragDistance():
                return False

        selected_component_nodes = set()
        for selected_item in self.selectedItems():
            if isinstance(selected_item, ComponentItem):
                selected_component_nodes.add(selected_item.component.node_a)
                selected_component_nodes.add(selected_item.component.node_b)

        grabber = self.mouseGrabberItem()
        if isinstance(grabber, WireHandle):
            return False

        current_grid_x, current_grid_y = self.snap_to_grid(event.scenePos())
        current_grid_pos = QPointF(current_grid_x, current_grid_y)
        grid_delta = current_grid_pos - self._last_grid_pos

        if grid_delta.manhattanLength() > 0:
            if not self._group_move_active:
                self._push_undo_snapshot()
            self._group_move_active = True
            moved_wire_node_ids = set()
            for item in self.selectedItems():
                if isinstance(item, ComponentItem):
                    item.setPos(item.pos() + grid_delta)
                elif isinstance(item, WireItem):
                    detach = True
                    if selected_component_nodes:
                        if item.wire.node_a in selected_component_nodes or item.wire.node_b in selected_component_nodes:
                            detach = False
                    item.apply_scene_delta(
                        grid_delta,
                        detach_shared_nodes=detach,
                        moved_node_ids=moved_wire_node_ids,
                    )

            self._last_grid_pos = current_grid_pos

        event.accept()
        return True

    def _handle_pointer_release(self, event):
        if self.current_tool != "pointer":
            return False
        if not self._group_move_active:
            return False
        for item in self.selectedItems():
            if isinstance(item, ComponentItem):
                self.handle_component_move(item)
            elif isinstance(item, WireItem):
                self.handle_wire_move(item, record_undo=False)
        self._group_move_active = False
        event.accept()
        return True

    def add_component_at(self, tool_type, x, y):
        """Create a component at the given position."""
        self._push_undo_snapshot()

        node_a = self.model.create_node(x - 30, y)
        node_b = self.model.create_node(x + 30, y)
        
        dipole = None
        d_id = self.model.get_next_dipole_id()

        # Model creation
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

    def handle_component_move(self, component_item):
        """
        Called after a component has finished moving.
        """
        # Update node coordinates
        component_item.update_model_nodes()
        
        # Collect node IDs for the moved component
        node_ids = {component_item.component.node_a.id, component_item.component.node_b.id}
        
        # Refresh wires connected to those nodes
        for item in self.items():
            if isinstance(item, WireItem):
                wire = item.wire
                if wire.node_a.id in node_ids or wire.node_b.id in node_ids:
                    item.refresh_geometry()

    def start_wire_drawing(self, x, y):
        """Start interactive wire drawing."""
        self.drawing_wire = True
        self.start_pos = (x, y)
        
        # Temporary wire preview
        self.temp_wire_item = QGraphicsLineItem(x, y, x, y)
        pen = QPen(Qt.gray, 2, Qt.DashLine)
        self.temp_wire_item.setPen(pen)
        self.addItem(self.temp_wire_item)

    def finish_wire_drawing(self, x, y):
        """Finalize the wire and add it to the model."""
        
        start_x, start_y = self.start_pos
        
        # Cleanup temporary preview
        self.removeItem(self.temp_wire_item)
        self.temp_wire_item = None
        self.drawing_wire = False
        
        # Do not create a zero-length wire
        if start_x == x and start_y == y:
            return

        # Register wire creation as its own undoable action.
        self._push_undo_snapshot()

        # Find or create the start node
        node_a = self.model.get_node_at(start_x, start_y)
        if not node_a:
            node_a = self.model.create_node(start_x, start_y)
            
        # Find or create the end node
        node_b = self.model.get_node_at(x, y)
        if not node_b:
            node_b = self.model.create_node(x, y)

        # Create wire in the model
        try:
            wire = self.model.create_wire(node_a, node_b)
            
            # Create the final wire item
            wire_item = WireItem(wire)
            self.addItem(wire_item)
            
        except Exception as e:
            print(f"[Erreur] Impossible de créer le fil : {e}")

    def update_wires_connected_to(self, component_model, new_pos, rotation):
        """
        Update connected wires while a component is moving.
        """
        
        # Node positions from component center and rotation
        cx, cy = new_pos.x(), new_pos.y()
        offset = 30
        rad = math.radians(rotation)
        dx = offset * math.cos(rad)
        dy = offset * math.sin(rad)
        
        # Update model in real time
        component_model.node_a.position = (cx - dx, cy - dy)
        component_model.node_b.position = (cx + dx, cy + dy)
        component_model.position = (cx, cy)

        # Refresh connected wires
        node_ids = {component_model.node_a.id, component_model.node_b.id}
        
        for item in self.items():
            if isinstance(item, WireItem): 
                wire = item.wire
                if wire.node_a.id in node_ids or wire.node_b.id in node_ids:
                    item.refresh_geometry()

    def cancel_wire_drawing(self):
        """Cancel the current wire drawing operation."""
        if self.temp_wire_item:
            self.removeItem(self.temp_wire_item)
            self.temp_wire_item = None
        self.drawing_wire = False

    def handle_wire_move(self, wire_item, record_undo=True):
        """
        Update the model and reset the visuals after a wire move.
        """
        if record_undo:
            self._push_undo_snapshot()
        
        # Compute absolute positions
        raw_pos_a = wire_item.handle_a.scenePos()
        raw_pos_b = wire_item.handle_b.scenePos()

        # Snapping
        xa, ya = self.get_snapped_position(raw_pos_a)
        xb, yb = self.get_snapped_position(raw_pos_b)
        
        # Node A
        node_a = self.model.get_node_at(xa, ya)
        if not node_a:
            node_a = self.model.create_node(xa, ya)
        
        # Node B
        node_b = self.model.get_node_at(xb, yb)
        if not node_b:
            node_b = self.model.create_node(xb, yb)

        # Update model references
        wire_item.wire.node_a = node_a
        wire_item.wire.node_b = node_b

        # Reset visuals
        wire_item.refresh_geometry()

    def delete_selection(self):
        """Delete all selected items."""
        selected = self.selectedItems()
        if not selected:
            return

        self._push_undo_snapshot()

        for item in selected:
            # Remove from the model
            if hasattr(item, 'component'):
                dipole_id = item.component.id
                self.model.remove_dipole(dipole_id)
            elif isinstance(item, WireItem):
                wire_id = item.wire.id
                self.model.remove_wire(wire_id)
            
            # Remove from the scene
            self.removeItem(item)

    def refresh_from_model(self):
        """
        Clear the scene and rebuild it from the model.
        """
        self.clear()
        
        # Add dipoles
        for dipole in self.model.dipoles.values():
            item = create_component_item(dipole)
            self.addItem(item)
            
        # Add wires
        for wire in self.model.wires.values():
            wire_item = WireItem(wire)
            self.addItem(wire_item)