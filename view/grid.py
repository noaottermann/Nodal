import math
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPen, QColor

class Grid:
    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        
        # Couleur des points
        self.pen = QPen(QColor(200, 200, 200), 2)
        
        # On ne dessine pas si le zoom est trop petit
        self.min_zoom_factor = 0.3 

    def draw(self, painter, rect, view_scale):
        """
        Dessine la grille uniquement dans la zone visible
        """
        
        # Si on est trop dézoomé, on ne dessine rien pour économiser le CPU
        if view_scale < self.min_zoom_factor:
            return

        # On récupère les bords gauche/haut du rectangle visible
        left = rect.left()
        top = rect.top()
        
        # Calcul du premier point "aligné" sur la grille
        first_x = left - (left % self.grid_size)
        first_y = top - (top % self.grid_size)

        # Création des points
        points = []
        
        # Boucle X de gauche à droite de l'écran
        x = first_x
        while x < rect.right():
            # Boucle Y de haut en bas de l'écran
            y = first_y
            while y < rect.bottom():
                points.append(QPointF(x, y))
                y += self.grid_size
            x += self.grid_size

        # Dessin
        if points:
            painter.setPen(self.pen)
            painter.drawPoints(points)