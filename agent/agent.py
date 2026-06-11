from environment import house
from environment.dumpster import Dumpster
from environment.house import House
from environment.station import GasStation
import pygame
import random
from environment.global_state import Weather
from search.state import N, E, S, W, DX, DY
from search.problem import GridSearchProblem
from search.astar import astar
from search.planner_costs import ACTION_COSTS, CELL_ENTRY_COSTS


TREE_STATE_KEYS = [
    "Fuel",
    "Trash",
    "Weather",
    "Day",
    "Season",
    "Dist_House",
    "Dist_Station",
    "Weight",
]


class Agent:

    def __init__(self, start_x, start_y, initial_direction=E):
        self.x = start_x
        self.y = start_y
        self.direction = initial_direction  # 0=N, 1=E, 2=S, 3=W
        self.trash_capacity = 100
        # SŁOWNIK: kluczem jest typ, wartością waga
        self.inventory = {
            "papier": 0,
            "plastik_metal": 0,
            "szklo": 0,
            "bio": 0,
            "zmieszane": 0
        }
        self.fuel_capacity = 150
        self.current_fuel = 150
        self.fuel_consumption_rate = 1
        # Grafika domyślnie patrzy w lewo; przy jeździe w prawo — odbicie lustrzane.
        self.facing_right = False

        # struktura slownikowa jako system ram (reprezentacja wiedzy)
        self.knowledge_base={
        "resources": {
            "current_fuel": self.current_fuel ,
            "fuel_capacity": self.fuel_capacity,
            "trash_capacity": self.trash_capacity,
            "current_trash": sum(self.inventory.values()),
            "detailed_inventory": self.inventory.copy(),
        },
        "agent_info":{
            "position": (self.x, self.y),
            "direction": self.get_direction_name()
        },

        "environment": { 
                "weather": "SUNNY",
                "day_of_the_week": "Monday",
                "fuel_cost_multiplier": 1.0 
        }}
        self.last_status = "System gotowy"
        self.decision_tree = None
        self.trash_classifier = None  # klasyfikator sieci neuronowej (CNN)

    def attach_decision_tree(self, tree):
        self.decision_tree = tree

    def attach_classifier(self, classifier):
        """Podpina klasyfikator sieci neuronowej do agenta."""
        self.trash_classifier = classifier

    def get_tree_state_dict(self, global_state, grid):
        row = self.get_discretized_state(global_state, grid)
        return dict(zip(TREE_STATE_KEYS, row))

    _FUEL_ROUNDTRIP_SAFETY_MARGIN = 1.18

    def _path_actions_to(self, grid, start_xyd, goal_x, goal_y):
        problem = GridSearchProblem(
            grid,
            goal_x,
            goal_y,
            action_costs=ACTION_COSTS,
            cell_entry_costs=CELL_ENTRY_COSTS,
        )
        path, _ = astar(start_xyd, (goal_x, goal_y), problem)
        return path

    def _fuel_and_pose_after_actions(self, grid, sx, sy, sd, actions, trash_kg):
        x, y, d = sx, sy, sd
        rate = self.fuel_consumption_rate
        wm = 1.0 + (trash_kg / self.trash_capacity) * 0.5
        fuel = 0.0
        for action in actions:
            if action == "obrót w lewo":
                fuel += 1 * rate
                d = (d - 1) % 4
            elif action == "obrót w prawo":
                fuel += 1 * rate
                d = (d + 1) % 4
            elif action == "przód":
                nx = x + DX[d]
                ny = y + DY[d]
                cell_cost = self.get_cell_entry_cost(grid, nx, ny)
                fuel += cell_cost * rate * wm
                x, y = nx, ny
        return fuel, x, y, d

    def _fuel_ok_to_primary_then_station(self, grid, primary_cell):
        station = grid.cells[0][grid.width - 1]
        trash0 = sum(self.inventory.values())
        start = (self.x, self.y, self.direction)

        path1 = self._path_actions_to(grid, start, primary_cell.x, primary_cell.y)
        if not path1:
            return False

        fuel1, ax, ay, ad = self._fuel_and_pose_after_actions(
            grid, self.x, self.y, self.direction, path1, trash0
        )

        if isinstance(primary_cell, House):
            space = max(0, self.trash_capacity - trash0)
            take = min(getattr(primary_cell, "trash_weight", 0), space)
            trash1 = min(self.trash_capacity, trash0 + take)
        elif isinstance(primary_cell, Dumpster):
            unload = self.inventory.get(primary_cell.zone_type, 0)
            trash1 = max(0.0, trash0 - unload)
        else:
            trash1 = trash0

        path2 = self._path_actions_to(grid, (ax, ay, ad), station.x, station.y)
        if not path2:
            return False

        fuel2, _, _, _ = self._fuel_and_pose_after_actions(
            grid, ax, ay, ad, path2, trash1
        )

        need = (fuel1 + fuel2) * self._FUEL_ROUNDTRIP_SAFETY_MARGIN
        return self.current_fuel >= need

    def select_target_using_tree(self, global_state, grid):
        self.sync_knowledge(global_state)
        if self.decision_tree is None:
            return None, "Brak podpiętego drzewa decyzyjnego."

        state_dict = self.get_tree_state_dict(global_state, grid)
        decision = self.decision_tree.predict(state_dict)
        station = grid.cells[0][grid.width - 1]

        print(f"Drzewo ({decision}): stan={state_dict}")

        if decision == "STATION":
            return station, "Mało paliwa -> jadę na stację."

        if decision == "DUMP":
            total = sum(self.inventory.values())
            if total <= 0:
                return station, "Brak śmieci do zrzutu -> jadę na stację."
            biggest_trash_type = max(self.inventory, key=self.inventory.get)
            target_node = None
            for y in range(grid.height):
                for x in range(grid.width):
                    cell = grid.cells[y][x]
                    if cell and hasattr(cell, "zone_type") and cell.zone_type == biggest_trash_type:
                        target_node = cell
                        break
                if target_node:
                    break
            if target_node:
                if not self._fuel_ok_to_primary_then_station(grid, target_node):
                    return (
                        station,
                        f"Zrzut: {biggest_trash_type} [brak paliwa -> stacja]",
                    )
                return target_node, f"Zrzut: {biggest_trash_type}"
            return station, "Brak strefy na mapie -> jadę na stację."

        if decision == "HOUSE":
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
                    key=lambda h: abs(h.x - self.x) + abs(h.y - self.y),
                )
                if not self._fuel_ok_to_primary_then_station(grid, target_node):
                    return (
                        station,
                        f"Odbiór: {target_node.trash_type} [brak paliwa -> stacja]",
                    )
                return target_node, f"Jadę po: {target_node.trash_type}"
            if (self.x, self.y) != (station.x, station.y):
                return station, "Brak domów z odbiorem -> wracam do bazy."
            return None, "Jestem w bazie (N - nowy dzien)."

        return None, f"Nieznana decyzja drzewa: {decision}"

    # metody ruchu 
    def turn_left(self):
        self.direction = (self.direction - 1) % 4

    def turn_right(self):
        self.direction = (self.direction + 1) % 4

    def move_forward(self):
        self.x += DX[self.direction]
        self.y += DY[self.direction]
        # Aktualizacja wizualna
        if self.direction == E:
            self.facing_right = True
        elif self.direction == W: # domyślnie ustawiona w prawo przy jeździe góra/dół
            self.facing_right = False

    def get_direction_name(self):
        # zamienia liczby na litery np: "0" na "N"
        names = {N: "N", E: "E", S: "S", W: "W"}
        return names[self.direction]

    #Metoda synchronizująca stan faktyczny z bazą wiedzy agenta  
    def sync_knowledge(self, global_state):
        #TODO: do poszerzenia o sync z wieksza iloscia danych m.in czesc "environment" do polaczenia z danymi globalnymi
        self.knowledge_base["resources"]["current_fuel"] = self.current_fuel
        self.knowledge_base["resources"]["current_trash"] = sum(self.inventory.values())
        self.knowledge_base["resources"]["detailed_inventory"] = self.inventory.copy()

        #dane o pozycji
        self.knowledge_base["agent_info"]["position"] = (self.x, self.y)
        self.knowledge_base["agent_info"]["direction"] = self.get_direction_name()

        # pobieranie pogody i dnia
        self.knowledge_base["environment"]["weather"] = global_state.current_weather.name
        self.knowledge_base["environment"]["day_of_the_week"] = global_state.current_day

        # obliczanie zużycia paliwa na podstawie pogody
        if global_state.current_weather == Weather.SUNNY:
            mult = 1.0
        elif global_state.current_weather == Weather.RAINY:
            mult = 1.5
        elif global_state.current_weather == Weather.SNOWY:
            mult = 2.0

        self.knowledge_base["environment"]["fuel_cost_multiplier"] = mult
        self.fuel_consumption_rate = mult

        # zabezpieczenie, żeby paliwo nie było ujemne
        if self.current_fuel < 0:
            self.current_fuel = 0
        self.knowledge_base["resources"]["current_fuel"] = self.current_fuel

    # funkcja zbierania śmieci z domu
    def collect_trash(self, house, global_state):
        total_now = sum(self.inventory.values())
        allowed_today = global_state.get_allowed_types_today()
        
        if house.needs_collection and house.trash_type in allowed_today:
            space_left = self.trash_capacity - total_now
            
            if space_left > 0:
                # Agent bierze tyle, ile wlezie. Albo wszystko, albo to, co się zmieści.
                amount_to_take = min(house.trash_weight, space_left)
                
                # Dodajemy do ekwipunku
                if house.trash_type in self.inventory:
                    self.inventory[house.trash_type] += amount_to_take
                else:
                    self.inventory["zmieszane"] += amount_to_take
                
                # Aktualizujemy wagę pod domkiem
                house.trash_weight -= amount_to_take
                
                if house.trash_weight <= 0:
                    house.needs_collection = False
                    house.trash_weight = 0
                    print("Zabrano całe śmieci z posesji.")
                else:
                    print(f"Śmieciarka się przepełniła! Zostawiono {house.trash_weight}kg pod domem.")

        self.sync_knowledge(global_state)

    # funcja wyładowania śmieciarki na wysypisku
    def empty_tank(self, dumpster, global_state):
        # TODO: dodać sprawdzanie, czy agent jest na wysypisku i czy w odpowiedniej strefie
        # wywalamy tylko te śmieci, które akceptuje dana strefa
        trash_to_unload = self.inventory[dumpster.zone_type]
        
        if trash_to_unload > 0:
            self.inventory[dumpster.zone_type] = 0
        self.sync_knowledge(global_state)

    def distance_to_station(self, station):
        # liczy odległość Manhatana do stacji
        dist_x = abs(self.x - station.x)
        dist_y = abs(self.y - station.y)
        return dist_x + dist_y
    
    def check_fuel_reserve(self, station):
        # 1. Czysta heurystyka (Odległość Manhattana)
        # Zakłada idealną, najkrótszą drogę bez żadnych przeszkód
        base_heuristic_distance = self.distance_to_station(station)
        
        # 2. Szacowanie utrudnień (pesymistyczny bufor)
        # Agent wie, że na pewno będzie musiał się obracać (każdy obrót to koszt 1)
        estimated_turns = 2 
        # Dodajemy bufor na wypadek, gdyby najkrótsza trasa prowadziła przez dom (koszt 10) lub wysypisko (5)
        obstacle_buffer = 10 
        
        # 3. Całkowity szacowany koszt
        total_estimated_cost = base_heuristic_distance + estimated_turns + obstacle_buffer
        
        # 4. Mnożymy przez utrudnienia pogodowe
        required_fuel = total_estimated_cost * self.fuel_consumption_rate
        
        # Jeśli paliwo spadnie do tego poziomu (lub niżej), rzucamy wszystko i jedziemy na stację
        if self.current_fuel <= required_fuel:
            return True
        return False

    def get_cell_entry_cost(self, grid, x, y):
        """Zwraca koszt wejścia na dane pole (z siatki gry)"""
        cell = grid.cells[y][x]
        if cell is None:

            return 1  # trawa
        if isinstance(cell, House):
            return 10  # dom
        if isinstance(cell, Dumpster):
            return 5  # wysypisko
        if isinstance(cell, GasStation):
            return 5  # stacja paliwa
        return 1

    def execute_action(self, action_name, global_state, grid):
        """
        Łącznik: zamienia tekst z A* na fizyczne działanie agenta.
      
        """
        if action_name == "obrót w lewo":
            self.turn_left()
            self.current_fuel -= 1 * self.fuel_consumption_rate
        elif action_name == "obrót w prawo":
            self.turn_right()
            self.current_fuel -= 1 * self.fuel_consumption_rate
        elif action_name == "przód":
            # Obliczamy koszty ruchu PRZED wykonaniem ruchu
            nx = self.x + DX[self.direction]
            ny = self.y + DY[self.direction]
            
            # Pobieramy koszt pola, na które się ruszamy
            cell_cost = self.get_cell_entry_cost(grid, nx, ny)
            
            # Liczymy współczynnik ciężaru (śmieci)
            current_weight = self.knowledge_base["resources"]["current_trash"]
            weight_multiplier = 1.0 + (current_weight / self.trash_capacity) * 0.5

            # Koszt uwzględnia teren, pogodę oraz ciężar samej śmieciarki
            fuel_cost = cell_cost * self.fuel_consumption_rate * weight_multiplier
            
            # Wykonujemy ruch
            self.move_forward()
            
            # Zużywamy paliwo zgodnie z rzeczywistym kosztem pola
            self.current_fuel -= fuel_cost

            
                
        # Po każdej akcji synchronizujemy wiedzę agenta
        self.sync_knowledge(global_state)

    def get_discretized_state(self, global_state, grid):
        # Generuje stan kategoryczny dla zbioru uczącego / drzewa

        # paliwo
        fuel_pct = (self.current_fuel / self.fuel_capacity) * 100
        if fuel_pct < 25:
            fuel_cat = "CRITICAL"
        elif fuel_pct <= 50:
            fuel_cat = "LOW"
        elif fuel_pct <= 75:
            fuel_cat = "MEDIUM"
        else:
            fuel_cat = "HIGH"

        # zapełnienie śmieciarki
        current_trash = sum(self.inventory.values())
        trash_pct = (current_trash / self.trash_capacity) * 100
        if trash_pct <= 25:
            trash_cat = "EMPTY"
        elif trash_pct <= 50:
            trash_cat = "LOW"
        elif trash_pct <= 75:
            trash_cat = "MEDIUM"
        else:
            trash_cat = "FULL"

        # pogoda
        weather_cat = global_state.current_weather.name

        # dzień tygodnia
        day_cat = global_state.current_day

        # pora roku
        season_cat = global_state.current_season.name

        #dystans
        station_node = grid.cells[0][grid.width - 1]
        station_problem = GridSearchProblem(
            grid,
            station_node.x,
            station_node.y,
            action_costs=ACTION_COSTS,
            cell_entry_costs=CELL_ENTRY_COSTS,
        )
        station_path, _ = astar((self.x, self.y, self.direction), (station_node.x, station_node.y), station_problem)
        
        # Długość ścieżki A* (lub bardzo dużo, jeśli brak ścieżki)
        dist_to_station = len(station_path) if station_path else 999 

        if dist_to_station <= 5: dist_station_cat = "NEAR"
        elif dist_to_station <= 15: dist_station_cat = "MEDIUM" # A* ma dłuższe ścieżki przez obroty, można zwiększyć limit
        else: dist_station_cat = "FAR"


        #dystans do najblizszego domu
        nearest_house = None
        min_path_cost = float('inf')
        allowed_today = global_state.get_allowed_types_today()

        for house in grid.iter_houses():
            if house.needs_collection and house.trash_type in allowed_today:
                
                problem = GridSearchProblem(
                    grid,
                    house.x,
                    house.y,
                    action_costs=ACTION_COSTS,
                    cell_entry_costs=CELL_ENTRY_COSTS,
                )
                path, _ = astar((self.x, self.y, self.direction), (house.x, house.y), problem)
                
                if path:
                    cost = len(path)
                    if cost < min_path_cost:
                        min_path_cost = cost
                        nearest_house = house

        
        if nearest_house and min_path_cost != float('inf'):
            if min_path_cost <= 5:
                dist_house_cat = "NEAR"
            elif min_path_cost <= 15: 
                dist_house_cat = "MEDIUM"
            else:
                dist_house_cat = "FAR"
            
            if nearest_house.trash_weight < 10:
                weight_cat = "SMALL"
            elif nearest_house.trash_weight <= 20:
                weight_cat = "MEDIUM"
            else:
                weight_cat = "LARGE"
        else:
            dist_house_cat = "NONE"
            weight_cat = "NONE"

        return [
            fuel_cat, trash_cat, weather_cat, day_cat, 
            season_cat, dist_house_cat, dist_station_cat, weight_cat
        ]
    
    def draw(self, screen, assets, tile_size):
        agent_img = assets["agent"]
        if self.facing_right:
            agent_img = pygame.transform.flip(agent_img, True, False)

        pos_x = self.x * tile_size + 290
        pos_y = self.y * tile_size
        screen.blit(agent_img, (pos_x, pos_y))