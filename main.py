import os
import random
import sys

import pandas as pd
import pygame

from agent.agent import Agent  # tu strzelam nazewnictwo - Ewelina
from environment.global_state import GlobalState, Weather
from environment.grid import Grid  # tu strzelam nazewnictwo - Martyna
from ml.decision_tree import DecisionTreeID3
from ml.trash_classifier import TrashClassifier
from search.astar import astar
from search.planner_costs import ACTION_COSTS, CELL_ENTRY_COSTS
from search.problem import GridSearchProblem
from search.state import E, DX, DY

# do ustalenia:
GRID_WIDTH = 16
GRID_HEIGHT = 16
TILE_SIZE = 60
INFO_PANEL_WIDTH = 290
BOTTOM_STATUS_HEIGHT = 40
WINDOW_WIDTH = INFO_PANEL_WIDTH + (GRID_WIDTH * TILE_SIZE)
WINDOW_HEIGHT = (GRID_HEIGHT * TILE_SIZE) + BOTTOM_STATUS_HEIGHT
FPS = 30


def pick_target_heuristic(agent, global_state, grid, grid_width):
    station = grid.cells[0][grid_width - 1]
    if agent.check_fuel_reserve(station):
        return station, "MAŁO PALIWA! Rzucam wszystko i jadę na stację!"
    if agent.knowledge_base["resources"]["current_trash"] >= 75:
        biggest_trash_type = max(agent.inventory, key=agent.inventory.get)
        for y in range(grid.height):
            for x in range(grid.width):
                cell = grid.cells[y][x]
                if cell and hasattr(cell, "zone_type") and cell.zone_type == biggest_trash_type:
                    return (
                        cell,
                        f"ŚMIECIARKA PEŁNA! Jadę na wysypisko wyrzucić: {biggest_trash_type}",
                    )
        return None, "ŚMIECIARKA PEŁNA, ale nie znaleziono kontenera na mapie."
    allowed_today = global_state.get_allowed_types_today()
    valid_houses = [
        h
        for h in grid.iter_houses()
        if h.needs_collection and h.trash_type in allowed_today
        and not getattr(h, 'skipped_today', False)
    ]
    if valid_houses:
        target_node = min(
            valid_houses,
            key=lambda h: abs(h.x - agent.x) + abs(h.y - agent.y),
        )
        return target_node, f"Znalazłem najbliższy dom! Jadę po: {target_node.trash_type}"
    if (agent.x, agent.y) != (station.x, station.y):
        return station, "Koniec pracy na dziś! Wracam do bazy."
    return None, "Jestem w bazie. Wciśnij 'N', żeby zacząć nowy dzień."


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
    screen.blit(font.render(f"{int(fuel_percent * 100)}%", True, (0, 0, 0)), (x_start + 73 + bar_width + 10, y_current))
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

def generate_expert_decision(state_row):
    """
    funkcja do generowania decyzji dla dataset
    state_row = [Fuel, Trash, Weather, Day, Season, Dist_House, Dist_Station, Weight]
    Zwraca: "STATION", "DUMP" lub "HOUSE" (lub "BASE")
    """
    fuel, trash, weather, day, season, dist_h, dist_s, weight = state_row

    
    #stan krytycznny (Brak paliwa)
    
    if fuel == "CRITICAL":
        return "STATION"

   # Złożone przypadki dla niskiego paliwa 
    if fuel == "LOW":
        
        #Zabezpieczenie przed błędem logicznym: jeśli jesteśmy pełni
        # Priorytetem jest wysypisko (obsługiwane niżej), ale jeśli stacja jest daleko,
        # musimy zatankować najpierw, żeby nie utknąć w drodze na zrzut
        if trash == "FULL" and dist_s == "FAR":
            return "STATION"

        #bardzo złe warunki pogodowe 
        if weather == "SNOWY" or season == "WINTER":
            # Zimą na niskim paliwie ryzykujemy jazdę do domu tylko, jeśli:
            # stacja jest w zasięgu ,
            #  dom jest bardzo blisko 
            # i łup jest tego warty 
            if dist_s in ["NEAR", "MEDIUM"] and dist_h == "NEAR" and weight in ["MEDIUM", "LARGE"] and trash != "FULL":
                pass # Przechodzimy niżej, żeby pojechać do HOUSE
            else:
                return "STATION" #w każdym innym przypadku nie ryzykujemy
                
        # 3.złe warunki pogodowe 
        elif weather == "RAINY":
            # W deszczu spalanie jest wyższe, definitywnie odrzucamy dalekie trasy
            if dist_h == "FAR" or dist_s == "FAR":
                return "STATION"
                
            # Jeśli stacja i dom są blisko/średnio, oceniamy łup
            if dist_h in ["NEAR", "MEDIUM"] and weight == "LARGE":
                pass # Opłaca się zaryzykować dla dużych śmieci
            elif dist_h == "NEAR" and dist_s == "NEAR":
                pass # Krótki skok dozwolony rutynowo
            else:
                return "STATION"
                
        # 4. Dobra pogoda
        else:
            # Gdy świeci słońce, możemy pozwolić sobie na najwięcej z rezerwą paliwa
            if dist_s == "FAR":
                # Stacja jest daleko, więc musimy kierować się w jej stronę
                # Pozwalamy na zebranie śmieci tylko po drodze
                if dist_h == "NEAR" and weight in ["MEDIUM", "LARGE"]:
                    pass
                else:
                    return "STATION"
            else:
                # Stacja jest blisko/srednio - mamy duży bufor bezpieczeństwa
                # Rezygnujemy tylko z bezsensownych wyjazdów (daleki dom + małe śmieci)
                if dist_h == "FAR" and weight == "SMALL":
                    return "STATION"
                # W pozostałych przypadkach jedziemy
                pass

        #Jeśli kod przeszedł przez 'pass', to znaczy, że stan paliwa 
        # nas nie zablokował. Ostateczna decyzja (HOUSE czy DUMP) zostanie 
        # podjęta przez niższe priorytety w funkcji
    
    #brak zadan
    
    # Rozpatrujemy wszystkie dni tygodnia
    if dist_h == "NONE" or weight == "NONE":
        # Jeśli mamy jakiekolwiek śmieci pod koniec pracy, zrzucamy je
        if trash in ["LOW", "MEDIUM", "FULL"]:
            return "DUMP"
        # Jeśli jesteśmy puści, ale paliwo nie jest pełne - tankujemy na jutro
        elif fuel in ["LOW", "MEDIUM"]:
            return "STATION"
        # Jeśli wszystko jest idealne na koniec dnia
        else:
            return "STATION" # Wracamy do bazy (pole stacji to baza)

    
    #ilość śmieci na pace
    
    if trash == "FULL":
        return "DUMP"

    if trash == "MEDIUM":
        
        # 1. Cel z dużą wagą - Największe ryzyko przepełnienia
        if weight == "LARGE":
            # Jeśli jedziemy daleko, a cel jest ogromny, nie ryzykujemy pustego przelotu
            # Lepiej się opróżnić, a po duże śmieci wrócić z pustą paką (czyli status DUMP teraz, HOUSE w następnej turze)
            if dist_h == "FAR":
                return "DUMP"
                
            # Jeśli jest średnio daleko, a pogoda jest zła - też nie ryzykujemy
            # Przy dobrej pogodzie można zaryzykować objazd
            elif dist_h == "MEDIUM":
                if weather in ["RAINY", "SNOWY"]:
                    return "DUMP"
                else:
                    pass # Przechodzimy niżej, żeby ew. pojechać do HOUSE
                    
            # Jeśli dom z dużym łupem jest pod nosem to bierzemy w ciemno
            # Nawet jeśli coś zostanie na chodniku, to opłacało się podjechać te 3 metry
            elif dist_h == "NEAR":
                return "HOUSE"

        # 2. Cel ze średnią wagą
        elif weight == "MEDIUM":
            # Średni cel przy średnim baku zazwyczaj się zmieści, ale unikamy
            # wypraw na drugi koniec mapy zimą
            if dist_h == "FAR" and season in ["AUTUMN", "WINTER"]:
                 return "DUMP" # Wczesny powrót zrzutu, bezpieczeństwo przede wszystkim
            else:
                 pass # Standardowo jedziemy po odbiór

        # 3. Cel z małą wagą 
        elif weight == "SMALL":
             # Zbieranie małych śmieci, gdy jesteśmy do połowy pełni, ma sens tylko po drodze
             if dist_h == "FAR":
                 # Jeśli mamy jechać na drugi koniec mapy po worek śmieci 5kg, a mamy już 70% paki:
                 # Lepiej zrzucić śmieci, żeby być gotowym na wieksze zlecenia
                 return "DUMP"
             elif dist_h == "MEDIUM" and weather != "SUNNY":
                 # W złą pogodę nawet średni dystans po mały worek nie opłaca się ze średnim statusem paki
                 return "DUMP"
             else:
                 pass # W promieniu NEAR lub dobrej pogodzie bierzemy.
                 
        #Podobnie jak przy paliwie, blok pass oznacza, że śmieciarka 
        # zaakceptowała ryzyko i przechodzi niżej 
        # który zatwierdzi ostateczną podróż (HOUSE)

    
    #normalna praca
    
    # Kiedy Fuel jest MEDIUM/HIGH, a Trash EMPTY/LOW
    

    # Ocena opłacalności wyjazdu (waga vs dystans)
    if weight == "LARGE":
        return "HOUSE" # Zawsze bierzemy duży łup gdy mamy miejsce i paliwo

    if weight == "MEDIUM":
        # Jesienią/Zimą unikamy dalekich tras, jeśli mamy tylko średni cel i średnie paliwo
        if dist_h == "FAR" and season in ["AUTUMN", "WINTER"] and fuel == "MEDIUM":
            return "STATION"
        return "HOUSE"

    if weight == "SMALL":
        # Jazda bardzo daleko po malutkie śmieci się nie opłaca
        if dist_h == "FAR":
            
            if fuel == "MEDIUM": return "STATION"
            return "HOUSE" # Skrajny przypadek: bak pełny, śmieciarka pusta, wiec jedziemy
        
        # Blisko lub średnio - jedziemy
        if dist_h in ["NEAR", "MEDIUM"]:
            return "HOUSE"

    # Fallback awaryjny 
    return "HOUSE"

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


def show_trash_popup(screen, image_path, nn_decision, matches, clock):
    """
    Wyświetla popup ze zdjęciem śmieci i decyzją sieci neuronowej.
    Zamyka się po naciśnięciu dowolnego klawisza lub po 3 sekundach.
    """
    background = screen.copy()

    trash_img = pygame.image.load(image_path)
    trash_img = pygame.transform.scale(trash_img, (250, 250))

    popup_w, popup_h = 400, 440
    popup_x = (WINDOW_WIDTH - popup_w) // 2
    popup_y = (WINDOW_HEIGHT - popup_h) // 2

    font_title = pygame.font.SysFont('Consolas', 20, bold=True)
    font_result = pygame.font.SysFont('Consolas', 16, bold=True)
    font_hint = pygame.font.SysFont('Consolas', 14)

    start_time = pygame.time.get_ticks()
    popup_duration = 3000

    while True:
        elapsed = pygame.time.get_ticks() - start_time
        if elapsed >= popup_duration:
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                return

        screen.blit(background, (0, 0))

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (255, 255, 255), (popup_x, popup_y, popup_w, popup_h), border_radius=12)
        pygame.draw.rect(screen, (60, 60, 60), (popup_x, popup_y, popup_w, popup_h), 3, border_radius=12)

        title = font_title.render("INSPEKCJA ŚMIECI", True, (0, 0, 0))
        screen.blit(title, (popup_x + (popup_w - title.get_width()) // 2, popup_y + 15))

        img_x = popup_x + (popup_w - 250) // 2
        screen.blit(trash_img, (img_x, popup_y + 50))

        result_text = f"Siec rozpoznala: {nn_decision}"
        result = font_result.render(result_text, True, (0, 0, 0))
        screen.blit(result, (popup_x + (popup_w - result.get_width()) // 2, popup_y + 315))

        if matches:
            status_text = "ZABIERAM"
            status_color = (0, 150, 0)
        else:
            status_text = "ZLE SMIECI - NIE ZABIERAM"
            status_color = (220, 30, 30)

        status = font_result.render(status_text, True, status_color)
        screen.blit(status, (popup_x + (popup_w - status.get_width()) // 2, popup_y + 350))

        remaining = max(0, popup_duration - elapsed) // 1000 + 1
        hint = font_hint.render(f"Klawisz lub {remaining}s...", True, (150, 150, 150))
        screen.blit(hint, (popup_x + (popup_w - hint.get_width()) // 2, popup_y + popup_h - 35))

        pygame.display.flip()
        clock.tick(FPS)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Inteligentna Śmieciarka")
    clock = pygame.time.Clock()

    assets = load_assets()

    global_state = GlobalState()

    grid = Grid(GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, global_state)
    agent = Agent(start_x=0, start_y=0, initial_direction=E)

    decision_model = DecisionTreeID3()
    train_df = pd.read_csv("data/garbage_truck_data.csv", sep=";")
    decision_model.train(train_df, target_column="Decision")
    os.makedirs("output", exist_ok=True)
    decision_model.save_tree_preview("output/decision_tree.txt")
    decision_model.export_graphviz_dot("output/decision_tree.dot")
    decision_model.print_tree()
    agent.attach_decision_tree(decision_model)

    # Inicjalizacja klasyfikatora sieci neuronowej (CNN)
    trash_classifier = TrashClassifier()
    agent.attach_classifier(trash_classifier)

    planned_path = []
    path_coords = []   # tu będziemy trzymać piksele naszej linii
    weather_particles = [] # tu trzymamy płatki śniegu i deszcz
    current_target = None # Współrzędne celu, do którego jedziemy

    running = True
    frame_count = 0  

    #zmiana na true powoduje automatyczną zmianę celu i dnia do generowania danych
    datasetCreationMode = False
    
    AUTO_SPACE_EVENT = pygame.USEREVENT + 1
    AUTO_N_EVENT = pygame.USEREVENT + 2
    if datasetCreationMode:
        training_data = []  
        pygame.time.set_timer(AUTO_SPACE_EVENT, 100) # Uruchamiaj co 1 sekundę
        pygame.time.set_timer(AUTO_N_EVENT, 2000)     # Uruchamiaj co 4 sekundy
        
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # zmiana dnia po wciśnięciu klawisza 'N'
            elif event.type in (AUTO_N_EVENT ,pygame.KEYDOWN,AUTO_SPACE_EVENT):
                if (event.type==pygame.KEYDOWN and event.key == pygame.K_n) or event.type==AUTO_N_EVENT:
                    global_state.next_day()
                    for h in grid.iter_houses():
                        h.generate_trash(global_state)
                        
                    agent.sync_knowledge(global_state)

            # zmiana celu: Po wciśnięciu SPACJI śmieciarka wybiera nowy cel i szuka do niego drogi

                if (event.type==pygame.KEYDOWN and event.key == pygame.K_SPACE) or  event.type==AUTO_SPACE_EVENT:
                    print("Spacja naciśnięta - wybieram cel...")
                    if datasetCreationMode:
                        target_node, msg = pick_target_heuristic(
                            agent, global_state, grid, GRID_WIDTH
                        )
                    else:
                        target_node, msg = agent.select_target_using_tree(
                            global_state, grid
                        )
                    print(msg)
                    agent.last_status = msg

                    if target_node:

                        if datasetCreationMode:
                                #Pobierz zdyskretyzowany stan od agenta
                                state_row = agent.get_discretized_state(global_state, grid)
                                
                                decision = generate_expert_decision(state_row)
        
                                full_entry = state_row + [decision]
                                training_data.append(full_entry)
                                                    

                                # 4. Automatyczny zapis do pliku po zebraniu 500 wierszy(większa ilość aby potem dobrać równe ilości ze wzgl na decyzję)
                                if len(training_data) == 500:
                                    import csv
                                    with open('data/garbage_truck_data_notbalanced.csv', 'w', newline='', encoding='utf-8') as f:
                                        writer = csv.writer(f, delimiter=';')
                                        
                                        writer.writerow(["Fuel", "Trash", "Weather", "Day", "Season", "Dist_House", "Dist_Station", "Weight", "Decision"])
                                        writer.writerows(training_data)
                                    print("!!! Zbiór 200 przykładów został zapisany do data/garbage_truck_data_notbalanced.csv !!!")
                                    pygame.time.set_timer(AUTO_SPACE_EVENT, 0)
                                    pygame.time.set_timer(AUTO_N_EVENT, 0)


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
                        # Inspekcja śmieci siecią neuronową
                        if agent.trash_classifier and cell.needs_collection:
                            image_path = agent.trash_classifier.get_random_image(cell.trash_type)
                            nn_decision = agent.trash_classifier.classify(image_path)
                            matches = (nn_decision == cell.trash_type)

                            show_trash_popup(screen, image_path, nn_decision, matches, clock)

                            if matches:
                                agent.last_status = f"Zebrano: {cell.trash_type}, {cell.trash_weight} kg (siec: {nn_decision})"
                                agent.collect_trash(cell, global_state)
                                print(f"\nZebrano smieci! Zapelnienie smieciarki: {agent.knowledge_base['resources']['current_trash']} kg")
                            else:
                                agent.last_status = f"ZLE SMIECI! Siec: {nn_decision}, oczekiwano: {cell.trash_type}"
                                cell.skipped_today = True
                                print(f"\nOdmowa odbioru! Siec wykryla: {nn_decision}, dom ma: {cell.trash_type}")
                        else:
                            agent.last_status = f"Zebrano: {cell.trash_type}, {cell.trash_weight} kg"
                            agent.collect_trash(cell, global_state)
                            print(f"\nZebrano smieci! Zapelnienie smieciarki: {agent.knowledge_base['resources']['current_trash']} kg")
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