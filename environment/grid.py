import random

from environment.dumpster import Dumpster
from environment.house import House
from environment.station import GasStation

ZONES = ["papier", "plastik_metal", "szklo", "bio", "zmieszane"]

HOUSE_ASSETS = {
    "papier": ("house_paper", "house_paper_empty"),
    "plastik_metal": ("house_plastic", "house_plastic_empty"),
    "szklo": ("house_glass", "house_glass_empty"),
    "bio": ("house_bio", "house_bio_empty"),
    "zmieszane": ("house_mixed", "house_mixed_empty"),
}

DUMP_ASSETS = {
    "papier": "dump_paper",
    "plastik_metal": "dump_plastic",
    "szklo": "dump_glass",
    "bio": "dump_bio",
    "zmieszane": "dump_mixed",
}


class Grid:
    #mapka jest w cells -  None to trawa, inaczej obiekt 

    def __init__(self, width, height, tile_size, global_state):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.cells = [[None for _ in range(width)] for _ in range(height)]
        self.generate(global_state)

    def generate(self, global_state):
        for y in range(self.height):
            for x in range(self.width):
                self.cells[y][x] = None

        for i, zone in enumerate(ZONES):
            self.cells[0][i] = Dumpster(i, 0, zone)

        sx = self.width - 1
        self.cells[0][sx] = GasStation(sx, 0)

        blocked = {(i, 0) for i in range(len(ZONES))}
        blocked.add((sx, 0))

        free = [(x, y) for y in range(self.height) for x in range(self.width) if (x, y) not in blocked]
        random.shuffle(free)
        n = random.randint(13, 17)
        for (x, y) in free[:n]:
            t = random.choice(ZONES)
            self.cells[y][x] = House(x, y, global_state, designated_trash_type=t)

    def iter_houses(self):
        for row in self.cells:
            for c in row:
                if isinstance(c, House):
                    yield c

    def draw(self, screen, assets):
        for y in range(self.height):
            for x in range(self.width):
                px = x * self.tile_size + 290
                py = y * self.tile_size
                cell = self.cells[y][x]

                if cell is None:
                    img = assets["grass"]
                elif isinstance(cell, GasStation):
                    img = assets["station"]
                elif isinstance(cell, Dumpster):
                    key = DUMP_ASSETS.get(cell.zone_type, "dump_mixed")
                    img = assets.get(key, assets["dump_mixed"])
                elif isinstance(cell, House):
                    kind = cell.trash_type or cell.designated_trash_type or "zmieszane"
                    full_k, empty_k = HOUSE_ASSETS.get(kind, HOUSE_ASSETS["zmieszane"])
                    if cell.needs_collection:
                        img = assets[full_k]
                    else:
                        img = assets[empty_k]
                else:
                    img = assets["grass"]

                screen.blit(img, (px, py))
