import pygame
import random

class Agent:

    def __init__(self,start_x, start_y):
        self.x = start_x
        self.y = start_y
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

        # struktura slownikowa jako system ram (reprezentacja wiedzy)
        self.knowledge_base={
            #TODO: powiekszenie wiedzy agenta, po ustaleniu
        "resources": {
            "current_fuel": self.current_fuel ,
            "fuel_capacity": self.fuel_capacity,
            "trash_capacity": self.trash_capacity,
            "current_trash": sum(self.inventory.values()),
            "detailed_inventory": self.inventory.copy()
        },
        "environment": { 
                "weather": "sunny",
                "day_of_the_week": "monday",
                "fuel_cost_multiplier": 1.0 
        }}

    #Metoda synchronizująca stan faktyczny z bazą wiedzy agenta  
    def sync_knowledge(self):
        #TODO: do poszerzenia o sync z wieksza iloscia danych m.in czesc "environment" do polaczenia z danymi globalnymi
        self.knowledge_base["resources"]["current_fuel"] = self.current_fuel
        self.knowledge_base["resources"]["current_trash"] = sum(self.inventory.values())
        self.knowledge_base["resources"]["detailed_inventory"] = self.inventory.copy()

    # funkcja zbierania śmieci z domu
    def collect_trash(self, house):
        total_now = sum(self.inventory.values())
        
        if house.needs_collection and total_now + house.trash_weight <= self.trash_capacity:
            # dodajemy wagę do odpowiedniego typu w słowniku
            if house.trash_type in self.inventory:
                self.inventory[house.trash_type] += house.trash_weight
            else:
                self.inventory["zmieszane"] += house.trash_weight

            house.reset_house()
            self.sync_knowledge()

    # funcja wyładowania śmieciarki na wysypisku
    def empty_tank(self, dumpster):
        # TODO: dodać sprawdzanie, czy agent jest na wysypisku i czy w odpowiedniej strefie
        # wywalamy tylko te śmieci, które akceptuje dana strefa
        trash_to_unload = self.inventory[dumpster.zone_type]
        
        if trash_to_unload > 0:
            self.inventory[dumpster.zone_type] = 0
        self.sync_knowledge()

    def distance_to_station(self, station):
        # liczy odległość Manhatana do stacji
        dist_x = abs(self.x - station.x)
        dist_y = abs(self.y - station.y)
        return dist_x + dist_y
    
    def check_fuel_reserve(self, station):
        distance = self.distance_to_station(station)
        # 1 kratka = 1 jeden litr paliwa (dodajemy 5 na zapas)
        if self.current_fuel <= distance + 5:
            return True
        return False

    
    # FUNKCJE RUCHU - każda zmienia pozycję o 1 kratkę (mapa to macierz)
    def move_up(self):
        if self.y > 0: 
            self.y -= 1
            self.current_fuel-=self.fuel_consumption_rate
            self.sync_knowledge()

    def move_down(self, grid_height):
        if self.y < grid_height - 1: 
            self.y += 1
            self.current_fuel-=self.fuel_consumption_rate
            self.sync_knowledge()

    def move_left(self):
        if self.x > 0: 
            self.x -= 1
            self.current_fuel-=self.fuel_consumption_rate
            self.sync_knowledge()

    def move_right(self, grid_width):
        if self.x < grid_width - 1: 
            self.x += 1
            self.current_fuel-=self.fuel_consumption_rate
            self.sync_knowledge()

    def move_random(self,grid_width, grid_height):
        choice = random.choice(['up', 'down', 'left', 'right'])
        if choice == 'up':
            self.move_up()
        elif choice == 'down':
            self.move_down(grid_height)
        elif choice == 'left':
            self.move_left()
        elif choice == 'right':
            self.move_right(grid_width)

    def draw(self, screen, assets, tile_size):
        agent_img = assets['agent']  

        pos_x = self.x * tile_size
        pos_y = self.y * tile_size
        screen.blit(agent_img, (pos_x, pos_y))