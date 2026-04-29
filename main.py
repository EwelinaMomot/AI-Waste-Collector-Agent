import pygame
import sys
from search.state import E, DX, DY
from search.astar import astar
from search.problem import GridSearchProblem
import random
from environment.global_state import GlobalState, Weather
from environment.grid import Grid # tu strzelam nazewnictwo - Martyna
from agent.agent import Agent # tu strzelam nazewnictwo - Ewelina

# do ustalenia:
GRID_WIDTH = 16
GRID_HEIGHT = 16
TILE_SIZE = 60
INFO_PANEL_WIDTH = 290
BOTTOM_STATUS_HEIGHT = 40
WINDOW_WIDTH = INFO_PANEL_WIDTH + (GRID_WIDTH * TILE_SIZE)
WINDOW_HEIGHT = (GRID_HEIGHT * TILE_SIZE) + BOTTOM_STATUS_HEIGHT
FPS = 30

# Koszty planowania A*.
# Łatwo można je zmieniać, aby pokazać zmianę trasy.
ACTION_COSTS = {
    "przód": 1,
    "obrót w lewo": 1,
    "obrót w prawo": 1,
}

CELL_ENTRY_COSTS = {
    "grass": 1,
    "house": 10,
    "dumpster": 5,
    "station": 5,
}

def scale(path):
    img = pygame.image.load(path)
    return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))


def load_assets():
    assets = {
        "grass": scale("assets/grass.png"),
        "agent": scale("assets/garbage_truck.png"),
        "station": scale("assets/station.png"),
        "dump_mixed": scale("assets/dump_mixed.png"),
    }
    for key, name in [
        ("house_paper", "house_paper.png"),
        ("house_paper_empty", "house_paper_empty.png"),
        ("house_plastic", "house_plastic.png"),
        ("house_plastic_empty", "house_plastic_empty.png"),
        ("house_glass", "house_glass.png"),
        ("house_glass_empty", "house_glass_empty.png"),
        ("house_bio", "house_bio.png"),
        ("house_bio_empty", "house_bio_empty.png"),
        ("house_mixed", "house_mixed.png"),
        ("house_mixed_empty", "house_mixed_empty.png"),
        ("dump_paper", "dump_paper.png"),
        ("dump_plastic", "dump_plastic.png"),
        ("dump_glass", "dump_glass.png"),
        ("dump_bio", "dump_bio.png"),
    ]:
        assets[key] = scale(f"assets/{name}")
    return assets


def draw_infoPanel(screen, agent, global_state):
    font = pygame.font.SysFont('Consolas', 20, bold=True)
    
    pygame.draw.rect(screen, (255, 255, 255), (0, 0, INFO_PANEL_WIDTH, WINDOW_HEIGHT))
    pygame.draw.line(screen, (0, 0, 0), (INFO_PANEL_WIDTH, 0), (INFO_PANEL_WIDTH, WINDOW_HEIGHT))

    x_start = 20
    y_current = 20

    # 1. ZASOBY AGENTA
    current_fuel = agent.knowledge_base["resources"]["current_fuel"]
    max_fuel = agent.knowledge_base["resources"]["fuel_capacity"]
    fuel_percent = max(0.0, current_fuel / max_fuel)

    current_trash = agent.knowledge_base["resources"]["current_trash"]
    max_trash = agent.knowledge_base["resources"]["trash_capacity"]
    trash_percent = min(1.0, current_trash / max_trash)
    
    bar_width = 120
    bar_height = 22

    # wyświetlanie paliwa
    screen.blit(font.render("Paliwo:", True, (0, 0, 0)), (x_start, y_current))
    pygame.draw.rect(screen, (200, 200, 200), (x_start + 80, y_current, bar_width, bar_height))
    fuel_color = (92, 255, 94) if fuel_percent > 0.3 else (255, 56, 56)
    pygame.draw.rect(screen, fuel_color, (x_start + 80, y_current, int(bar_width * fuel_percent), bar_height))
    pygame.draw.rect(screen, (0, 0, 0), (x_start + 80, y_current, bar_width, bar_height), 1)
    screen.blit(font.render(f"{int(current_fuel)}%", True, (0, 0, 0)), (x_start + 73 + bar_width + 10, y_current))

    y_current += 40

    # wyświetlanie zapełnienia śmieciarki
    screen.blit(font.render("Śmieci:", True, (0, 0, 0)), (x_start, y_current))
    pygame.draw.rect(screen, (200, 200, 200), (x_start + 80, y_current, bar_width, bar_height))
    trash_color = (153, 212, 255)
    pygame.draw.rect(screen, trash_color, (x_start + 80, y_current, int(bar_width * trash_percent), bar_height))
    pygame.draw.rect(screen, (0, 0, 0), (x_start + 80, y_current, bar_width, bar_height), 1)
    screen.blit(font.render(f"{int(current_trash)}/{max_trash}", True, (0, 0, 0)), (x_start + 73 + bar_width + 10, y_current))
    
    y_current += 60

    # 2. CZAS I ŚRODOWISKO
    screen.blit(font.render(f"Dzień: {global_state.current_day}", True, (0, 0, 0)), (x_start, y_current))
    y_current += 30
    screen.blit(font.render(f"Pora: {global_state.current_season.name}", True, (0, 0, 0)), (x_start, y_current))
    y_current += 30
    screen.blit(font.render(f"Pogoda: {global_state.current_weather.name}", True, (0, 0, 0)), (x_start, y_current))
    y_current += 30
    screen.blit(font.render(f"Spalanie: x{agent.fuel_consumption_rate}", True, (0, 0, 0)), (x_start, y_current))

    y_current += 60
    
    # 3. HARMONOGRAM
    allowed_list = global_state.get_allowed_types_today()
    allowed_str = ", ".join(allowed_list) if allowed_list else "Brak wywozu"
    screen.blit(font.render("Dzisiaj zbieramy:", True, (255, 132, 222)), (x_start, y_current))
    screen.blit(font.render(allowed_str, True, (0, 0, 0)), (x_start, y_current + 25))

    y_current += 80

    # 4. STATUS AGENTA
    status_bg_rect = (INFO_PANEL_WIDTH, GRID_HEIGHT * TILE_SIZE, WINDOW_WIDTH - INFO_PANEL_WIDTH, BOTTOM_STATUS_HEIGHT)
    pygame.draw.rect(screen, (255, 255, 255), status_bg_rect)
    
    status_label = font.render("KOMUNIKAT: ", True, (255, 56, 56))
    status_val = font.render(agent.last_status, True, (0, 0, 0))
    
    text_y = GRID_HEIGHT * TILE_SIZE + 10
    screen.blit(status_label, (INFO_PANEL_WIDTH + 10, text_y))
    screen.blit(status_val, (INFO_PANEL_WIDTH + 10 + status_label.get_width(), text_y))


def calculate_path_coords(start_x, start_y, start_dir, planned_path):
    coords = []
    curr_x = start_x
    curr_y = start_y
    curr_d = start_dir
    
    # TILE_SIZE // 2 przesuwa nas idealnie na środek kwadratu
    coords.append((curr_x * TILE_SIZE + TILE_SIZE // 2, curr_y * TILE_SIZE + TILE_SIZE // 2))
    
    for action in planned_path:
        if action == "obrót w lewo":
            curr_d = (curr_d - 1) % 4
        elif action == "obrót w prawo":
            curr_d = (curr_d + 1) % 4
        elif action == "przód":
            curr_x += DX[curr_d]
            curr_y += DY[curr_d]
            # po zrobieniu kroku w przód, zapisujemy nowy punkt do narysowania
            coords.append((curr_x * TILE_SIZE + TILE_SIZE // 2, curr_y * TILE_SIZE + TILE_SIZE // 2))
    return coords


def draw_weather_effects(screen, global_state, particles):
    # jeśli świeci słońce, czyścimy niebo i uciekamy z funkcji
    if global_state.current_weather == Weather.SUNNY:
        particles.clear()
        return

    # tworzenie nowych opadów na górze ekranu
    if global_state.current_weather == Weather.RAINY:
        for _ in range(3): # deszcz pada gęsto (3 krople co klatkę)
            x = random.randint(0, WINDOW_WIDTH)
            speed_y = random.randint(10, 15) # szybko spada
            particles.append({"type": "rain", "x": x, "y": 0, "speed_y": speed_y, "speed_x": 1})
            
    elif global_state.current_weather == Weather.SNOWY:
        if random.random() < 0.3: # śnieg pada rzadziej
            x = random.randint(0, WINDOW_WIDTH)
            speed_y = random.randint(2, 4) # wolno spada
            speed_x = random.choice([-1, 0, 1]) # unosi się lekko na boki
            particles.append({"type": "snow", "x": x, "y": 0, "speed_y": speed_y, "speed_x": speed_x})

    # rysowanie i opadanie w dół
    for p in particles[:]:
        p["x"] += p["speed_x"]
        p["y"] += p["speed_y"]

        if p["type"] == "rain":
            # rysujemy niebieską kreskę
            pygame.draw.line(screen, (144, 231, 252), (p["x"], p["y"]), (p["x"] + p["speed_x"], p["y"] + 10), 2)
        elif p["type"] == "snow":
            # rysujemy białe kółko
            pygame.draw.circle(screen, (255, 255, 255), (int(p["x"]), int(p["y"])), 3)

        # jeśli spadło poniżej mapy, to usuwamy z pamięci
        if p["y"] > GRID_HEIGHT * TILE_SIZE:
            particles.remove(p)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Inteligentna Śmieciarka")
    clock = pygame.time.Clock()

    assets = load_assets()

    global_state = GlobalState()

    grid = Grid(GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, global_state)
    agent = Agent(start_x=0, start_y=0, initial_direction=E)

    planned_path = []  # Tu będziemy przechowywać listę akcji z A*
    path_coords = []   # tu będziemy trzymać piksele naszej linii
    weather_particles = [] # tu trzymamy płatki śniegu i deszcz
    current_target = None # Współrzędne celu, do którego jedziemy

    running = True
    frame_count = 0  

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # zmiana dnia po wciśnięciu klawisza 'N'
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:
                    global_state.next_day()
                    for h in grid.iter_houses():
                        h.generate_trash(global_state)
                        
                    agent.sync_knowledge(global_state)

                # zmiana celu: Po wciśnięciu SPACJI śmieciarka wybiera nowy cel i szuka do niego drogi
                if event.key == pygame.K_SPACE:
                    target_node = None
                    station = grid.cells[0][GRID_WIDTH - 1]

                    # PRIORYTET 1: agent sprawdza swój bak
                    if agent.check_fuel_reserve(station):
                        target_node = station
                        msg = "MAŁO PALIWA! Rzucam wszystko i jadę na stację!"
                        print(msg)
                        agent.last_status = msg
                    
                    # PRIORYTET 2: śmieciarka jest pełna (próg 75, bo z domku może dojść nawet 25kg)
                    elif agent.knowledge_base["resources"]["current_trash"] >= 75:
                        biggest_trash_type = max(agent.inventory, key=agent.inventory.get)
                        
                        # przeszukujemy mapę w poszukiwaniu odpowiedniego kontenera na wysypisku
                        for y in range(grid.height):
                            for x in range(grid.width):
                                cell = grid.cells[y][x]
                                if cell and hasattr(cell, 'zone_type') and cell.zone_type == biggest_trash_type:
                                    target_node = cell
                                    msg = f"ŚMIECIARKA PEŁNA! Jadę na wysypisko wyrzucić: {biggest_trash_type}"
                                    print(msg)
                                    agent.last_status = msg
                                    break
                            if target_node:
                                break
                    
                    # PRIORYTET 3: jeśli paliwa i miejsca jest dużo, szukamy najbliższego domu ze śmieciami
                    else:
                        allowed_today = global_state.get_allowed_types_today()

                        valid_houses = [h for h in grid.iter_houses() if h.needs_collection and h.trash_type in allowed_today] # lista wszystkich domów z których możena odebrać śmieci

                        if valid_houses:
                            # wybieramy ten dom, do którego jest najbliżej w linii prostej (odległość Manhattana)
                            target_node = min(valid_houses, key=lambda h: abs(h.x - agent.x) + abs(h.y - agent.y))
                            print(f"\nZnalazłem najbliższy dom! Jadę po: {target_node.trash_type}")
                        else:
                            # jeśli agent nic nie znalazł (bo np. zebrał już wszystko na dziś)                       
                            if (agent.x, agent.y) != (station.x, station.y):
                                # Ustawiamy cel na stację jako "powrót do domu"
                                target_node = station 
                                msg="\nKoniec pracy na dziś! Wracam do bazy."
                            else:
                                msg="\nJestem w bazie. Wciśnij 'N', żeby zacząć nowy dzień."                         
                            print(msg)
                            agent.last_status = msg
                    
                    if target_node:
                        current_target = (target_node.x, target_node.y)
                        # Tworzymy problem wyszukiwania
                        problem = GridSearchProblem(
                            grid,
                            target_node.x,
                            target_node.y,
                            action_costs=ACTION_COSTS,
                            cell_entry_costs=CELL_ENTRY_COSTS,
                        )
                        path_result, visited_nodes = astar((agent.x, agent.y, agent.direction), current_target, problem) 
                        planned_path = path_result or []

                        # zapisuje odwiedzone węzły w agencie, żeby mieć do nich dostęp przy rysowaniu
                        agent.last_visited_nodes = visited_nodes

                        print(f"\nZaplanowana trasa do {current_target}: {planned_path}")

                        path_coords = calculate_path_coords(agent.x, agent.y, agent.direction, planned_path)
       
        frame_count += 1
        if frame_count >= 15:  # Ruszaj się co pół sekundy
           # WYKONANIE RUCHU: Jeśli mamy zaplanowaną ścieżkę, wykonujemy jeden krok co kilka klatek
            if planned_path:
                next_action = planned_path.pop(0) # Pobierz pierwszą akcję z listy
                agent.execute_action(next_action, global_state,grid)

                # odświeżamy linię po każdym kroku agenta (żeby znikała z tyłu)
                path_coords = calculate_path_coords(agent.x, agent.y, agent.direction, planned_path)
                
                #Jeśli to był ostatni krok, zbierz śmieci
                if not planned_path:
                    cell = grid.cells[agent.y][agent.x]
                    # stoimy na domku ze śmieciami do zebrania
                    if cell and hasattr(cell, 'needs_collection'):
                        agent.last_status = f"Zebrano: {cell.trash_type}, {cell.trash_weight} kg"
                        agent.collect_trash(cell, global_state)
                        print(f"\nZebrano śmieci! Zapełnienie śmieciarki: {agent.knowledge_base['resources']['current_trash']} kg")
                    # stoimy na stacji paliw
                    elif cell and hasattr(cell, 'refill_agent'):
                        cell.refill_agent(agent)
                        print("\nZatankowano do pełna!")
                    # stoimy na wysypisku
                    elif cell and hasattr(cell, 'zone_type'):
                        agent.empty_tank(cell, global_state)
                        print(f"\nWyrzucono śmieci do strefy {cell.zone_type}! Aktualne zapełnienie: {agent.knowledge_base['resources']['current_trash']} kg")

        screen.fill((255, 255, 255))

        grid.draw(screen, assets)

        # RYSOWANIE WIZUALIZACJI A* (Heatmapa)
        if hasattr(agent, 'last_visited_nodes'):
            for node in agent.last_visited_nodes:
                vx, vy, _ = node
                rect = pygame.Surface((TILE_SIZE, TILE_SIZE))
                rect.set_alpha(60) # przezroczystość (im więcej razy algorytm sprawdził pole, tym będzie bardziej różowe!)
                rect.fill((251, 82, 231))
                screen.blit(rect, (vx * TILE_SIZE+ INFO_PANEL_WIDTH, vy * TILE_SIZE))

        # RYSOWANIE ŚCIEŻKI
        if len(path_coords) > 1:
            offset_coords = [(cx + INFO_PANEL_WIDTH, cy) for cx, cy in path_coords]
            pygame.draw.lines(screen, (255, 0, 0), False, offset_coords, 4)
            cel_x, cel_y = offset_coords[-1]
            pygame.draw.circle(screen, (0, 0, 255), (cel_x, cel_y), 5)

        agent.draw(screen, assets, TILE_SIZE)

        draw_weather_effects(screen, global_state, weather_particles)

        # Rysowanie tła panelu (opcjonalnie, żeby oddzielić od mapy)
        pygame.draw.rect(screen, (255, 255, 255), (0, 0, INFO_PANEL_WIDTH, WINDOW_HEIGHT))
        
        # Wyświetlenie informacji o stanie
        draw_infoPanel(screen, agent, global_state)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()