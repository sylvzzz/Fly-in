from zone.zone import Zone, ZoneType
from connection.connection import Connection
import heapq


class Graph:
    def __init__(self) -> None:
        """
        zones: stores all of our zones using the zone class
        connections: stores connections between zones using connection class
        adjency: for each zone saves who its connected with
        """
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.adjacency: dict[str, list[Connection]] = {}

    def add_zone(self, zone: Zone) -> None:
        """
        guarda a zona no dicionário de zonas e
        inicializa a sua lista de adjacência vazia (ainda sem conexões).
        """
        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)
        self.adjacency[connection.zone1.name].append(connection)
        self.adjacency[connection.zone2.name].append(connection)

    def get_connection(self, zone1: Zone, zone2: Zone) -> Connection | None:
        # procura na adjacência de zone1 a conexão que liga a zone2
        for connection in self.adjacency[zone1.name]:
            if (connection.zone1.name == zone2.name
                    or connection.zone2.name == zone2.name):
                return connection
        return None  # não existe conexão entre as duas zonas

    def path_cost(self, path: list[Zone]) -> int:
        """Calcula o custo total de um caminho."""
        cost = 0
        for zone in path[1:]:
            if zone.zone_type == ZoneType.RESTRICTED:
                cost += 2
            else:
                cost += 1
        return cost

    def generate_paths(self, start: Zone, end: Zone,
                       nb_drones: int) -> list[list[Zone]]:
        distinct_paths: list[list[Zone]] = []

        path = self.find_path(start, end)
        if path:
            distinct_paths.append(path)

        found_new = True
        while found_new:
            found_new = False
            for existing in distinct_paths:
                # tenta excluir subconjuntos de zonas intermédias
                intermediate = [z.name for z in existing[1:-1]]
                for zone_name in intermediate:
                    alt = self.find_path(start, end, {zone_name})
                    if alt and alt not in distinct_paths:
                        distinct_paths.append(alt)
                        found_new = True
                        break
                if found_new:
                    break

        distinct_paths.sort(key=lambda p: self.path_cost(p))

        if not distinct_paths:
            return []

        min_cost = self.path_cost(distinct_paths[0])  # já ordenados por custo
        best_paths = [p for p in distinct_paths
                      if self.path_cost(p) == min_cost]

        paths: list[list[Zone]] = []
        for i in range(nb_drones):
            paths.append(best_paths[i % len(best_paths)])

        return paths

    def find_path(self, start: Zone, end: Zone,
                  excluded_zones: set[str] | None = None) -> list[Zone]:

        # priority queue, stores (cost, zone) ordered by smallest cost
        heap = [(0.0, start.name)]
        # costs dict, stores smallest cost to get to each zone
        costs: dict[str, float] = {start.name: 0.0}
        # stores where "we" came from to memorize zonez and path
        came_from: dict[str, str | None] = {start.name: None}

        while heap:
            current_cost, current_name = heapq.heappop(heap)

            if current_name == end.name:
                path: list[Zone] = []
                current: str | None = end.name
                while current is not None:
                    path.append(self.zones[current])
                    current = came_from[current]
                path.reverse()  # was from end to start so we reverse
                return path

            # explore all neighbors of current zone
            for connection in self.adjacency[current_name]:
                if connection.zone1.name == current_name:
                    neighbor = connection.zone2
                else:
                    neighbor = connection.zone1

                if excluded_zones and neighbor.name in excluded_zones:
                    continue

                if neighbor.zone_type == ZoneType.BLOCKED:
                    continue

                if neighbor.zone_type == ZoneType.RESTRICTED:
                    move_cost = 2.0
                elif neighbor.zone_type == ZoneType.PRIORITY:
                    move_cost = 0.9
                else:
                    move_cost = 1.0

                new_cost = current_cost + move_cost

                if (neighbor.name not in costs
                        or new_cost < costs[neighbor.name]):
                    costs[neighbor.name] = new_cost
                    came_from[neighbor.name] = current_name
                    heapq.heappush(heap, (new_cost, neighbor.name))

        # if all this was done and we got here it means theres no possible path
        return []
