from graph.graph import Graph
from drone.drone import Drone
from zone.zone import Zone, ZoneType
from typing import TypedDict


class DroneState(TypedDict):
    drone_id: int
    zone: str | None
    in_transit: bool
    dest: str | None
    delivered: bool


class TurnData(TypedDict):
    turn: int
    connections_used: dict[str, int]
    drones: list[DroneState]


class Engine:
    """
    Core simulation engine responsible for coordinating drone movement
    through a graph until all drones reach the destination.

    The engine manages turn-based execution, enforcing constraints such as:
    - zone capacity limits
    - connection usage limits
    - delivery completion conditions

    Args:
            graph: Graph structure representing zones and connections.
            drones: List of drones participating in the simulation.
            end_zone: Final destination zone where drones are delivered.
    """
    def __init__(self, graph: Graph, drones: list[Drone],
                 end_zone: Zone) -> None:
        self.graph = graph
        self.drones = drones
        self.end_zone = end_zone
        self.turns: int = 0
        self.connections_used: dict[str, int] = {}

    def run(self) -> list[TurnData]:
        """
        Executes the drone delivery simulation until all drones are delivered.

        The simulation advances turn by turn while enforcing:
        - zone capacity constraints
        - connection capacity limits
        - restricted-zone transit rules
        - drone movement synchronization

        Each turn is processed in two phases:
        1. Resolve drones currently in transit.
        2. Execute new drone movements.

        Restricted zones require drones to enter a transit state before
        arriving on the next turn. Connection usage is tracked per turn
        to ensure link capacities are respected.

        A history list is stored after every turn, including:
        - turn number
        - connection usage
        - drone positions
        - transit states
        - delivery status

        Returns:
            A list containing the complete simulation history.
        """
        moves_history: list[TurnData] = []
        while not all(drone.delivered for drone in self.drones):
            self.turns += 1
            self.connections_used = {}
            turn_moves: list[str] = []
            moving_out: set[int] = set()

            # Reset da flag de chegada de trânsito
            for drone in self.drones:
                drone.arrived_this_turn = False

            # Primeiro passo: chegadas obrigatórias de trânsito
            for drone in self.drones:
                if drone.delivered or not drone.in_transit:
                    continue
                if drone.drone_id in moving_out:
                    continue
                destination = drone.transit_destination
                if destination is None:
                    continue
                drones_in_dest = len([
                    d for d in self.drones
                    if d.current_zone is not None
                    and d.current_zone.name == destination.name
                    and not d.delivered
                    and d.drone_id not in moving_out
                ])
                if drones_in_dest < destination.max_drones:
                    moving_out.add(drone.drone_id)
                    drone.current_zone = destination
                    drone.in_transit = False
                    drone.transit_destination = None
                    drone.arrived_this_turn = True
                    turn_moves.append(f"D{drone.drone_id}-{destination.name}")
                    if destination.name == self.end_zone.name:
                        drone.delivered = True
                        continue

                    # imeadiatly tries to move to the next zone
                    if drone.path_index < len(drone.path):
                        next_zone = drone.path[drone.path_index]
                        if next_zone.zone_type == ZoneType.RESTRICTED:
                            drones_in_next = len([
                                d for d in self.drones
                                if d.current_zone is not None
                                and d.current_zone.name == next_zone.name
                                and not d.delivered
                                and d.drone_id not in moving_out
                            ])
                            already_arriving = len([
                                d for d in self.drones
                                if d.transit_destination is not None
                                and d.transit_destination.name
                                == next_zone.name
                            ])
                            connection = self.graph.get_connection(
                                drone.current_zone, next_zone
                                )
                            conn_ok = True
                            if connection is not None:
                                z1_name = connection.zone1.name
                                z2_name = connection.zone2.name
                                key_min = min(z1_name, z2_name)
                                key_max = max(z1_name, z2_name)
                                conn_key = f"{key_min}-{key_max}"
                                used = self.connections_used.get(conn_key, 0)
                                if used >= connection.max_link_capacity:
                                    conn_ok = False
                            total_in_next = drones_in_next + already_arriving
                            can_fit = total_in_next < next_zone.max_drones
                            if conn_ok and can_fit:
                                d_name = drone.current_zone.name
                                c_name = f"{d_name}-{next_zone.name}"
                                drone.in_transit = True
                                drone.transit_destination = next_zone
                                drone.current_zone = None
                                drone.path_index += 1
                                turn_moves[-1] = f"D{drone.drone_id}-{c_name}"
                                # if it moved dont block
                                drone.arrived_this_turn = False

            # Segundo passo: movimentos normais
            for drone in self.drones:
                if drone.delivered or drone.in_transit:
                    continue
                if drone.arrived_this_turn:
                    continue
                if drone.path_index >= len(drone.path):
                    continue

                next_zone = drone.path[drone.path_index]

                drones_in_zone = len([
                    d for d in self.drones
                    if d.current_zone is not None
                    and d.current_zone.name == next_zone.name
                    and not d.delivered
                    and d.drone_id not in moving_out
                ])

                if drones_in_zone >= next_zone.max_drones:
                    continue
                if drone.current_zone is None:
                    continue
                connection = self.graph.get_connection(drone.current_zone,
                                                       next_zone)
                if connection is not None:
                    z1_name = connection.zone1.name
                    z2_name = connection.zone2.name
                    key_min = min(z1_name, z2_name)
                    key_max = max(z1_name, z2_name)
                    conn_key = f"{key_min}-{key_max}"

                    used = self.connections_used.get(conn_key, 0)
                    if used >= connection.max_link_capacity:
                        continue
                    self.connections_used[conn_key] = used + 1

                if next_zone.zone_type == ZoneType.RESTRICTED:
                    # verifica se há espaço garantido no próximo turn
                    already_arriving = len([
                        d for d in self.drones
                        if d.transit_destination is not None
                        and d.transit_destination.name == next_zone.name
                    ])
                    total_in_zone = drones_in_zone + already_arriving
                    if total_in_zone >= next_zone.max_drones:
                        continue  # não entra em trânsito, espera
                    conn_name = f"{drone.current_zone.name}-{next_zone.name}"
                    drone.in_transit = True
                    drone.transit_destination = next_zone
                    drone.current_zone = None
                    drone.path_index += 1
                    turn_moves.append(f"D{drone.drone_id}-{conn_name}")
                else:
                    drone.current_zone = next_zone
                    drone.path_index += 1
                    turn_moves.append(f"D{drone.drone_id}-{next_zone.name}")
                    if next_zone.name == self.end_zone.name:
                        drone.delivered = True

                moving_out.add(drone.drone_id)

            if turn_moves:
                print(" ".join(turn_moves))

            drone_states = []
            for d in self.drones:
                zone_name = d.current_zone.name if d.current_zone else None
                dest_name = (
                    d.transit_destination.name
                    if d.transit_destination else None
                )
                drone_state: DroneState = {
                    "drone_id": d.drone_id,
                    "zone": zone_name,
                    "in_transit": d.in_transit,
                    "dest": dest_name,
                    "delivered": d.delivered,
                }
                drone_states.append(drone_state)

            turn_data: TurnData = {
                "turn": self.turns,
                "connections_used": dict(self.connections_used),
                "drones": drone_states,
            }

            moves_history.append(turn_data)
        return moves_history
