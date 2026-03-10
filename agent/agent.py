import pygame
import random

class Agent:

    def __init__(self,start_x, start_y):
        self.x = start_x
        self.y = start_y
    
    # FUNKCJE RUCHU - każda zmienia pozycję o 1 kratkę (mapa to macierz)
    def move_up(self):
        if self.y > 0: 
            self.y -= 1

    def move_down(self, grid_height):
        if self.y < grid_height - 1: 
            self.y += 1

    def move_left(self):
        if self.x > 0: 
            self.x -= 1

    def move_right(self, grid_width):
        if self.x < grid_width - 1: 
            self.x += 1

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