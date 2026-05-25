# Fly-in — Como funciona o Engine e o Dijkstra

---

## Dijkstra — `find_path`

### O que é o Dijkstra?

O Dijkstra é um algoritmo de pathfinding que encontra o caminho **mais curto** entre dois nós num grafo com pesos. "Mais curto" significa o caminho com o **menor custo total**, onde cada aresta (conexão) tem um peso (custo em turns).

### Como funciona no teu código

```python
heap = [(0, start.name)]
costs = {start.name: 0}
came_from = {start.name: None}
```

Três estruturas de dados:
- **`heap`** — fila de prioridade (min-heap). Guarda `(custo, nome_zona)`. O elemento com menor custo é sempre processado primeiro.
- **`costs`** — dicionário que guarda o menor custo conhecido para chegar a cada zona.
- **`came_from`** — dicionário que guarda de onde viemos para chegar a cada zona. Usado no final para reconstruir o caminho.

### O loop principal

```python
while heap:
    current_cost, current_name = heapq.heappop(heap)
```

A cada iteração, retira o nó com menor custo da heap. Este é o nó que vamos explorar agora.

```python
if current_name == end.name:
    # reconstruir o caminho
```

Se chegámos ao destino, reconstruímos o caminho percorrendo `came_from` de trás para a frente e invertemos.

### Exploração de vizinhos

```python
for connection in self.adjacency[current_name]:
    neighbor = connection.zone2 if connection.zone1.name == current_name else connection.zone1

    if neighbor.zone_type == ZoneType.BLOCKED:
        continue  # zona inacessível, ignora

    move_cost = 2 if neighbor.zone_type == ZoneType.RESTRICTED else 1
    new_cost = current_cost + move_cost

    if neighbor.name not in costs or new_cost < costs[neighbor.name]:
        costs[neighbor.name] = new_cost
        came_from[neighbor.name] = current_name
        heapq.heappush(heap, (new_cost, neighbor.name))
```

Para cada vizinho:
1. Se for `BLOCKED`, ignora.
2. Calcula o custo de mover para lá (`RESTRICTED` custa 2, resto custa 1).
3. Se o novo custo for melhor que o conhecido, atualiza e adiciona à heap.

### `excluded_zones`

Parâmetro opcional que permite forçar o algoritmo a ignorar certas zonas. Usado em `generate_paths` para encontrar caminhos alternativos.

---

## generate_paths — Distribuição de drones por caminhos

### Objetivo

Encontrar múltiplos caminhos distintos e distribuir os drones entre eles para maximizar o paralelismo e reduzir congestionamento.

### Como funciona

```python
path = self.find_path(start, end)
distinct_paths.append(path)
```

Começa com o caminho mais curto.

```python
for existing in distinct_paths:
    for zone_name in intermediate:
        alt = self.find_path(start, end, {zone_name})
        if alt and alt not in distinct_paths:
            distinct_paths.append(alt)
```

Para cada caminho já encontrado, tenta excluir cada zona intermédia individualmente e encontrar um caminho alternativo. Se encontrar um novo caminho (diferente dos já conhecidos), adiciona à lista. Repete até não encontrar mais nenhum novo.

```python
distinct_paths.sort(key=lambda p: self.path_cost(p))
min_cost = self.path_cost(distinct_paths[0])
best_paths = [p for p in distinct_paths if self.path_cost(p) == min_cost]
```

Ordena por custo e filtra apenas os caminhos com custo mínimo — não vale a pena enviar drones por rotas mais longas.

```python
for i in range(nb_drones):
    paths.append(best_paths[i % len(best_paths)])
```

Round-robin: distribui os drones ciclicamente pelos melhores caminhos. Com 3 caminhos e 9 drones: D1→C1, D2→C2, D3→C3, D4→C1, D5→C2, ...

---

## Engine — `run`

### Estrutura geral de cada turn

```python
while not all(drone.delivered for drone in self.drones):
    self.turns += 1
    self.connections_used = {}
    turn_moves = []
    moving_out = set()

    # Reset flags
    for drone in self.drones:
        drone.arrived_this_turn = False

    # Passo 1: chegadas de trânsito
    # Passo 2: movimentos normais

    if turn_moves:
        print(" ".join(turn_moves))
```

A cada turn:
- `connections_used` — reset do registo de conexões usadas (limite `max_link_capacity`).
- `turn_moves` — lista dos movimentos deste turn para o output.
- `moving_out` — set de IDs de drones que já se moveram (para libertar capacidade corretamente).
- `arrived_this_turn` — flag que impede double-move em drones que chegaram do trânsito.

---

### Passo 1 — Chegadas de trânsito (restricted zones)

Quando um drone entra em trânsito para uma `restricted` zone, demora **2 turns** a chegar. O primeiro turn fica "na connection" (`in_transit=True`, `current_zone=None`). O segundo turn é obrigatório — o drone DEVE chegar.

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
        and d.drone_id not in moving_out  # não conta quem já saiu este turn
    ])

    if drones_in_dest < destination.max_drones:
        moving_out.add(drone.drone_id)
        drone.current_zone = destination
        drone.in_transit = False
        drone.arrived_this_turn = True
        turn_moves.append(f"D{drone.drone_id}-{destination.name}")
```

Depois de chegar, tenta encadear imediatamente para a próxima zona se também for `restricted`:

```python
if drone.path_index < len(drone.path):
    next_zone = drone.path[drone.path_index]
    if next_zone.zone_type == ZoneType.RESTRICTED:
        # verifica espaço no destino seguinte
        if conn_ok and drones_in_next + already_arriving < next_zone.max_drones:
            conn_name = f"{drone.current_zone.name}-{next_zone.name}"
            drone.in_transit = True
            drone.current_zone = None
            drone.arrived_this_turn = False  # já se moveu, não bloquear
```

Isto evita perder 1 turn desnecessário entre duas `restricted` zones consecutivas.

---

### Passo 2 — Movimentos normais

```python
for drone in self.drones:
    if drone.delivered or drone.in_transit:
        continue
    if drone.arrived_this_turn:
        continue  # já se moveu neste turn (chegou do trânsito)
```

Salta drones já entregues, em trânsito, ou que chegaram do trânsito neste turn.

**Verificação de capacidade da zona destino:**
```python
drones_in_zone = len([
    d for d in self.drones
    if d.current_zone is not None
    and d.current_zone.name == next_zone.name
    and not d.delivered
    and d.drone_id not in moving_out  # quem já saiu não conta
])

if drones_in_zone >= next_zone.max_drones:
    continue  # zona cheia, drone espera
```

**Verificação de capacidade da conexão:**
```python
conn_key = f"{min(z1, z2)}-{max(z1, z2)}"
if self.connections_used.get(conn_key, 0) >= connection.max_link_capacity:
    continue  # conexão cheia, drone espera
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
    continue  # não há espaço garantido no próximo turn — não entra em trânsito

conn_name = f"{drone.current_zone.name}-{next_zone.name}"
drone.in_transit = True
drone.transit_destination = next_zone
drone.current_zone = None  # drone está na connection, não numa zona
drone.path_index += 1
turn_moves.append(f"D{drone.drone_id}-{conn_name}")
```

O `already_arriving` é crucial — garante que o drone só entra em trânsito se tiver espaço garantido no destino no próximo turn. Sem isto, o drone ficaria bloqueado na connection indefinidamente, violando o subject.

**Movimento normal:**
```python
drone.current_zone = next_zone
drone.path_index += 1
turn_moves.append(f"D{drone.drone_id}-{next_zone.name}")
if next_zone.name == self.end_zone.name:
    drone.delivered = True
```

---

### Regra de libertação de capacidade

O subject diz: *"Drones moving out of a zone free up capacity for that same turn."*

Isto é implementado através do set `moving_out`. Quando contamos drones numa zona, excluímos os que já foram marcados como `moving_out` — como se já tivessem saído. Isto permite que outro drone entre na mesma zona no mesmo turn, desde que haja espaço após as saídas.

---

### Output format

```python
if turn_moves:
    print(" ".join(turn_moves))
```

Cada turn é uma linha. Os movimentos são separados por espaço:
- `D1-goal` — movimento normal para zona `goal`
- `D1-start-loop_a` — drone em trânsito para `loop_a` (restricted), está na connection `start-loop_a`

Drones que não se movem são omitidos. Drones entregues desaparecem do output.