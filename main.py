import pygame
import sys

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

# ladowanie ikonek - jak zdecydujemy sie na nie, to trzeba wrzucac do folderu assets i tu implementowac loading
def load_assets():
    assets = {}

    raw_tile = pygame.image.load('assets/pole.png')
    raw_agent = pygame.image.load('assets/garbage_truck.png')

    assets['empty_tile'] = pygame.transform.scale(raw_tile, (TILE_SIZE, TILE_SIZE))
    assets['agent'] = pygame.transform.scale(raw_agent, (TILE_SIZE, TILE_SIZE))

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

    grid = Grid(width=GRID_WIDTH, height=GRID_HEIGHT, tile_size=TILE_SIZE)
    agent = Agent(start_x=0, start_y=0) 

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
       
        frame_count += 1
        if frame_count >= 15:  # Ruszaj się co pół sekundy
            agent.move_random(GRID_WIDTH, GRID_HEIGHT, global_state)
            frame_count = 0  
            

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