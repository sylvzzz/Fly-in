from zone.zone import Zone

class Drone:
    def __init__(self, drone_id: int, current_zone: Zone,
                 path: list[Zone]) -> None:
        self.drone_id = drone_id
        self.current_zone: Zone | None = current_zone
        self.path = path
        self.delivered: bool = False
        self.path_index: int = 1
        self.in_transit: bool = False  # está a atravessar uma conexão restricted?
        self.transit_destination: Zone | None = None  # zona de destino do trânsito
        self.arrived_this_turn: bool = False

    """
    why we start on index 1 instead of 0?

    so, if we started on 0 we would be saying, move to start,
    thats your next move, and while building this project i found
    that initializing at index 0 would put the drone in an 
    infinite loop and didnt leave the start, so we gotta start it at index 1
    as it is initialized at start anyways 
    """