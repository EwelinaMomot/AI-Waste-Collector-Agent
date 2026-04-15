import pygame
import sys
from search.state import E
from search.bfs import bfs
from search.problem import GridSearchProblem
from environment.global_state import GlobalState
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
    fuel_text = f"Paliwo: {agent.current_fuel }%"
    current_trash = sum(agent.inventory.values())
    trash_text = f"Pojemność: {current_trash}/{agent.trash_capacity}"
    
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


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Inteligentna Śmieciarka")
    clock = pygame.time.Clock()

    assets = load_assets()

    global_state = GlobalState()

    grid = Grid(GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, global_state)
    agent = Agent(start_x=0, start_y=0, initial_direction=E)

    planned_path = []  # Tu będziemy przechowywać listę akcji z BFS
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

                # zmiana celu: Po wciśnięciu SPACJI śmieciarka wybiera nowy cel i szuka do niego drogi
                if event.key == pygame.K_SPACE:
                    # Przykładowy cel: szukamy domu, który potrzebuje odbioru śmieci
                    target_house = None
                    for h in grid.iter_houses():
                        if h.needs_collection: # Sprawdzamy, czy dom ma śmieci
                            target_house = h
                            break
                    
                    if target_house:
                        current_target = (target_house.x, target_house.y)
                        # Tworzymy problem wyszukiwania
                        problem = GridSearchProblem(grid, target_house.x, target_house.y)
                        planned_path = bfs((agent.x, agent.y, agent.direction), current_target, problem)
                        print(f"Zaplanowana trasa: {planned_path}")
       
        frame_count += 1
        if frame_count >= 15:  # Ruszaj się co pół sekundy
           # WYKONANIE RUCHU: Jeśli mamy zaplanowaną ścieżkę, wykonujemy jeden krok co kilka klatek
            if planned_path:
                next_action = planned_path.pop(0) # Pobierz pierwszą akcję z listy
                agent.execute_action(next_action, global_state) 
                
                #Jeśli to był ostatni krok, zbierz śmieci
                if not planned_path:
                    cell = grid.cells[agent.y][agent.x]
                    if cell and hasattr(cell, 'needs_collection'):
                        agent.collect_trash(cell, global_state)
                        print(f"Zebrano śmieci! Stan baku: {sum(agent.inventory.values())}")

        screen.fill((255, 255, 255))

        grid.draw(screen, assets)
        agent.draw(screen, assets, TILE_SIZE)

        # Rysowanie tła panelu (opcjonalnie, żeby oddzielić od mapy)
        pygame.draw.rect(screen, (200, 200, 200), (0, GRID_HEIGHT * TILE_SIZE, WINDOW_WIDTH, INFO_PANEL_HEIGHT))
        
        # Wyświetlenie informacji o stanie
        draw_infoPanel(screen, agent, global_state)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()