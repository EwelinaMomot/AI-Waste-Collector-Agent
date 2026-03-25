import random
from environment.global_state import Season

class House:
    def __init__(self, grid_x, grid_y, global_state, designated_trash_type=None):
        self.x = grid_x
        self.y = grid_y
        self.possible_types = ["papier", "plastik_metal", "szklo", "bio", "zmieszane"]
        self.designated_trash_type = designated_trash_type

        self.generate_trash(global_state)  # generujemy śmieci uwzględniając porę roku z global_state

    def generate_trash(self, global_state):
        self.needs_collection = random.choice([True, False])  # losowo wybiera czy trzeba wywieźć śmieci

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

            if self.designated_trash_type is not None:
                self.trash_type = self.designated_trash_type
            else:
                self.trash_type = random.choice(types_for_season)
        else:
            self.trash_weight = 0
            self.trash_type = None

    def reset_house(self):
        # agent wywozi śmieci, więc resetujemy dane domu
        self.needs_collection = False
        self.trash_weight = 0
        self.trash_type = None
