import pygame
import os

GRASS = 0
## testowe oznaczenia, zobaczymy jak bedziemy mapke robic:
#ROAD = 1
#HOUSE = 2
#HOUSE_PLASTIC = 3


class Grid:
    def __init__(self, width, height, tile_size):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.map = []
        self.load_map()
        
        
    def load_map(self, filename="map.txt"):
        filepath = os.path.join("assets", filename)
        with open(filepath, 'r') as file:
            lines = file.readlines()
            
            for line in lines:
                clean_line = line.strip() 
                    
                row = []
                for char in clean_line:
                    row.append(int(char))
                    
                self.map.append(row)



    def draw(self, screen, assets):
        for y in range(self.height):
            for x in range(self.width):
                pos_x = x * self.tile_size
                pos_y = y * self.tile_size
                
                tile_type = self.map[y][x]
                # tutaj narazie sprawdzam tylko dla grass (0). jak umówimy sie na pola to dodam obsluge innych
                if tile_type == GRASS:
                    tile_img = assets['empty_tile']
                
                screen.blit(tile_img, (pos_x, pos_y))
    
    
                
