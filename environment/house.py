import random
from environment.global_state import Season

class House:
    def __init__(self, grid_x, grid_y, global_state, designated_trash_type=None):
        self.x = grid_x
        self.y = grid_y
        self.possible_types = ["papier", "plastik_metal", "szklo", "bio", "zmieszane"]
        self.designated_trash_type = designated_trash_type
        self.skipped_today = False  # flaga: agent odmówił odbioru (złe śmieci wg sieci neuronowej)

        self.generate_trash(global_state)  # generujemy śmieci uwzględniając porę roku z global_state

    def generate_trash(self, global_state):
        self.skipped_today = False  # reset flagi na nowy dzień
        szansa_na_smieci = random.randint(70, 100)
        self.needs_collection = random.randint(1, 100) <= szansa_na_smieci

        if self.needs_collection:
            # wpływ pory roku na wage i typ śmieci
            # Lato
            if global_state.current_season == Season.SUMMER:
                self.trash_weight = random.randint(5, 15)
                types_for_season = self.possible_types + ["bio", "bio"]  # latem więcej odpadów bio
            
            # Zima
            elif global_state.current_season == Season.WINTER:
                self.trash_weight = random.randint(10, 25)
                types_for_season = self.possible_types + ["zmieszane", "zmieszane"]
            
            # Jesień
            elif global_state.current_season == Season.AUTUMN:
                self.trash_weight = random.randint(5, 20)
                types_for_season = self.possible_types + ["bio"]

            # Wiosna
            else:
                self.trash_weight = random.randint(1, 10)
                types_for_season = self.possible_types

            allowed_today = global_state.get_allowed_types_today()
            
            if allowed_today:
                # 90% szans, że obywatele sprawdzili harmonogram i wystawili to, co trzeba
                if random.random() < 0.90:
                    self.trash_type = random.choice(allowed_today)
                else:
                    self.trash_type = random.choice(types_for_season)
            # w niedziele dzień święty i nie ma śmieci wcale
        else:
            self.trash_weight = 0
            self.trash_type = None

    def reset_house(self):
        # agent wywozi śmieci, więc resetujemy dane domu
        self.needs_collection = False
        self.trash_weight = 0
        self.trash_type = None
