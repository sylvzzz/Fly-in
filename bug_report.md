# Main Bugs

**Engine - path_index**

- **Error:** `path_index` starting at `0`, the first move was "move to start" where the drone already was, causing an infinite loop.
- **Solution:** Inicialize `path_index = 1` on class `Drone`, jumping start zone, as thats the beggining anyways.

---

**Restricted zones**

- **Error:** After implementing 2 turn moves for restricted zones, the `circular_loop` map wasnt meeting target of moves beacause used the same path with `max_link_capacity=1`.
- **Solution:** Create a method `generate_paths` on `Graph` that finds multiple alternative paths excluding zones from previous generated paths, distributing drones by different paths.

---

**Performance on visualizer**

**Error:**

In the first version of the visualizer, inside the `draw_zones` and `draw_sidebar` methods, there were commands such as:
```python
def draw_zones(self, screen):
    font = pygame.font.Font(None, 24)  # <-- insane weight on performance, this was being created every frame
```

Why did this slow down the simulation?
The draw_zones method is executed on every single frame. If the simulation runs at 60 FPS, Pygame was forced to create a brand new Font object 60 times per second. If it ran at 180 FPS, it would do this 180 times.

To instantiate this object, the computer must access the system's font subsystem, read data from memory (or disk), and process vector data for rendering. Multiplied by the total number of zones and sidebar interface elements, this generated a massive and unnecessary CPU overhead, choking the frame rate and causing noticeable lag.

**Solution:**

Code Changes:
In the Constructor (__init__):
We allocate text assets a single time in memory.

```Python
pygame.font.init()
self.font_zones = pygame.font.Font(None, 24)
self.font_title = pygame.font.Font(None, 20)
self.font_text = pygame.font.Font(None, 16)
```
In the Drawing Methods (draw_zones and draw_sidebar):
We removed the local font declarations and updated the code to use the persistent object variables (self.font_...).

```Python
# Example in draw_zones:
label = self.font_zones.render(zone.name, True, "white")
```

With this solution i removed the lag completly.