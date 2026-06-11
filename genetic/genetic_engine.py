import random

class GeneticRouteEngine:
    def __init__(self, population_size=100):
        self.population_size = population_size

    def calculate_distance(self, pos1, pos2):
        # Odległość Manhattana
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def calculate_total_route_distance(self, route, houses):
        # Całkowity dystans trasy
        total_dist = 0
        current_pos = (0, 0)  # Start z bazy (0,0)
        
        for house_idx in route:
            house_pos = houses[house_idx]
            total_dist += self.calculate_distance(current_pos, house_pos)
            current_pos = house_pos
            
        total_dist += self.calculate_distance(current_pos, (0, 0)) # Powrót do bazy
        return total_dist

    def calculate_fitness(self, route, houses):
        # Fitness (odwrotność dystansu)
        distance = self.calculate_total_route_distance(route, houses)
        return 1.0 / (float(distance) + 1e-6) # Zabezpieczenie przed /0

    def create_initial_population(self, num_houses):
        # Losowa populacja początkowa
        population = []
        base_route = list(range(num_houses))
        
        for _ in range(self.population_size):
            random_route = base_route.copy()
            random.shuffle(random_route)
            population.append(random_route)
            
        return population

    def roulette_wheel_selection(self, population, fitness_scores):
        # Wybór rodzica (reguła ruletki)
        total_fitness = sum(fitness_scores)
        pick = random.uniform(0, total_fitness) # Losowy punkt na kole
        
        current_sum = 0
        for individual, fitness in zip(population, fitness_scores):
            current_sum += fitness
            if current_sum > pick:
                return individual
                
        return population[-1] # Fallback

# KOD TESTOWY:
if __name__ == "__main__":
    print("\nTEST SILNIKA GENETYCZNEGO")
    
    simulated_houses = [
        (2, 5), (10, 12), (1, 1), (14, 2), 
        (8, 8), (3, 11), (12, 4), (6, 1)
    ]
    
    engine = GeneticRouteEngine(population_size=100)
    pop = engine.create_initial_population(len(simulated_houses))
    
    print(f"Utworzono populację: {len(pop)} tras.")
    
    fitness_scores = [engine.calculate_fitness(r, simulated_houses) for r in pop]
    distances = [engine.calculate_total_route_distance(r, simulated_houses) for r in pop]
    
    print(f"Najkrótsza trasa (start): {min(distances)}")
    print(f"Najdłuższa trasa (start): {max(distances)}")
    
    parent1 = engine.roulette_wheel_selection(pop, fitness_scores)
    parent2 = engine.roulette_wheel_selection(pop, fitness_scores)
    
    print("\nWylosowani rodzice - Ruletka")
    print(f"- Rodzic 1: {parent1} (Dystans: {engine.calculate_total_route_distance(parent1, simulated_houses)})")
    print(f"- Rodzic 2: {parent2} (Dystans: {engine.calculate_total_route_distance(parent2, simulated_houses)})\n")