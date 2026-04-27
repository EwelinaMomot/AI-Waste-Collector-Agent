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
TILE_SIZE = 40
INFO_PANEL_HEIGHT = 100
WINDOW_WIDTH = GRID_WIDTH * TILE_SIZE
WINDOW_HEIGHT = (GRID_HEIGHT * TILE_SIZE) + INFO_PANEL_HEIGHT
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
    #TODO: dodać więcej danych do wyświetlenia
    font = pygame.font.SysFont('Arial', 22)

    # 1. ZASOBY AGENTA
    fuel_text = f"Paliwo: {int(agent.knowledge_base['resources']['current_fuel'])}%"
    current_trash = agent.knowledge_base["resources"]["current_trash"]
    trash_text = f"Pojemność: {current_trash}/{agent.knowledge_base['resources']['trash_capacity']}"
    
    # 2. CZAS I ŚRODOWISKO
    day_text = f"Dzień: {global_state.current_day}"
    season_text = f"Pora roku: {global_state.current_season.name}"
    weather_text = f"Pogoda: {global_state.current_weather.name} (Spalanie x{agent.fuel_consumption_rate})"
    
    # 3. HARMONOGRAM
    allowed_list = global_state.get_allowed_types_today()
    if allowed_list:
        allowed_str = ", ".join(allowed_list)
    else:
        allowed_str = "Brak wywozu (Niedziela)"
    schedule_text = f"Zbieramy: {allowed_str}"
    
    fuel_surf = font.render(fuel_text, True, (0, 0, 0))
    trash_surf = font.render(trash_text, True, (0, 0, 0))
    day_surf = font.render(day_text, True, (0, 0, 0))
    season_surf = font.render(season_text, True, (0, 0, 0))
    weather_surf = font.render(weather_text, True, (0, 0, 0))
    schedule_surf = font.render(schedule_text, True, (0, 0, 0))

    ui_y_start = GRID_HEIGHT * TILE_SIZE + 10

    # wiersz 1: Paliwo | Dzień | Pora roku
    screen.blit(fuel_surf, (20, ui_y_start))
    screen.blit(day_surf, (200, ui_y_start))
    screen.blit(season_surf, (400, ui_y_start))
    
    # wiersz 2: Zapełnienie śmieciarki | Pogoda i spalanie
    screen.blit(trash_surf, (20, ui_y_start + 30))
    screen.blit(weather_surf, (200, ui_y_start + 30))
    
    # wiersz 3: Harmonogram (na całą szerokość)
    screen.blit(schedule_surf, (20, ui_y_start + 60))


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
                        print("\nMAŁO PALIWA! Rzucam wszystko i jadę na stację!")
                    
                    # PRIORYTET 2: śmieciarka jest pełna (próg 75, bo z domku może dojść nawet 25kg)
                    elif agent.knowledge_base["resources"]["current_trash"] >= 75:
                        biggest_trash_type = max(agent.inventory, key=agent.inventory.get)
                        
                        # przeszukujemy mapę w poszukiwaniu odpowiedniego kontenera na wysypisku
                        for y in range(grid.height):
                            for x in range(grid.width):
                                cell = grid.cells[y][x]
                                if cell and hasattr(cell, 'zone_type') and cell.zone_type == biggest_trash_type:
                                    target_node = cell
                                    print(f"\nŚMIECIARKA PEŁNA! Jadę na wysypisko wyrzucić: {biggest_trash_type}")
                                    break
                            if target_node:
                                break
                    
                    # PRIORYTET 3: jeśli paliwa i miejsca jest dużo, szukamy domu ze śmieciami
                    else:
                        allowed_today = global_state.get_allowed_types_today()

                        for h in grid.iter_houses():
                            if h.needs_collection and (h.trash_type in allowed_today): # Sprawdzamy, czy dom ma śmieci
                                target_node = h
                                break

                        # jeśli agent nic nie znalazł (bo np. zebrał już wszystko na dziś)
                        if target_node is None:
                            print("\nWszystkie dozwolone śmieci zebrane! Wciśnij 'N', żeby zmienić dzień.")
                    
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
                        planned_path = astar((agent.x, agent.y, agent.direction), current_target, problem) or []
                        print(f"\nZaplanowana trasa do {current_target}: {planned_path}")

                        path_coords = calculate_path_coords(agent.x, agent.y, agent.direction, planned_path)
       
        frame_count += 1
        if frame_count >= 15:  # Ruszaj się co pół sekundy
           # WYKONANIE RUCHU: Jeśli mamy zaplanowaną ścieżkę, wykonujemy jeden krok co kilka klatek
            if planned_path:
                next_action = planned_path.pop(0) # Pobierz pierwszą akcję z listy
                agent.execute_action(next_action, global_state)

                # odświeżamy linię po każdym kroku agenta (żeby znikała z tyłu)
                path_coords = calculate_path_coords(agent.x, agent.y, agent.direction, planned_path)
                
                #Jeśli to był ostatni krok, zbierz śmieci
                if not planned_path:
                    cell = grid.cells[agent.y][agent.x]
                    # stoimy na domku ze śmieciami do zebrania
                    if cell and hasattr(cell, 'needs_collection'):
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

        # RYSOWANIE ŚCIEŻKI
        if len(path_coords) > 1:
            pygame.draw.lines(screen, (255, 0, 0), False, path_coords, 4)
            cel_x, cel_y = path_coords[-1]
            pygame.draw.circle(screen, (0, 0, 255), (cel_x, cel_y), 5)

        agent.draw(screen, assets, TILE_SIZE)

        draw_weather_effects(screen, global_state, weather_particles)

        # Rysowanie tła panelu (opcjonalnie, żeby oddzielić od mapy)
        pygame.draw.rect(screen, (255, 255, 255), (0, GRID_HEIGHT * TILE_SIZE, WINDOW_WIDTH, INFO_PANEL_HEIGHT))
        
        # Wyświetlenie informacji o stanie
        draw_infoPanel(screen, agent, global_state)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()