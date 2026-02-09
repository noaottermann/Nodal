class Node:
    """
    Represents an electrical node in the circuit.
    """

    def __init__(self, node_id, x=0.0, y=0.0, is_ground=False):
        """
        Initialize a new node.

        Args:
            node_id (int): Unique node ID
            x (float): X coordinate on the grid
            y (float): Y coordinate on the grid
            is_ground (bool): True if this node is the ground reference (0V)
        """
        self.id = int(node_id)
        self.position = (float(x), float(y))
        self.is_ground = is_ground
        self._potential = 0.0
        self.connected_dipoles = []

    @property
    def potential(self):
        return self._potential

    @potential.setter
    def potential(self, value):
        if self.is_ground:
            self._potential = 0.0
        else:
            self._potential = float(value)

    def add_connection(self, dipole):
        if dipole not in self.connected_dipoles:
            self.connected_dipoles.append(dipole)

    def remove_connection(self, dipole):
        if dipole in self.connected_dipoles:
            self.connected_dipoles.remove(dipole)

    def to_dict(self):
        return {
            "id": self.id,
            "position": self.position,
            "is_ground": self.is_ground,
            "potential": self._potential
        }

    @classmethod
    def from_dict(cls, data):
        x, y = data.get("position", (0.0, 0.0))
        node = cls(
            node_id=data["id"],
            x=x,
            y=y,
            is_ground=data.get("is_ground", False)
        )
        if "potential" in data:
            node._potential = data["potential"]
        return node

    def __repr__(self):
        state = "GND" if self.is_ground else f"{self._potential:.2f}V"
        return f"<Node {self.id} | Pos={self.position} | {state}>"