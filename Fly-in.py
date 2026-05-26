import os
import sys
from parsing import Parser
from graph.graph import Graph
from visualizer.visualizer import Visualizer
from drone.drone import Drone
from engine.engine import Engine

"""
Multi-agent drone routing simulator in Python with custom pathfinding for dynamic networks. Handles concurrent drone movement, zone occupancy rules, and conflict resolution while optimizing for minimal simulation turns. Focuses on graph algorithms, OOP design, and performance under real-world constraints like bottlenecks and deadlock prevention.
"""

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
    
    engine = Engine(graph, drones, end)
    data = engine.run()
    print(f"\nTotal turns: {len(data)}")
    # screen width, height, graph, list of turns, start_zone
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