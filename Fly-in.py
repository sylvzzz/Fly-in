import os
import sys
from parsing import Parser
from graph import Graph
from visualizer import Visualizer
from drone import Drone
from engine import Engine


def main(map_file: str) -> None:
    """
    Core program of my Fly-in project:

    Here we basicly join everything we built, we create the parser
    via the parsing module, we create a graph and add the zones
    to our graph, find diferent paths for our drones so we can
    prevent things such as problems with max number of drones per zone
    and finnaly we let our engine run to guide the drones, and
    with the data returned from the generator (list of the turns)
    we send them to the visualizer so we can play around with each
    turn like pause, go back in turns, or just auto play it.
    """

    maps = {
        "maps/challenger/01_the_impossible_dream.txt": "The impossible dream",
        "maps/hard/01_maze_nightmare.txt": "Maze nightmare",
        "maps/hard/02_capacity_hell.txt": "Capacity hell",
        "maps/hard/03_ultimate_challenge.txt": "Ultimate challenge",
        "maps/medium/01_dead_end_trap.txt": "Dead end trap",
        "maps/medium/02_circular_loop.txt": "Circular loop",
        "maps/medium/03_priority_puzzle.txt": "Priority puzzle",
        "maps/easy/01_linear_path.txt": "Linear path",
        "maps/easy/02_simple_fork.txt": "Simple fork",
        "maps/easy/03_basic_capacity.txt": "Basic capacity"
    }

    parser = Parser(map_file)
    nb_drones, start, end, hubs, connections = parser.get_map_data()

    # build the graph
    graph = Graph()
    graph.add_zone(start)
    graph.add_zone(end)
    for hub in hubs:
        graph.add_zone(hub)
    for conn in connections:
        graph.add_connection(conn)

    # find paths and create drones
    paths = graph.generate_paths(start, end, nb_drones)
    drones = [
        Drone(i + 1, start, paths[i % len(paths)])
        for i in range(nb_drones)
    ]

    engine = Engine(graph, drones, end)
    data = engine.run()
    print(f"\nTotal turns: {len(data)}")
    # screen width, height, graph, list of turns, start_zone
    map_name = maps.get(map_file, map_file)
    vis = Visualizer(1280, 780, 120, graph, data, start, map_name)
    vis.run()


if __name__ == "__main__":
    args = sys.argv
    if len(args) == 2:
        try:
            map_file = args[1]
            os.system("cls" if os.name == "nt" else "clear")
            main(map_file)
        except FileNotFoundError:
            print("\033[31m" + f"Map file {map_file} not found" + "\033[0m")
        except IsADirectoryError:
            print("\033[31m" + f"Map file {map_file}/ "
                  "cannot be a directory" + "\033[0m")
    else:
        print("Correct usage: python3 Fly-in.py map_file.txt")
