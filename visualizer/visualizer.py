import pygame
from graph.graph import Graph
from zone.zone import Zone


class Visualizer:
    def __init__(self, WIDTH: int, HEIGHT: int, FPS: int,
                 graph: Graph, history: list[dict], start_zone: Zone) -> None:
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.FPS = FPS
        self.graph = graph
        self.sidebar_width = WIDTH // 8  # sidebar takes 1/8 of width
        self.game_width = WIDTH - self.sidebar_width  # game area width
        self.history = history
        # Simulation state
        self.current_turn = 0
        self.total_turns = len(history)
        self.is_paused = False
        self.animation_progress: float = 0.0  # 0.0 = início, 1.0 = fim
        self.animation_speed: float = 0.05   # quanto avança por frame
        
        self.start_zone = start_zone

        self.ZONE_RADIUS = None  # computed automatically
        self.ZONE_COLORS = {
            "green":    (50, 200, 50),
            "blue":     (50, 100, 255),
            "red":      (220, 50, 50),
            "orange":   (255, 165, 0),
            "purple":   (180, 50, 180),
            "black":    (0, 0, 0),
            "brown":    (139, 69, 19),
            "maroon":   (128, 0, 0),
            "gold":     (255, 215, 0),
            "darkred":  (139, 0, 0),
            "violet":   (238, 130, 238),
            "crimson":  (220, 20, 60),
            "rainbow":  (255, 0, 127),  # magenta for "rainbow"
        }
        self.zoom = 0.85  # 1.0 = no zoom; < 1 = zoom out; > 1 = zoom in
        self.pan_offset_x = 0  # panning offset in pixels
        self.pan_offset_y = 0
        self.pan_limit = 300  # maximum panning distance in pixels
        self.mouse_pressed = False  # track if mouse button is held
        self.mouse_prev_x = 0  # previous mouse position for delta calculation
        self.mouse_prev_y = 0
        self._scale_x = 1.0  # separate x and y scaling for independent spacing
        self._scale_y = 1.0
        self.ZONE_RADIUS = None  # will be computed based on average scale
        self._label_zoom_threshold = 1.0  # will be computed based on zone density

        self._compute_offsets()

    def _compute_offsets(self) -> None:
        if not self.graph.zones:
            self._scale_x = 1.0
            self._scale_y = 1.0
            self._map_center_x = 0
            self._map_center_y = 0
            return
        xs = [z.x for z in self.graph.zones.values()]
        ys = [z.y for z in self.graph.zones.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        map_w = max_x - min_x if max_x > min_x else 1
        map_h = max_y - min_y if max_y > min_y else 1

        padding = 80  # screen edge margin in pixels
        # Calculate independent scale for x and y dimensions
        self._scale_x = (self.WIDTH - padding) / map_w
        self._scale_y = (self.HEIGHT - padding) / map_h
        
        # Cap scales to reasonable max size (allows zones to spread)
        max_scale = 150  # max pixels per unit
        self._scale_x = min(self._scale_x, max_scale)
        self._scale_y = min(self._scale_y, max_scale)

        self.ZONE_RADIUS = max(6, int((self._scale_x + self._scale_y) / 2 * 0.2))  # radius based on average scale

        self._map_center_x = (min_x + max_x) / 2
        self._map_center_y = (min_y + max_y) / 2
        
        # Calculate label zoom threshold based on zone density
        num_zones = len(self.graph.zones)
        
        """
        Here we check for the number of zones because we dont
        want piled up zone names so for x number of zones we change the zoom 
        goal for showing up the labels.
        """
        if num_zones < 35:
            self._label_zoom_threshold = 0.60
        else:
            self._label_zoom_threshold = 1.45

    def to_screen(self, zx: int, zy: int) -> tuple[int, int]:
        sx = (zx - self._map_center_x) * self._scale_x * self.zoom + self.game_width // 2 + self.pan_offset_x
        sy = (zy - self._map_center_y) * self._scale_y * self.zoom + self.HEIGHT // 2 + self.pan_offset_y
        return (int(sx), int(sy))
    
    def draw_zones(self, screen) -> None:
        font = pygame.font.Font(None, 24)  # None = default font; 24 = font size
        r = int(self.ZONE_RADIUS * self.zoom)
        show_labels = self.zoom >= self._label_zoom_threshold  # adaptive threshold based on zone density
        for zone in self.graph.zones.values():
            cx, cy = self.to_screen(zone.x, zone.y)
            color = self.ZONE_COLORS.get(zone.color, (150, 150, 150))  # lookup color in dict, fallback to gray
            pygame.draw.circle(screen, color, (cx, cy), r)
            pygame.draw.circle(screen, "white", (cx, cy), r, 2)  # 2 = border thickness
            if show_labels:  # only render labels if zoom threshold met
                label = font.render(zone.name, True, "white")
                screen.blit(label, (cx - label.get_width() // 2, cy - r - 25))  # 25 = name offset above circle
    
    def draw_connections(self, screen) -> None:
        width = max(1, int(4 * self.zoom))  # 4 = base line thickness
        for conn in self.graph.connections:
            z1, z2 = conn.zone1, conn.zone2
            p1 = self.to_screen(z1.x, z1.y)
            p2 = self.to_screen(z2.x, z2.y)
            pygame.draw.line(screen, "gray", p1, p2, width)
    
    def _on_window_resized(self, new_width: int, new_height: int) -> None:
        """Handle window resize event - recalculate offsets for new dimensions."""
        self.WIDTH = new_width
        self.HEIGHT = new_height
        self.sidebar_width = new_width // 8
        self.game_width = new_width - self.sidebar_width
        self._compute_offsets()
    
    def draw_sidebar(self, screen) -> None:
        """Draw sidebar with legend, turn info, and commands."""
        sidebar_x = self.game_width
        sidebar_rect = pygame.Rect(sidebar_x, 0, self.sidebar_width, self.HEIGHT)
        pygame.draw.rect(screen, (30, 30, 30), sidebar_rect)  # dark background
        pygame.draw.line(screen, (100, 100, 100), (sidebar_x, 0), (sidebar_x, self.HEIGHT), 2)  # divider
        
        font_title = pygame.font.Font(None, 20)
        font_text = pygame.font.Font(None, 16)
        
        y_offset = 15
        
        # Turn info
        turn_text = f"Turn: {self.current_turn}/{self.total_turns}"
        turn_label = font_title.render(turn_text, True, "white")
        screen.blit(turn_label, (sidebar_x + 10, y_offset))
        y_offset += 35
        
        # Status (paused/playing)
        status = "PAUSED" if self.is_paused else "PLAYING"
        status_color = (255, 100, 100) if self.is_paused else (100, 255, 100)
        status_label = font_text.render(f"Status: {status}", True, status_color)
        screen.blit(status_label, (sidebar_x + 10, y_offset))
        y_offset += 25
        
        
        # Commands section
        y_offset += 10
        commands_title = font_title.render("Commands:", True, (200, 200, 200))
        screen.blit(commands_title, (sidebar_x + 10, y_offset))
        y_offset += 25
        
        commands = [
            "+  Zoom in",
            "-  Zoom out",
            "Space  Play/Pause",
            "<-  Prev turn",
            "Arror Down  Decrease FPS",
            "Arrow Up  Increase FPS",
            "->  Next turn",
            "R  Reset view",
            "S  Restart Simulation",
            "E  Finnish Simulation",
            "Q  Quit"
        ]
        
        for cmd in commands:
            cmd_label = font_text.render(cmd, True, (180, 180, 180))
            screen.blit(cmd_label, (sidebar_x + 10, y_offset))
            y_offset += 18
        
        # Drones section
        y_offset += 15
        drones_title = font_title.render("Drones:", True, (200, 200, 200))
        screen.blit(drones_title, (sidebar_x + 10, y_offset))
        y_offset += 25

        fps_info = font_text.render(f"FPS: {self.FPS}", True, (200, 200, 200))
        screen.blit(fps_info, (sidebar_x + 10, y_offset))
        
        y_offset += 35

        if self.history and self.current_turn > 0:
            turn_data = self.history[self.current_turn - 1]
            
            for i, drone in enumerate(turn_data["drones"]):
                if drone["delivered"]:
                    status_text = "DELIVERED"
                    color = (100, 255, 100)
                else:
                    zone = drone.get("zone", "?")
                    status_text = f"at {zone}"
                    color = (200, 200, 200)
                
                drone_label = font_text.render(f"D{i+1}: {status_text}", True, color)
                screen.blit(drone_label, (sidebar_x + 10, y_offset))
                y_offset += 15

    def draw_drones(self, screen: pygame.Surface, drone_img: pygame.Surface) -> None:
        import math

        # turno 0 — estado inicial, todos os drones no start
        if not self.history:
            return
        
        # posição atual
        turn_data = self.history[self.current_turn - 1]

        # posição anterior (se existir)
        if self.current_turn > 1:
            prev_turn_data = self.history[self.current_turn - 2]
        else:
            prev_turn_data = None

        if self.current_turn == 0:
            total = len(self.history[0]["drones"])
            cx_base, cy_base = self.to_screen(self.start_zone.x, self.start_zone.y)
            for idx in range(total):
                cx, cy = cx_base, cy_base
                if total > 1:
                    angle = (idx / total) * 2 * math.pi
                    cx += int(math.cos(angle) * 15)
                    cy += int(math.sin(angle) * 15)
                img_rect = drone_img.get_rect(center=(cx, cy))
                screen.blit(drone_img, img_rect)
            return

        turn_data = self.history[self.current_turn - 1]

        # contar quantos drones estão em cada zona
        zone_drone_count: dict[str, int] = {}
        for d in turn_data["drones"]:
            if d["delivered"]:
                continue
            name = d["zone"] or d["dest"]
            if name:
                zone_drone_count[name] = zone_drone_count.get(name, 0) + 1

        zone_drone_index: dict[str, int] = {}

        for drone in turn_data["drones"]:
            if drone["delivered"]:
                continue
            zone_name = drone["zone"] or drone["dest"]
            if zone_name is None:
                continue

            zone = self.graph.zones.get(zone_name)
            if zone is None:
                continue

            cx, cy = self.to_screen(zone.x, zone.y)

            # interpolar com posição anterior
            if prev_turn_data:
                prev_zone_name = None
                for pd in prev_turn_data["drones"]:
                    if pd["id"] == drone["id"]:
                        prev_zone_name = pd["zone"] or pd["dest"]
                        break
                if prev_zone_name:
                    prev_zone = self.graph.zones.get(prev_zone_name)
                    if prev_zone:
                        px, py = self.to_screen(prev_zone.x, prev_zone.y)
                        cx = int(px + (cx - px) * self.animation_progress)
                        cy = int(py + (cy - py) * self.animation_progress)

            idx = zone_drone_index.get(zone_name, 0)
            total = zone_drone_count[zone_name]
            if total > 1:
                angle = (idx / total) * 2 * math.pi
                cx += int(math.cos(angle) * 15)
                cy += int(math.sin(angle) * 15)
            zone_drone_index[zone_name] = idx + 1

            img_rect = drone_img.get_rect(center=(cx, cy))
            screen.blit(drone_img, img_rect)
    
    def run(self) -> None:
        pygame.init()
        screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        clock = pygame.time.Clock()
        background = pygame.image.load("assets/fundo.jpeg")

        # Scale background to fit the game area (without sidebar)
        background = pygame.transform.scale(background, (self.game_width, self.HEIGHT))
        drone_img = pygame.image.load("assets/bee.png").convert_alpha()
        drone_img = pygame.transform.scale(drone_img, (30, 30))  # ajusta o tamanho
        running = True
        pygame.display.set_caption("Fly-in by dbotelho")
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self._on_window_resized(event.w, event.h)
                    background = pygame.transform.scale(background, (self.game_width, self.HEIGHT))
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # left mouse button
                        self.mouse_pressed = True
                        self.mouse_prev_x, self.mouse_prev_y = event.pos
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.mouse_pressed = False
                elif event.type == pygame.MOUSEMOTION:
                    if self.mouse_pressed:
                        dx = event.pos[0] - self.mouse_prev_x
                        dy = event.pos[1] - self.mouse_prev_y
                        self.pan_offset_x += dx
                        self.pan_offset_y += dy
                        # Apply panning limits scaled by zoom level
                        effective_limit = self.pan_limit * self.zoom
                        self.pan_offset_x = max(-effective_limit, min(effective_limit, self.pan_offset_x))
                        self.pan_offset_y = max(-effective_limit, min(effective_limit, self.pan_offset_y))
                        self.mouse_prev_x, self.mouse_prev_y = event.pos

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_LEFT:
                        self.current_turn = max(0, self.current_turn - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.current_turn = min(self.total_turns, self.current_turn + 1)
                    elif event.key == pygame.K_r:
                        # Reset zoom and panning
                        self.zoom = 0.85
                        self.pan_offset_x = 0
                        self.pan_offset_y = 0

                    elif event.key == pygame.K_UP:
                        if self.FPS < 180:
                            self.FPS += 15
                    elif event.key == pygame.K_DOWN:
                        if self.FPS >= 30:
                            self.FPS -= 15
                        
                    elif event.key == pygame.K_s:
                        self.current_turn = 0
                    
                    elif event.key == pygame.K_e:
                        self.current_turn = len(self.history)

                    elif event.key == pygame.K_q:
                        running = False
            
            # Draw game area
            screen.blit(background, (0, 0))
            keys = pygame.key.get_pressed()
            if keys[pygame.K_EQUALS] or keys[pygame.K_PLUS]:
                self.zoom = min(self.zoom * 1.02, 3.0)  # 1.02 = zoom speed; 3.0 = max zoom
            if keys[pygame.K_MINUS]:
                self.zoom = max(self.zoom / 1.02, 0.7)  # 1.02 = zoom speed; 0.2 = min zoom
            self.draw_connections(screen)
            self.draw_zones(screen)
            self.draw_drones(screen, drone_img)
            
            # Draw sidebar
            self.draw_sidebar(screen)
            
            pygame.display.flip()
            if not self.is_paused:
                self.animation_progress += self.animation_speed
                if self.animation_progress >= 1.0:
                    self.animation_progress = 0.0
                    if self.current_turn < self.total_turns:
                        self.current_turn += 1

            clock.tick(self.FPS)
        pygame.quit()
