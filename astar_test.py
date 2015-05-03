import astar

t_initial = 'a'
t_limit = 20
edges = {'a': {'b':1, 'c':10}, 'b':{'c':1}}

def t_graph(state):
	for next_state, cost in edges[state].items():
		yield ((state, next_state), next_state, cost)

def t_is_goal(state):
	return state == 'c'

def null_heuristic(state):
	return 0

print astar.search(t_graph, t_initial, t_is_goal, null_heuristic)