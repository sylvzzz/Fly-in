import os
import sys
from parsing import Parser
from graph.graph import Graph
from visualizer.visualizer import Visualizer

"""
Multi-agent drone routing simulator in Python with custom pathfinding for dynamic networks. Handles concurrent drone movement, zone occupancy rules, and conflict resolution while optimizing for minimal simulation turns. Focuses on graph algorithms, OOP design, and performance under real-world constraints like bottlenecks and deadlock prevention.
"""


def testar_parsing_zone_e_connection():

    parser = Parser("maps/easy/02_simple_fork.txt")

    try:
        nb_drones, start, end, hubs, connections = parser.get_map_data()

        print(f"Drones: {nb_drones}")
        print(f"Start: {start.name} ({start.x}, {start.y})")
        print(f"End: {end.name} ({end.x}, {end.y})")

        print(f"\nHubs ({len(hubs)}):")
        for hub in hubs:
            print(f"  {hub.name} | tipo={hub.zone_type} | max_drones={hub.max_drones}")

        print(f"\nConnections ({len(connections)}):")
        for conn in connections:
            print(f"  {conn.zone1.name} <-> {conn.zone2.name} | cap={conn.max_link_capacity}")

    except ValueError as e:
        print(f"Erro: {e}")

        """
        exemplo de output

        Drones: 3
        Start: start (0, 0)
        End: goal (3, 0)

        Hubs (3):
        junction | tipo=ZoneType.NORMAL | max_drones=2
        path_a | tipo=ZoneType.NORMAL | max_drones=1
        path_b | tipo=ZoneType.NORMAL | max_drones=1

        Connections (5):
        start <-> junction | cap=1
        junction <-> path_a | cap=1
        junction <-> path_b | cap=1
        path_a <-> goal | cap=1
        path_b <-> goal | cap=1
        """


def testar_graph():
    parser = Parser("maps/easy/02_simple_fork.txt")
    nb_drones, start, end, hubs, connections = parser.get_map_data()

    # Construir o grafo
    graph = Graph()
    graph.add_zone(start)
    graph.add_zone(end)
    for hub in hubs:
        graph.add_zone(hub)
    for conn in connections:
        graph.add_connection(conn)

    # Imprimir adjacência
    print("Adjacência:")
    for zone_name, conns in graph.adjacency.items():
        neighbors = [
            c.zone1.name if c.zone2.name == zone_name else c.zone2.name
            for c in conns
        ]
        print(f"  {zone_name} -> {neighbors}")
    """
    exemplo de output

    Adjacência:
    start -> ['junction']
    goal -> ['path_a', 'path_b']
    junction -> ['start', 'path_a', 'path_b']
    path_a -> ['junction', 'goal']
    path_b -> ['junction', 'goal']
    """

    print("\n\n Caminho resolvido:\n")
    path = graph.find_path(start, end)
    for zone in path:
        print(f" Zona atual: {zone.name} (tipo de zona={zone.zone_type}, custo acumulado calculado)")
        if zone.name == "goal":
            print("\n Chegamos ao goal!")
    
def testar_engine() -> str:
    from parsing import Parser
    from graph.graph import Graph
    from drone.drone import Drone
    from engine.engine import Engine


    os.system("clear")
    all_maps = ["maps/challenger/01_the_impossible_dream.txt",
                "maps/hard/01_maze_nightmare.txt",
                "maps/hard/02_capacity_hell.txt",
                "maps/hard/03_ultimate_challenge.txt",
                "maps/medium/01_dead_end_trap.txt",
                "maps/medium/02_circular_loop.txt",
                "maps/medium/03_priority_puzzle.txt",
                "maps/easy/01_linear_path.txt",
                "maps/easy/02_simple_fork.txt",
                "maps/easy/03_basic_capacity.txt"
                ]
    for i in all_maps:
        parser = Parser(i)
        nb_drones, start, end, hubs, connections = parser.get_map_data()

        # construir o grafo
        graph = Graph()
        graph.add_zone(start)
        graph.add_zone(end)
        for hub in hubs:
            graph.add_zone(hub)
        for conn in connections:
            graph.add_connection(conn)

        # encontrar caminho e criar drones
        paths = graph.generate_paths(start, end, nb_drones)
        drones = [Drone(i + 1, start, paths[i % len(paths)]) for i in range(nb_drones)]

        path = graph.find_path(start, end)
        print([z.name for z in path])

        # correr simulação
        print(f"Simulation result for {i}")
        print()
        engine = Engine(graph, drones, end)
        data = engine.run()
        print(f"\nTotal de turnos do {i}: {engine.turns}")
        vis = Visualizer(1280, 780, 60, graph, data, start)
        vis.run()



def test_all_maps():
    os.system("clear")
    all_maps = ["maps/challenger/01_the_impossible_dream.txt",
                "maps/hard/01_maze_nightmare.txt",
                "maps/hard/02_capacity_hell.txt",
                "maps/hard/03_ultimate_challenge.txt",
                "maps/medium/01_dead_end_trap.txt",
                "maps/medium/02_circular_loop.txt",
                "maps/medium/03_priority_puzzle.txt",
                "maps/easy/01_linear_path.txt",
                "maps/easy/02_simple_fork.txt",
                "maps/easy/03_basic_capacity.txt"
                ]
    turns_results = []
    for maps in all_maps:
        os.system("clear")
        turns_results.append(testar_engine(maps))
        input("Show next ...")
    os.system("clear")
    for i in turns_results:
        print(i)

def test_visualizer() -> None:
    from parsing import Parser
    from graph.graph import Graph

    all_maps = ["maps/challenger/01_the_impossible_dream.txt",
                "maps/hard/01_maze_nightmare.txt",
                "maps/hard/02_capacity_hell.txt",
                "maps/hard/03_ultimate_challenge.txt",
                "maps/medium/01_dead_end_trap.txt",
                "maps/medium/02_circular_loop.txt",
                "maps/medium/03_priority_puzzle.txt",
                "maps/easy/01_linear_path.txt",
                "maps/easy/02_simple_fork.txt",
                "maps/easy/03_basic_capacity.txt"
                ]

    for maps in all_maps:
        parser = Parser(maps)
        nb_drones, start, end, hubs, connections = parser.get_map_data()
        graph = Graph()
        graph.add_zone(start)
        graph.add_zone(end)
        for hub in hubs:
            graph.add_zone(hub)
        for conn in connections:
            graph.add_connection(conn)
        vis = Visualizer(1280, 780, 60, graph)
        vis.run()

def main(map_file: str) -> None:
    from parsing import Parser
    from graph.graph import Graph
    from drone.drone import Drone
    from engine.engine import Engine


    parser = Parser(map_file)
    nb_drones, start, end, hubs, connections = parser.get_map_data()

        # construir o grafo
    graph = Graph()
    graph.add_zone(start)
    graph.add_zone(end)
    for hub in hubs:
        graph.add_zone(hub)
    for conn in connections:
        graph.add_connection(conn)

        # encontrar caminho e criar drones
    paths = graph.generate_paths(start, end, nb_drones)
    drones = [Drone(i + 1, start, paths[i % len(paths)]) for i in range(nb_drones)]

    path = graph.find_path(start, end)
    engine = Engine(graph, drones, end)
    data = engine.run()
    vis = Visualizer(1280, 780, 60, graph, data, start)
    vis.run()

if __name__ == "__main__":
    args = sys.argv
    if len(args) == 2:
        try:
            map_file = args[1]
            main(map_file)
        except FileNotFoundError:
            print("\033[31m" + f"\nMap file {map_file} not found" + "\033[0m")
    else:
        print("Correct usage: python3 Fly-in.py map_file.txt")