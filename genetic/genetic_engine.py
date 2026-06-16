import random
from genetic.genetic_operators import order_crossover, mutate

class GeneticRouteEngine:
    def __init__(self, population_size=100):
        self.population_size = population_size

    def calculate_distance(self, pos1, pos2):
        # Odległość Manhattana
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def calculate_total_route_distance(self, route, houses, start_pos=(0, 0)):
        # Całkowity dystans trasy
        total_dist = 0
        current_pos = start_pos  # Start z aktualnej pozycji agenta
        
        for house_idx in route:
            house_pos = houses[house_idx]
            total_dist += self.calculate_distance(current_pos, house_pos)
            current_pos = house_pos
            
        total_dist += self.calculate_distance(current_pos, (0, 0)) # Powrót do bazy
        return total_dist

    def calculate_fitness(self, route, houses, start_pos=(0, 0)):
        # Fitness (odwrotność dystansu)
        distance = self.calculate_total_route_distance(route, houses, start_pos)
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
    
    def evolve(self, houses, generations=100, mutation_rate=0.05, start_pos=(0, 0)):

        population = self.create_initial_population(
            len(houses)
        )

        best_route = None
        best_distance = float("inf")
        generation_history = []  # historia dystansów per pokolenie

        for generation in range(generations):

            fitness_scores = [
                self.calculate_fitness(route, houses, start_pos)
                for route in population
            ]

            #ELITYZM czyli znajdź najlepszego osobnika
            distances = [
                self.calculate_total_route_distance(
                    route,
                    houses,
                    start_pos
                )
                for route in population
            ]

            best_idx = distances.index(min(distances))
            elite = population[best_idx].copy()

            new_population = [elite]

            while len(new_population) < self.population_size:

                parent1 = self.roulette_wheel_selection(
                    population,
                    fitness_scores
                )

                parent2 = self.roulette_wheel_selection(
                    population,
                    fitness_scores
                )

                child = order_crossover(
                    parent1,
                    parent2
                )

                child = mutate(
                    child,
                    mutation_rate
                )

                new_population.append(child)

            population = new_population

            distances = [
                self.calculate_total_route_distance(
                    route,
                    houses,
                    start_pos
                )
                for route in population
            ]

            current_best = min(distances)
            generation_history.append(current_best)

            if current_best < best_distance:

                best_distance = current_best

                best_route = population[
                    distances.index(current_best)
                ].copy()

            print(
                f"[GA] Pokolenie {generation + 1:>3}/{generations}: "
                f"najlepszy dystans = {current_best}"
            )

        return best_route, best_distance, generation_history
    
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

    print("TEST GENETIC OPERATORS")
    child = order_crossover(parent1, parent2)

    print("\nPo krzyżowaniu:")
    print(child)

    child = mutate(child)

    print("\nPo mutacji:")
    print(child)

    print(
        f"Dystans dziecka: "
        f"{engine.calculate_total_route_distance(child, simulated_houses)}"
    )

    print("TEST BEST ROUTE")
    best_route, best_distance, history = engine.evolve(
    simulated_houses,
    generations=100
    )

    print("\nNAJLEPSZA ZNALEZIONA TRASA")
    print(best_route)
    print("Dystans:", best_distance)
    print(f"Ewolucja: start={history[0]}, koniec={history[-1]}")