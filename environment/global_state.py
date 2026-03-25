import random
from enum import Enum

class Weather(Enum):
    SUNNY = 1
    RAINY = 2
    SNOWY = 3

class Season(Enum):
    SPRING = 1
    SUMMER = 2
    AUTUMN = 3
    WINTER = 4

class GlobalState:
    def __init__(self):
        self.current_weather = Weather.SUNNY
        self.current_season = Season.SUMMER
        self.current_day = "Monday"
        self.day_counter = 0 # licznik, który będzie pilnował zmiany pory roku

        # harmonogram wywozu śmieci
        self.schedule = {
            "Monday": ["papier", "plastik_metal"],
            "Tuesday": ["szklo", "bio"],
            "Wednesday": ["zmieszane", "papier"],
            "Thursday": ["plastik_metal", "szklo"],
            "Friday": ["bio", "zmieszane"],
            "Saturday": ["zmieszane"],
            "Sunday": [] # dzień wolny
        }

    def get_allowed_types_today(self):
        return self.schedule.get(self.current_day, [])

    def change_weather(self):
        # prawodopodobieństwa pogody zależne od pory roku
        if self.current_season == Season.SPRING:
            weights = [60, 39, 1]    # Wiosna: 60% słońce, 40% deszcz
        elif self.current_season == Season.SUMMER:
            weights = [80, 20, 0]
        elif self.current_season == Season.AUTUMN:
            weights = [29, 70, 1]
        elif self.current_season == Season.WINTER:
            weights = [30, 10, 60]

        # random.choices zwraca listę wyników, więc bierzemy pierwszy [0]
        self.current_weather = random.choices(list(Weather), weights=weights, k=1)[0]

    def next_season(self):
        seasons = list(Season)
        current_index = seasons.index(self.current_season)
        next_index = (current_index + 1) % len(seasons)
        self.current_season = seasons[next_index]
        print(f"ZMIANA PORY ROKU NA: {self.current_season.name}")

    def next_day(self):
        days = list(self.schedule.keys())
        current_index = days.index(self.current_day)
        next_index = (current_index + 1) % 7 # modulo 7 żeby wrócić do poniedziałku po niedzieli
        self.current_day = days[next_index]
        print(f"NOWY DZIEŃ: {self.current_day}")
        
        self.day_counter += 1
        
        # zmiana pory roku co 7 dni (po każdej niedzieli)
        if self.day_counter % 7 == 0:
            self.next_season()

        # po zmianie dnia nowa
        self.change_weather()