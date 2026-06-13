import random


def order_crossover(parent1, parent2):
    #zwraca nowe dziecko

    size = len(parent1)

    start, end = sorted(
        random.sample(range(size), 2)
    )

    child = [-1] * size

    #kopiujemy fragment z rodzica 1
    child[start:end + 1] = parent1[start:end + 1]

    #geny(domki) z rodzica 2 których jeszcze nie ma
    remaining = []

    for gene in parent2:
        if gene not in child:
            remaining.append(gene)

    idx = 0

    for i in range(size):
        if child[i] == -1:
            child[i] = remaining[idx]
            idx += 1

    return child


def mutate(route, mutation_rate=0.05):
    
    #Mutacja przez zamianę dwóch domków
    

    route = route.copy()

    if random.random() < mutation_rate:

        i, j = random.sample(
            range(len(route)),
            2
        )

        route[i], route[j] = (
            route[j],
            route[i]
        )

    return route



if __name__ == "__main__":

    parent1 = [0, 1, 2, 3, 4, 5]
    parent2 = [4, 5, 3, 2, 1, 0]

    print("Rodzic 1:", parent1)
    print("Rodzic 2:", parent2)

    child = order_crossover(parent1, parent2)

    print("Dziecko:", child)

    mutated = mutate(child)

    print("Po mutacji:", mutated)