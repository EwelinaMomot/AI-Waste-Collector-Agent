class GasStation:
    def __init__(self, grid_x, grid_y):
        self.x = grid_x
        self.y = grid_y

    def refill_agent(self, agent):
        agent.current_fuel = agent.fuel_capacity