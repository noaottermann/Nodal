from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPen, QColor

class Grid:
    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        
        # Point color
        self.pen = QPen(QColor(200, 200, 200), 2)
        
        # Skip drawing when zoomed out too far
        self.min_zoom_factor = 0.3 

    def draw(self, painter, rect, view_scale):
        """
        Draw the grid only within the visible area.
        """
        
        # Skip drawing when too zoomed out to save CPU
        if view_scale < self.min_zoom_factor:
            return

        # Visible bounds
        left = rect.left()
        top = rect.top()
        
        # First grid-aligned point
        first_x = left - (left % self.grid_size)
        first_y = top - (top % self.grid_size)

        # Build points
        points = []
        
        # Loop X from left to right
        x = first_x
        while x < rect.right():
            # Loop Y from top to bottom
            y = first_y
            while y < rect.bottom():
                points.append(QPointF(x, y))
                y += self.grid_size
            x += self.grid_size

        # Draw
        if points:
            painter.setPen(self.pen)
            painter.drawPoints(points)