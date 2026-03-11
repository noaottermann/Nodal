from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath
from PyQt5.QtCore import Qt, QPointF, QRectF


class NodeItem(QGraphicsEllipseItem):
    """Element graphique representant un noeud libre"""

    RADIUS = 2
    HIT_RADIUS = 8

    def __init__(self, node_model):
        super().__init__(-self.RADIUS, -self.RADIUS, self.RADIUS * 2, self.RADIUS * 2)
        self.node = node_model
        self._drag_active = False
        self._undo_snapshot_taken = False

        self.setFlags(
            QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setZValue(3)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setCursor(Qt.OpenHandCursor)
        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(QColor(Qt.black)))
        self.setToolTip(f"Noeud {self.node.id}")

        x, y = self.node.position
        self.setPos(x, y)

    def boundingRect(self):
        return QRectF(
            -self.HIT_RADIUS,
            -self.HIT_RADIUS,
            self.HIT_RADIUS * 2,
            self.HIT_RADIUS * 2,
        )

    def shape(self):
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), self.HIT_RADIUS, self.HIT_RADIUS)
        return path

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._undo_snapshot_taken = False
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            self._drag_active = False
            self._undo_snapshot_taken = False
            self.setCursor(Qt.OpenHandCursor)
            scene = self.scene()
            if scene and hasattr(scene, "finalize_node_move"):
                scene.finalize_node_move(self)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            scene = self.scene()
            x, y = scene.snap_to_grid(value)
            snapped = QPointF(x, y)

            if self._drag_active:
                if not self._undo_snapshot_taken and self.pos() != snapped:
                    if hasattr(scene, "_push_undo_snapshot"):
                        scene._push_undo_snapshot()
                    self._undo_snapshot_taken = True

                if hasattr(scene, "preview_node_move"):
                    scene.preview_node_move(self.node, snapped)

            return snapped

        return super().itemChange(change, value)
