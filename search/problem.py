from environment.dumpster import Dumpster
from environment.house import House
from environment.station import GasStation

from search.state import DX, DY

ACTION_FORWARD = "przód" ## do ustalenia nazwy, tymczasowo dalam tak - jak coś to możecie pozmieniać
ACTION_TURN_LEFT = "obrót w lewo"
ACTION_TURN_RIGHT = "obrót w prawo"


class GridSearchProblem:

    def __init__(self, grid, goal_x, goal_y, action_costs=None, cell_entry_costs=None):
        self.grid = grid
        self.goal_x = goal_x
        self.goal_y = goal_y
        self.action_costs = action_costs or {
            ACTION_FORWARD: 1,
            ACTION_TURN_LEFT: 1,
            ACTION_TURN_RIGHT: 1,
        }
        self.cell_entry_costs = cell_entry_costs or {
            "grass": 1,
            "house": 10,
            "dumpster": 5,
            "station": 5,
        }

    def is_goal(self, state):
        x, y, _ = state
        return x == self.goal_x and y == self.goal_y

    def is_out_of_bounds(self, x, y):
        if x < 0 or y < 0:
            return True
        if x >= self.grid.width or y >= self.grid.height:
            return True
        return False

    def is_cell_blocked_for_entry(self, x, y):
        if self.is_out_of_bounds(x, y):
            return True
        cell = self.grid.cells[y][x]
        if cell is None:
            return False
        if isinstance(cell, House) or isinstance(cell, Dumpster) or isinstance(cell, GasStation):
            return False
        return False

    def can_move_forward(self, state):
        x, y, d = state
        nx = x + DX[d]
        ny = y + DY[d]
        return not self.is_cell_blocked_for_entry(nx, ny)

    def get_successors(self, state):
        x, y, d = state
        out = []

        left_dir = (d - 1) % 4 # dir jest jako numerek, aby tu latwiej bylo z obrotami
        right_dir = (d + 1) % 4
        out.append((ACTION_TURN_LEFT, (x, y, left_dir)))
        out.append((ACTION_TURN_RIGHT, (x, y, right_dir)))

        if self.can_move_forward(state):
            nx = x + DX[d]
            ny = y + DY[d]
            out.append((ACTION_FORWARD, (nx, ny, d)))

        return out

    def get_cell_entry_cost(self, x, y):
        cell = self.grid.cells[y][x]
        if cell is None:
            return self.cell_entry_costs["grass"]
        if isinstance(cell, House):
            return self.cell_entry_costs["house"]
        if isinstance(cell, Dumpster):
            return self.cell_entry_costs["dumpster"]
        if isinstance(cell, GasStation):
            return self.cell_entry_costs["station"]
        return self.cell_entry_costs["grass"]

    def get_action_cost(self, action, from_state, to_state):
        if action == ACTION_FORWARD:
            x, y, _ = to_state
            return self.action_costs[ACTION_FORWARD] + self.get_cell_entry_cost(x, y)
        return self.action_costs[action]

    def get_successors_with_costs(self, state):
        out = []
        for action, next_state in self.get_successors(state):
            step_cost = self.get_action_cost(action, state, next_state)
            out.append((action, next_state, step_cost))
        return out

    def heuristic(self, state):
        x, y, _ = state
        return abs(x - self.goal_x) + abs(y - self.goal_y)

    def is_goal_house_with_trash(self, state):
        if not self.is_goal(state):
            return False
        cell = self.grid.cells[self.goal_y][self.goal_x]
        if not isinstance(cell, House):
            return False
        if not cell.needs_collection:
            return False
        if cell.trash_type is None:
            return False
        return True
