from zone import Zone

class Connection:
    """
    Represents a bidirectional link between two zones in the graph.

    Each connection defines a pathway that drones can traverse between
    zones, with an optional capacity limit controlling how many drones
    can use the connection per turn.

    Attributes:
        zone1: First endpoint of the connection.
        zone2: Second endpoint of the connection.
        max_link_capacity: Maximum number of drones that can traverse
            this connection in a single turn.
    """
    def __init__(self, zone1: Zone, zone2: Zone,
                 max_link_capacity: int = 1) -> None:
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = max_link_capacity