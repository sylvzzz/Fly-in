*This project has been created as part of the 42 curriculum by <a href ="https://github.com/sylvzzz">dbotelho</a>*
# Fly-in
Multi-agent drone routing simulator in Python with custom pathfinding for dynamic networks. Handles concurrent drone movement, zone occupancy rules, and conflict resolution while optimizing for minimal simulation turns. Focuses on graph algorithms, OOP design, and performance under real-world constraints like bottlenecks and deadlock prevention.

![Demo](assets/demo.gif)


### Whats a heapq?
Heapq is a python module where we can use a lista (heapq) where the smallest value element goes out first, indenpendent of the order it was inserted. This is used in our Dijkstra algorithm pathfinder to get the smallest costing nodes and paths.

```Python
heappush(heap, elemento) # adds an element to the list keeping order

pythonheapq.heappush(heap, (2.0, "junction"))  # adds a zones with cost 2.0

heapq.heappush(heap, (1.0, "path_a"))    # adds a zone with cost 1.0
# the list reorganizes itself so the smallest item is always first

heappop(heap) # takes out the smallest cost item

cost, nome = heapq.heappop(heap)  # returns (1, "path_a") - cheapest node
```

<br>

# How its used on Dijkstra:

Heap starts: [(0, "start")]

1st iteration -> pop -> (0, "start")<br>
  neighbors: junction (cost 1), path_b (cost 1)<br>
  push -> [(1, "junction"), (1, "path_b")]<br>

2nd iteration -> pop -> (1, "junction")  <- smallest cost pops out first<br>
  neighbors: goal (cost 2)<br>
  push -> [(1, "path_b"), (2, "goal")]<br>

3rd iteration -> pop -> (1, "path_b")
  ...<br>

Without heapq we would need to iterate trough the list and find the smallest cost, something that would be quite inefecient. The heapq guarantees that we get the smallest cost every time first, the core of Dijkstras theory

The simulation is a loop of turns: 

For each drone thats not delivered, it tries to move it to the next zone of its path.
Checks if destiny has free space
If it does move the drone, else waits.
Records every move of each turn, with the syntax of (Drone_id-Zone_name) ex: D1-zone1 D2-zone2
Checks if all drones are delivered

<br>

# Resources

- [Dijkstra Algorithm](https://www.youtube.com/watch?v=EFg3u_E6eHU)
- [Heapq documentation](https://docs.python.org/3/library/heapq.html)
- [Pygame documentation](https://www.pygame.org/docs/)
- [Pygame crash course](https://www.youtube.com/watch?v=FfWpgLFMI7w)
- [Claude](https://claude.ai)