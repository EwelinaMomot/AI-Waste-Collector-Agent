import heapq


def astar(start_state, goal_state, problem):
    gx, gy = goal_state[0], goal_state[1]

    def goal_match(s):
        x, y, _ = s
        return x == gx and y == gy

    open_heap = []
    start_h = problem.heuristic(start_state)
    heapq.heappush(open_heap, (start_h, 0, start_state))

    g_cost = {start_state: 0}
    parent = {start_state: None}
    action_to_reach = {start_state: None}
    closed_list = set()

    while open_heap:
        _, current_g, n = heapq.heappop(open_heap)

        if n in closed_list:
            continue
        if current_g > g_cost.get(n, float("inf")):
            continue

        closed_list.add(n)

        if goal_match(n):
            return reconstruct_actions(n, parent, action_to_reach), closed_list

        for action, m, step_cost in problem.get_successors_with_costs(n):
            if m in closed_list:
                continue

            new_g = g_cost[n] + step_cost
            if new_g < g_cost.get(m, float("inf")):
                g_cost[m] = new_g
                parent[m] = n
                action_to_reach[m] = action
                f_cost = new_g + problem.heuristic(m)
                heapq.heappush(open_heap, (f_cost, new_g, m))

    return None, closed_list


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
