class Dumpster:
    # strefy na wysypisku
    ZONES = ["papier", "plastik_metal", "szklo", "bio", "zmieszane"]

    def __init__(self, grid_x, grid_y, zone_type):
        self.x = grid_x
        self.y = grid_y

        # spradzanie, czy typ strefy jest poprwany
        if zone_type in self.ZONES:
            self.zone_type = zone_type
        else:
            self.zone_type = "zmieszane"

    def accept_trash(self, trash_type):
        # sprawdzanie, czy typ śmieci pasuje do strefy
        if trash_type == self.zone_type:
            return True
        elif self.zone_type == "zmieszane":
            return True  # strefa zmieszana akceptuje wszystkie typy
        else:
            return False