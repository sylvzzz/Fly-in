from graph.graph import Graph
from drone.drone import Drone
from zone.zone import Zone, ZoneType


class Engine:
    def __init__(self, graph: Graph, drones: list[Drone],
                 end_zone: Zone) -> None:
        self.graph = graph
        self.drones = drones
        self.end_zone = end_zone
        self.turns: int = 0
        self.connections_used: dict[str, int] = {}

    def run(self) -> list[dict]:
        moves_history = []
        while not all(drone.delivered for drone in self.drones):
            self.turns += 1
            self.connections_used: dict[str, int] = {}
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

                    # tenta imediatamente entrar em trânsito para a próxima zona
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
                                and d.transit_destination.name == next_zone.name
                            ])
                            connection = self.graph.get_connection(drone.current_zone, next_zone)
                            conn_ok = True
                            if connection is not None:
                                conn_key = f"{min(connection.zone1.name, connection.zone2.name)}-{max(connection.zone1.name, connection.zone2.name)}"
                                if self.connections_used.get(conn_key, 0) >= connection.max_link_capacity:
                                    conn_ok = False
                                else:
                                    self.connections_used[conn_key] = self.connections_used.get(conn_key, 0) + 1
                            if conn_ok and drones_in_next + already_arriving < next_zone.max_drones:
                                conn_name = f"{drone.current_zone.name}-{next_zone.name}"
                                drone.in_transit = True
                                drone.transit_destination = next_zone
                                drone.current_zone = None  # type: ignore
                                drone.path_index += 1
                                turn_moves[-1] = f"D{drone.drone_id}-{conn_name}"
                                drone.arrived_this_turn = False  # já se moveu, não bloquear

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

                connection = self.graph.get_connection(drone.current_zone, next_zone)
                if connection is not None:
                    conn_key = f"{min(connection.zone1.name, connection.zone2.name)}-{max(connection.zone1.name, connection.zone2.name)}"
                    if self.connections_used.get(conn_key, 0) >= connection.max_link_capacity:
                        continue
                    self.connections_used[conn_key] = self.connections_used.get(conn_key, 0) + 1

                if next_zone.zone_type == ZoneType.RESTRICTED:
                    # verifica se há espaço garantido no próximo turn
                    already_arriving = len([
                        d for d in self.drones
                        if d.transit_destination is not None
                        and d.transit_destination.name == next_zone.name
                    ])
                    if drones_in_zone + already_arriving >= next_zone.max_drones:
                        continue  # não entra em trânsito, espera
                    conn_name = f"{drone.current_zone.name}-{next_zone.name}"
                    drone.in_transit = True
                    drone.transit_destination = next_zone
                    drone.current_zone = None  # type: ignore
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
            moves_history.append({
                "turn": self.turns,
                "connections_used": dict(self.connections_used),
                "drones": [
                    {
                        "id": d.drone_id,
                        "zone": d.current_zone.name if d.current_zone else None,
                        "in_transit": d.in_transit,
                        "dest": d.transit_destination.name if d.transit_destination else None,
                        "delivered": d.delivered,
                    }
                    for d in self.drones
                ],
            })
        return moves_history