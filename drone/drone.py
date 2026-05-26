from zone.zone import Zone


class Drone:
    """
    Represents a drone moving through the zone following a optimized path.

    Each drone tracks its current position, delivery status, and move state.
    Movement can occur instantly or through a transit state when crossing
    restricted zones that require an additional turn to complete.

    Attributes:
        drone_id: Unique identifier of the drone.
        current_zone: Current zone where the drone is located.
        path: Ordered list of zones representing the route to the destination.
        delivered: Whether the drone has reached the final zone.
        path_index: Index of the next zone in the path to visit.
        in_transit: Indicates the drone is crossing a restricted connection.
        transit_destination: Target zone if the drone is in transit.
        arrived_this_turn: Indicates if the drone completed a move this turn.
    """
    def __init__(self, drone_id: int, current_zone: Zone,
                 path: list[Zone]) -> None:
        self.drone_id = drone_id
        self.current_zone: Zone | None = current_zone
        self.path = path
        self.delivered: bool = False
        self.path_index: int = 1
        self.in_transit: bool = False
        self.transit_destination: Zone | None = None
        self.arrived_this_turn: bool = False

    """
    why we start on index 1 instead of 0?

    so, if we started on 0 we would be saying, move to start,
    thats your next move, and while building this project i found
    that initializing at index 0 would put the drone in an
    infinite loop and didnt leave the start, so we gotta start it at index 1
    as it is initialized at start anyways
    """
