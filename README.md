# Fly-in
Multi-agent drone routing simulator in Python with custom pathfinding for dynamic networks. Handles concurrent drone movement, zone occupancy rules, and conflict resolution while optimizing for minimal simulation turns. Focuses on graph algorithms, OOP design, and performance under real-world constraints like bottlenecks and deadlock prevention.


### O que é o heapq?
É um módulo do Python que implementa uma fila de prioridade mínima — uma lista onde o elemento com o menor valor sai sempre primeiro, independentemente da ordem em que foi inserido.
Imagina uma fila normal num supermercado — entra quem chegou primeiro. Numa fila de prioridade, entra quem tem maior prioridade, neste caso menor custo.

```
heappush(heap, elemento) — adiciona um elemento à fila mantendo a ordem:
pythonheapq.heappush(heap, (3, "junction"))  # adiciona zona com custo 3

heapq.heappush(heap, (1, "path_a"))    # adiciona zona com custo 1
# a fila internamente reorganiza-se para o menor ficar primeiro
heappop(heap) — retira e devolve o elemento com menor custo:
pythoncusto, nome = heapq.heappop(heap)  # devolve (1, "path_a") — o mais barato
```

Como usamos no Dijkstra:
heap começa: [(0, "start")]

1ª iteração → pop → (0, "start")
  vizinhos: junction (custo 1), path_b (custo 1)
  push → [(1, "junction"), (1, "path_b")]

2ª iteração → pop → (1, "junction")  ← menor custo sai primeiro
  vizinhos: goal (custo 2)
  push → [(1, "path_b"), (2, "goal")]

3ª iteração → pop → (1, "path_b")
  ...
Sem o heapq, terias de percorrer a lista inteira para encontrar a zona mais barata a cada passo — muito mais lento. O heapq garante que sempre exploramos o caminho mais barato primeiro, que é exatamente a essência do Dijkstra.

A simulação é um loop de turnos. A cada turno:

Para cada drone que não está entregue, tenta movê-lo para a próxima zona do seu path
Verifica se a zona destino tem capacidade disponível
Se sim, move o drone. Se não, o drone espera
Regista os movimentos desse turno no formato D1-zona D2-zona
Verifica se todos os drones chegaram ao goal
Se sim, termina


Main Bugs found while building this project:
Bug 1 — Zone.__new__(Zone)
Quando um drone entrava em trânsito para uma restricted zone, a current_zone ficava com um objeto inválido em vez de None. Isso fazia com que outros drones contassem esse drone como "presente" numa zona fantasma, bloqueando movimentos desnecessariamente.
Bug 2 — moving_out incompleto
O moving_out.add(drone.drone_id) não estava dentro do bloco RESTRICTED, então drones que entravam em trânsito não eram marcados como "a sair" — a zona anterior continuava "ocupada" para outros drones nesse mesmo turn.
O efeito combinado: em mapas com muitas restricted zones (como o circular loop e o challenger), cada drone bloqueava a zona anterior durante 1 turn extra desnecessário, causando uma fila em cascata. Com 6 drones no circular loop isso multiplicava rapidamente de ~9 para 25 turns, e no challenger de ~39 para 91.

why we start on index 1 on the drone_path instead of 0?

    so, if we started on 0 we would be saying, move to start,
    thats your next move, and while building this project i found
    that initializing at index 0 would put the drone in an 
    infinite loop and didnt leave the start, so we gotta start it at index 1
    as it is initialized at start anyways 

Drones were doing more than 1 move per turn


**Dijkstra**

- **Erro:** `new_cost` e `heappush` fora do `for loop` — só o último vizinho era processado, os outros eram ignorados.
- **Resolução:** Indentar corretamente o `new_cost` e o bloco `if neighbor.name not in costs` para dentro do `for loop`, garantindo que todos os vizinhos são processados.

---

**Motor de simulação — path_index**

- **Erro:** `path_index` a começar em `0` — o primeiro movimento era "mover para o start" onde o drone já estava, causando loop infinito.
- **Resolução:** Inicializar `path_index = 1` na classe `Drone`, saltando a zona inicial que já é a zona atual do drone quando é criado.

---

**Motor de simulação — delivered**

- **Erro:** `drone.delivered = True` fora do `if drones_in_zone < next_zone.max_drones` — os drones chegavam ao goal mas nunca eram marcados como entregues, causando loop infinito.
- **Resolução:** Indentar o `if next_zone.name == self.end_zone.name` para dentro do bloco de movimento, garantindo que só é executado quando o drone realmente se move.

---

**Motor de simulação — registo de conexão**

- **Erro:** A conexão era registada como usada antes de verificar se a zona destino tinha capacidade — ficava ocupada mesmo quando o drone não se movia.
- **Resolução:** Mover o registo da conexão para dentro do `if drones_in_zone < next_zone.max_drones`, garantindo que só é registada quando o drone realmente se move.

---

**Zonas restricted**

- **Erro:** Após implementar o trânsito de 2 turnos, o `circular_loop` piorou de 9 para 21 turnos porque todos os drones usavam o mesmo caminho com `max_link_capacity=1`.
- **Resolução:** Implementar o método `generate_paths` no `Graph` que encontra múltiplos caminhos alternativos excluindo zonas intermédias, distribuindo os drones por caminhos diferentes.

---

**Múltiplos caminhos**

- **Erro:** Todos os drones criados com o mesmo `path` — sem distribuição por caminhos alternativos, causando congestionamento e deadlocks.
- **Resolução:** Usar `generate_paths` em vez de `find_path` na criação dos drones, atribuindo a cada drone um caminho diferente com `paths[i % len(paths)]`.


