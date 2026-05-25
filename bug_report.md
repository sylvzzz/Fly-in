# Fly-in — Bug Report

---

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

**Zone.__new__ — zona fantasma em trânsito**

- **Erro:** Ao entrar em trânsito para uma `restricted` zone, `drone.current_zone` era definido com `Zone.__new__(Zone)` — um objeto `Zone` sem `__init__`, logo sem atributo `name`. Qualquer acesso a `.name` causava `AttributeError: 'Zone' object has no attribute 'name'`.
- **Resolução:** Substituir `Zone.__new__(Zone)` por `None` (`drone.current_zone = None`), tornando o tipo `Optional[Zone]` e filtrando com `d.current_zone is not None` em todas as listcomps de contagem de ocupação.

---

**Motor de simulação — double-move em trânsito**

- **Erro:** Um drone que chegava do trânsito no primeiro passo era adicionado a `moving_out`, mas o segundo passo não verificava esse set — o drone movia-se duas vezes no mesmo turn, violando a regra de um movimento por turn.
- **Resolução:** Adicionar a flag `arrived_this_turn: bool` na classe `Drone`. No primeiro passo, marcar `drone.arrived_this_turn = True` ao chegar. No segundo passo, saltar drones com `arrived_this_turn = True`. Reset da flag no início de cada turn.

---

**Motor de simulação — conn_name após None**

- **Erro:** `drone.current_zone` era posto a `None` antes de construir `conn_name = f"{drone.current_zone.name}-{next_zone.name}"` — causava `AttributeError: 'NoneType' object has no attribute 'name'`.
- **Resolução:** Guardar `conn_name` antes de pôr `current_zone = None`:
  ```python
  conn_name = f"{drone.current_zone.name}-{next_zone.name}"
  drone.current_zone = None
  ```

---

**Motor de simulação — drones em trânsito bloqueados**

- **Erro:** O subject diz que um drone em trânsito para uma `restricted` zone DEVE chegar no turn seguinte — não pode ficar à espera na connection. O engine não verificava a capacidade do destino antes de entrar em trânsito, podendo bloquear drones indefinidamente.
- **Resolução:** Antes de entrar em trânsito, verificar se há espaço garantido no destino no próximo turn, contando drones já em trânsito para essa zona (`already_arriving`). Se `drones_in_zone + already_arriving >= max_drones`, o drone espera em vez de entrar em trânsito.

---

**Motor de simulação — encadeamento de restricted zones**

- **Erro:** Um drone que chegava a uma `restricted` zone intermediária ficava bloqueado por `arrived_this_turn = True` e não podia entrar imediatamente em trânsito para a zona seguinte — perdia 1 turn desnecessário. Isto causava o `circular_loop` ter 16 turns em vez de 15.
- **Resolução:** No primeiro passo, após a chegada do trânsito, verificar imediatamente se o drone pode entrar em trânsito para a próxima zona da path. Se sim, encadear o movimento no mesmo turn e repor `arrived_this_turn = False`.

---

**generate_paths — caminhos alternativos não encontrados**

- **Erro:** A lógica anterior de `generate_paths` excluía todas as zonas intermédias do caminho anterior de uma vez — em grafos com entrada única (como o challenger), isso bloqueava todos os caminhos alternativos, resultando em apenas 1 caminho encontrado e todos os 25 drones em fila única.
- **Resolução:** Excluir apenas **uma** zona intermédia de cada vez por tentativa, iterando sobre cada zona do caminho existente. Isso permite encontrar desvios parciais que partilham a entrada mas divergem nas zonas intermédias.

---

**generate_paths — caminhos subótimos no round-robin**

- **Erro:** O round-robin distribuía drones igualmente por todos os caminhos encontrados, incluindo caminhos mais longos — drones eram enviados por rotas piores, aumentando o número de turns em mapas como `hard/01`.
- **Resolução:** Calcular o custo de cada caminho com `path_cost()`, ordenar por custo, e usar apenas os caminhos com custo mínimo (`best_paths`) para a distribuição round-robin. Caminhos mais longos são ignorados.



Based on my analysis of your code against the subject rules, here are the violations:
1. No validation that nb_drones is > 0 (parsing/parsing.py:143-144) — accepts 0 or negative. Rule VII.4 says "positive integer."
2. No validation that max_drones / max_link_capacity are > 0 (parsing/parsing.py:176-183, 256-264) — accepts 0 or negative. Rule VII.4 says "positive integers."
3. Transit arrivals don't account for simultaneous departures (engine/engine.py:36-42) — "Drones moving out of a zone free up capacity for that same turn" (VII.2/VII.3). When a transit drone arrives at a restricted zone, it checks occupancy of drones not in moving_out — but normal-move departures haven't been processed yet. So a transit arrival can be blocked by a drone that will leave the same turn.
4. Priority zones not prioritized in pathfinding (graph/graph.py:114-117) — Rule VII.3 says priority zones should be "preferred in pathfinding algorithms." Your find_path gives both NORMAL and PRIORITY cost 1, so there's no differentiation.