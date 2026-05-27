# Fly-in — How the engine and the dijkstra work


## Dijkstra — `find_path`

### What is the DIJKSTRA algorithm?

THe Dijkstra alogrithm is a pathfinding algorithm commonly used for graphs to the **shortest path** between two nodes with costs in a graph. "Shortest" means the **smallest possible cost**, where each node (connection) has a cost (cost in turns). A real life example of Dijkstra's use could be Google Maps calculating the shortest trip possible on your phone from your current location to the destination you choose.

### How does it work in my code?

```python
# priority queue, stores (cost, zone) ordered by smallest cost
heap = [(0.0, start.name)]
# costs dict, stores smallest cost to get to each zone
costs: dict[str, float] = {start.name: 0.0}
# stores where "we" came from to memorize zone and path
came_from: dict[str, str | None] = {start.name: None}
```

Three main data structures:
- **`heap`** — priority queue, stores `(cost, zone_name)`. The smallest element is always first.
- **`costs`** — dictionary that stores the smallest possible cost to get to each zone.
- **`came_from`** — dictionary that stores where we came from to get to each zone, so we can rebuild the path at the end

### THe main loop

```python
while heap:
    current_cost, current_name = heapq.heappop(heap)
```

At eachy iteration we pop out the smallest cost node from the heap, thats the node we're navigating trough now.

```python
if current_name == end.name:
    # rebuild path
```

If we've arrived at the destiny we rebuild the path using `came_from` from the end to the start to invert the path.

### Exploring neighbor nodes

```python
for connection in self.adjacency[current_name]:
    neighbor = connection.zone2 if connection.zone1.name == current_name else connection.zone1

    if neighbor.zone_type == ZoneType.BLOCKED:
        continue  # innaccessible zone, cant use it

    move_cost = 2 if neighbor.zone_type == ZoneType.RESTRICTED else 1
    new_cost = current_cost + move_cost

    if neighbor.name not in costs or new_cost < costs[neighbor.name]:
        costs[neighbor.name] = new_cost
        came_from[neighbor.name] = current_name
        heapq.heappush(heap, (new_cost, neighbor.name))
```

For each neighbor:
1. If `BLOCKED`, ignores.
2. Calculates the cost to move to X zone (`RESTRICTED` costs 2, `NORMAL` costs 1, `PRIORITY` costs 0.9 so the dijkstra can prioritize to move there).
3. If the new cost is better than the previously known one, updates and adds it to the heap.

### `excluded_zones`

Optional attribute that allows the alogrithm to ignore certain zones so the method `generate_paths()` can return different paths for drones

---

## generate_paths — Distribute drones paths

### Goal

Find multiple paths to distribute drones to reduce congestion and keep drones moving.

### How it works

```python
path = self.find_path(start, end)
distinct_paths.append(path)
```

Starts with shortest path

```python
for existing in distinct_paths:
    for zone_name in intermediate:
        alt = self.find_path(start, end, {zone_name})
        if alt and alt not in distinct_paths:
            distinct_paths.append(alt)
```

For each zone already found, tries to exclude intermediary zones individually and find alternaives. If a new path different from the ones already know it adds the path to the list. This repeats until theres no more new paths.

```python
distinct_paths.sort(key=lambda p: self.path_cost(p))
min_cost = self.path_cost(distinct_paths[0])
best_paths = [p for p in distinct_paths if self.path_cost(p) == min_cost]
```

Orders by cost and filters only by the minimal cost, its not worth to send drones to high cost routes.

```python
for i in range(nb_drones):
    paths.append(best_paths[i % len(best_paths)])
```

This loop distributes the drones with the best paths possible. An example with 3 paths and 9 drones: D1→P1, D2→P2, D3→P3, D4→P1, D5→P2, ...

---

## Engine — `run`

### Structure for every turn

```python
while not all(drone.delivered for drone in self.drones):
    self.turns += 1
    self.connections_used = {}
    turn_moves = []
    moving_out = set()

    # Reset flags
    for drone in self.drones:
        drone.arrived_this_turn = False

    # Step 1: carrivals from transit
    # Step 2: normals turns

    if turn_moves:
        print(" ".join(turn_moves))
```

At each turn:
- `connections_used` - reset of record of used connections (limite `max_link_capacity`).
- `turn_moves` - list of moves this turn to print it on the terminal.
- `moving_out` - set of drone ID's of already moved drones (to store).
- `arrived_this_turn` - flag implemented to block drones from doing more than 1 move per turn

---

### Step 1 — Arrivals from transit (restricted zones)

When a drone enters transit to a `restricted zone`, it takes **2 turns** to travel, has a cost of 2 to the dijkstra chegar. O primeiro turn fica "na connection" (`in_transit=True`, `current_zone=None`). The second turn is mandatory, it must arrive.

```python
for drone in self.drones:
    if drone.delivered or not drone.in_transit:
        continue
    destination = drone.transit_destination

    drones_in_dest = len([
        d for d in self.drones
        if d.current_zone is not None
        and d.current_zone.name == destination.name
        and not d.delivered
        and d.drone_id not in moving_out  # doesnt count who already finnished this turn
    ])

    if drones_in_dest < destination.max_drones:
        moving_out.add(drone.drone_id)
        drone.current_zone = destination
        drone.in_transit = False
        drone.arrived_this_turn = True
        turn_moves.append(f"D{drone.drone_id}-{destination.name}")
```

After arriving, tries to immediately chain to the next zone if it is also `restricted`:

```python
if drone.path_index < len(drone.path):
    next_zone = drone.path[drone.path_index]
    if next_zone.zone_type == ZoneType.RESTRICTED:
        # checks for space in the next destination
        if conn_ok and drones_in_next + already_arriving < next_zone.max_drones:
            conn_name = f"{drone.current_zone.name}-{next_zone.name}"
            drone.in_transit = True
            drone.current_zone = None
            drone.arrived_this_turn = False  # if moved out, dont block the zone
```

This avoids losing an extra turn between two `restricted` zones consecutivas.

---

### Passo 2 — Normal Moves

```python
for drone in self.drones:
    if drone.delivered or drone.in_transit:
        continue
    if drone.arrived_this_turn:
        continue  # has moved this turn
```

Salta drones já entregues, em trânsito, ou que chegaram do trânsito neste turn.

**Verificação de capacidade da zona destino:**
```python
drones_in_zone = len([
    d for d in self.drones
    if d.current_zone is not None
    and d.current_zone.name == next_zone.name
    and not d.delivered
    and d.drone_id not in moving_out  # who moved out doesnt count
])

if drones_in_zone >= next_zone.max_drones:
    continue  # zone full, drone waits
```

**Verificação de capacidade da conexão:**
```python
conn_key = f"{min(z1, z2)}-{max(z1, z2)}"
if self.connections_used.get(conn_key, 0) >= connection.max_link_capacity:
    continue  # zone full, drone waits
self.connections_used[conn_key] += 1
```

**Movimento para restricted zone:**
```python
already_arriving = len([
    d for d in self.drones
    if d.transit_destination is not None
    and d.transit_destination.name == next_zone.name
])
if drones_in_zone + already_arriving >= next_zone.max_drones:
    continue  # no space guaranteed for next move, stays

conn_name = f"{drone.current_zone.name}-{next_zone.name}"
drone.in_transit = True
drone.transit_destination = next_zone
drone.current_zone = None  # drone is at connection , not a zone
drone.path_index += 1
turn_moves.append(f"D{drone.drone_id}-{conn_name}")
```

The `already_arriving` flag is crucial guarantees the drone only enters transit if space is guaranteed on the next zone. Without this he drone would stay at the connection, violating the project rule  `For multi-turn movements (restricted zones), the drone occupies the connection
during transit and MUST arrive at the destination after the specified number of
turns. It cannot wait on the connection for an empty space in the destination zone.`

**Normal movement:**
```python
drone.current_zone = next_zone
drone.path_index += 1
turn_moves.append(f"D{drone.drone_id}-{next_zone.name}")
if next_zone.name == self.end_zone.name:
    drone.delivered = True
```

---

### Free of capacity rule

The subject says: *"Drones moving out of a zone free up capacity for that same turn."*

This is implemented via the set() `moving_out`. When we count drones in a zone, we exclude the ones with `moving_out` as they already left. This allows another drones entering that zone, as long there is space for the drone.

---

### Output format

```python
if turn_moves:
    print(" ".join(turn_moves))
```

Each turn is a line printed on the terminal, each move is separated by a space:
- `D1-goal` - D1 made a made a normal move to zone `goal`
- `D1-start-loop_a` - drone moving to `loop_a` (restricted zone), is in the connection `start-loop_a`
