from collections import deque


def bfs(start_state, goal_state, problem):
    # start_state: (x, y, kierunek)
    # goal_state: (gx, gy) — tylko wspolrzedne celu, kierunek na celu dowolny, dawać będziemy imo na początek jakiś konkretny domek aby pokazać dzialanie
    # zwraca liste akcji (!! tak z tego co kojarzę Pan mówil, ale najwyżej też zmienimy) albo None

    gx, gy = goal_state[0], goal_state[1]

    def goal_match(s):
        x, y, _ = s
        return x == gx and y == gy

    open_list = deque()
    open_list.append(start_state)
    closed_list = set()

    parent = {start_state: None}
    action_to_reach = {start_state: None}

    while len(open_list) > 0:
        n = open_list.popleft()

        if n in closed_list:
            continue
        closed_list.add(n)

        if goal_match(n):
            return reconstruct_actions(n, parent, action_to_reach)

        for action, m in problem.get_successors(n):
            if m in closed_list:
                continue
            if m not in parent:
                parent[m] = n
                action_to_reach[m] = action
                open_list.append(m)

    return None


def reconstruct_actions(end, parent, action_to_reach):
    path = []
    cur = end
    while cur is not None and parent.get(cur) is not None:
        act = action_to_reach.get(cur)
        if act:
            path.append(act)
        cur = parent.get(cur)
    path.reverse()
    return path
