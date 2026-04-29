from environment import house
from environment.dumpster import Dumpster
from environment.house import House
from environment.station import GasStation
import pygame
import random
from environment.global_state import Weather
from search.state import N, E, S, W, DX, DY

class Agent:

    def __init__(self,start_x, start_y, initial_direction=E):
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
        self.fuel_capacity = 100
        self.current_fuel = 100
        self.fuel_consumption_rate = 1
        # Grafika domyślnie patrzy w lewo; przy jeździe w prawo — odbicie lustrzane.
        self.facing_right = False

        # struktura slownikowa jako system ram (reprezentacja wiedzy)
        self.knowledge_base={
            #TODO: powiekszenie wiedzy agenta, po ustaleniu
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


    #metody ruchu 
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
        
        if house.needs_collection and total_now + house.trash_weight <= self.trash_capacity:
            # dodajemy wagę do odpowiedniego typu w słowniku
            if house.trash_type in allowed_today:    
                if house.trash_type in self.inventory:
                    self.inventory[house.trash_type] += house.trash_weight
                else:
                    self.inventory["zmieszane"] += house.trash_weight
                house.needs_collection = False
                house.trash_weight = 0

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
            
            # Koszt ruchu = koszt pola * mnożnik zuzycia
            fuel_cost = cell_cost * self.fuel_consumption_rate
            
            # Wykonujemy ruch
            self.move_forward()
            
            # Zużywamy paliwo zgodnie z rzeczywistym kosztem pola
            self.current_fuel -= fuel_cost
    
        # Po każdej akcji synchronizujemy wiedzę agenta
        self.sync_knowledge(global_state)

    def draw(self, screen, assets, tile_size):
        agent_img = assets["agent"]
        if self.facing_right:
            agent_img = pygame.transform.flip(agent_img, True, False)

        pos_x = self.x * tile_size + 290
        pos_y = self.y * tile_size
        screen.blit(agent_img, (pos_x, pos_y))