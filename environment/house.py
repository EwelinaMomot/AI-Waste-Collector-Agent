import random

class House:
    def __init__(self, grid_x, grid_y):
        self.x = grid_x
        self.y = grid_y

        self.possible_types = ["papier", "plastik_metal", "szklo", "bio", "zmieszane"]

        # DANE DOMU
        self.needs_collection = random.choice([True, False])  # losowo wybiera czy trzeba wywieźć śmieci
        
        if self.needs_collection:
            self.trash_weight = random.randint(1, 15)
            # na razie losowo przypisuje typ śmieci 
            self.trash_type = random.choice(self.possible_types)
        else:
            self.trash_weight = 0
            self.trash_type = None

    def reset_house(self):
        # agent wywozi śmieci, więc resetujemy dane domu
        self.needs_collection = False
        self.trash_weight = 0
        self.trash_type = None