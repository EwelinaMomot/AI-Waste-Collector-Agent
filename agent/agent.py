from environment import house
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
                house.reset_house()

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
        distance = self.distance_to_station(station)
        required_fuel = distance * self.fuel_consumption_rate
        if self.current_fuel <= required_fuel + 5:
            return True
        return False

    def execute_action(self, action_name, global_state):
        """Łącznik: zamienia tekst z BFS na fizyczne działanie agenta"""
        if action_name == "obrót w lewo":
            self.turn_left()
        elif action_name == "obrót w prawo":
            self.turn_right()
        elif action_name == "przód":
            # Zużycie paliwa dzieje się tylko przy faktycznym ruchu
            self.move_forward()
            self.current_fuel -= self.fuel_consumption_rate
    
        # Po każdej akcji synchronizujemy wiedzę agenta
        self.sync_knowledge(global_state)

    def draw(self, screen, assets, tile_size):
        agent_img = assets["agent"]
        if self.facing_right:
            agent_img = pygame.transform.flip(agent_img, True, False)

        pos_x = self.x * tile_size
        pos_y = self.y * tile_size
        screen.blit(agent_img, (pos_x, pos_y))