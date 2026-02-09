import math
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QTransform

# Model and graphics items
from model.components import Resistor, VoltageSourceDC, VoltageSourceAC, Capacitor, Inductor
from .component_item import ComponentItem, create_component_item
from .wire_item import WireHandle, WireItem

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
        # Middle click starts panning
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
            # Restore cursor
            self.setCursor(Qt.ArrowCursor) 
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            # Calculate mouse delta
            dx = event.x() - self._pan_start_x
            dy = event.y() - self._pan_start_y
            
            self._pan_start_x = event.x()
            self._pan_start_y = event.y()
            
            # Adjust hidden scrollbars
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - dx)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - dy)
            event.accept()
        else:
            super().mouseMoveEvent(event)

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
        self._group_move_active = False
        self._drag_start_on_item = False

    def set_tool(self, tool_name):
        """Set the active tool name."""
        self.current_tool = tool_name

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
        grid_x, grid_y = self.get_snapped_position(scene_pos)
        if self.current_tool == "pointer":
            grid_x, grid_y = self.snap_to_grid(scene_pos)

        self._last_grid_pos = QPointF(grid_x, grid_y)
        self._group_move_active = False
        self._drag_start_on_item = False

        # Left click
        if event.button() == Qt.LeftButton:
            if self.current_tool == "pointer":
                # Avoid group moves when starting a rubber-band selection
                item = self.itemAt(scene_pos, QTransform())
                if item is not None and not isinstance(item, WireHandle):
                    self._drag_start_on_item = True
                super().mousePressEvent(event)
            elif self.current_tool == "wire":
                self.start_wire_drawing(grid_x, grid_y)
                event.accept()
            elif self.current_tool in ["resistor", "source_dc"]:
                self.add_component_at(self.current_tool, grid_x, grid_y)
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Ghost wire
        if self.current_tool == "wire" and self.drawing_wire and self.temp_wire_item:
            new_pos = event.scenePos()
            grid_x, grid_y = self.get_snapped_position(new_pos)
            line = self.temp_wire_item.line()
            line.setP2(QPointF(grid_x, grid_y))
            self.temp_wire_item.setLine(line)
            super().mouseMoveEvent(event)
            return
        
        # Group move
        if self.current_tool == "pointer" and self.selectedItems() and event.buttons() & Qt.LeftButton:
            if not self._drag_start_on_item:
                super().mouseMoveEvent(event)
                return

            selected_component_nodes = set()
            for selected_item in self.selectedItems():
                if isinstance(selected_item, ComponentItem):
                    selected_component_nodes.add(selected_item.component.node_a)
                    selected_component_nodes.add(selected_item.component.node_b)
            
            # Ignore drag when manipulating a wire handle
            grabber = self.mouseGrabberItem()
            if isinstance(grabber, WireHandle):
                super().mouseMoveEvent(event)
                return
            
            current_grid_x, current_grid_y = self.snap_to_grid(event.scenePos())
            current_grid_pos = QPointF(current_grid_x, current_grid_y)
            grid_delta = current_grid_pos - self._last_grid_pos
            
            if grid_delta.manhattanLength() > 0:
                self._group_move_active = True
                # Move all selected items by the same delta
                for item in self.selectedItems():
                    if isinstance(item, ComponentItem):
                        item.setPos(item.pos() + grid_delta)
                    elif isinstance(item, WireItem):
                        detach = True
                        if selected_component_nodes:
                            if item.wire.node_a in selected_component_nodes or item.wire.node_b in selected_component_nodes:
                                detach = False
                        item.apply_scene_delta(grid_delta, detach_shared_nodes=detach)
                
                self._last_grid_pos = current_grid_pos
            
            event.accept()
            
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle left-click release actions."""
        if event.button() == Qt.LeftButton:
            if self.current_tool == "pointer" and self._group_move_active:
                # Finalize group move (model update + per-item snapping)
                for item in self.selectedItems():
                    if isinstance(item, ComponentItem):
                        self.handle_component_move(item)
                    elif isinstance(item, WireItem):
                        self.handle_wire_move(item)
                self._group_move_active = False
                event.accept()
                return
            
            if self.current_tool == "wire" and self.drawing_wire:
                # Finish wire
                scene_pos = event.scenePos()
                grid_x, grid_y = self.get_snapped_position(scene_pos)
                self.finish_wire_drawing(grid_x, grid_y)
                event.accept()
                
            else:
                super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)
        self._drag_start_on_item = False

    def add_component_at(self, tool_type, x, y):
        """Create a component at the given position."""
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

    def handle_wire_move(self, wire_item):
        """
        Update the model and reset the visuals after a wire move.
        """
        
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
        for item in self.selectedItems():
            # Remove from the model
            if hasattr(item, 'component'):
                dipole_id = item.component.id
                self.model.remove_dipole(dipole_id)
            
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
            
        # TODO: add wires from the model