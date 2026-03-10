import pygame
import sys

from environment.grid import Grid # tu strzelam nazewnictwo - Martyna
from agent.agent import Agent # tu strzelam nazewnictwo - Ewelina

# do ustalenia:
GRID_WIDTH = 16
GRID_HEIGHT = 16
TILE_SIZE = 50
WINDOW_WIDTH = GRID_WIDTH * TILE_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * TILE_SIZE
FPS = 30

# ladowanie ikonek - jak zdecydujemy sie na nie, to trzeba wrzucac do folderu assets i tu implementowac loading
def load_assets():
    assets = {}

    raw_tile = pygame.image.load('assets/pole.png')
    raw_agent = pygame.image.load('assets/garbage_truck.png')

    assets['empty_tile'] = pygame.transform.scale(raw_tile, (TILE_SIZE, TILE_SIZE))
    assets['agent'] = pygame.transform.scale(raw_agent, (TILE_SIZE, TILE_SIZE))

    return assets


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Inteligentna Śmieciarka")
    clock = pygame.time.Clock()

    assets = load_assets()

    grid = Grid(width=GRID_WIDTH, height=GRID_HEIGHT, tile_size=TILE_SIZE)
    agent = Agent(start_x=0, start_y=0) 

    running = True
    frame_count = 0  

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
       
        frame_count += 1
        if frame_count >= 15:  # Ruszaj się co pół sekundy
            agent.move_random(GRID_WIDTH, GRID_HEIGHT)
            frame_count = 0  
            

        screen.fill((255, 255, 255))

        grid.draw(screen, assets)
        agent.draw(screen, assets, TILE_SIZE)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()