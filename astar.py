try:
	import Queue as Q  # ver. < 3.0
except ImportError:
	import queue as Q

verbose = True
def debug(*args):
	if (verbose):
		print ''.join([str(arg) for arg in args])

# Trivial heuristic
def null_heuristic(state):
	return 0

# Generic A* search
# TODO: use limit
def search(graph, initial, is_goal, limit, heuristic=null_heuristic):
	global end_state
	end_state = initial
	# Initialization
	frontier = Q.PriorityQueue()
	# Save out a sequence of states to the goal
	previous = {}
	previous[initial] = None
	# Save the actions taken to get to that state
	action_to_state = {}
	# Store the cost of the path so far
	cost_so_far = {}
	cost_so_far[initial] = 0
	frontier.put((0, initial))

	while not frontier.empty():
		priority, current_state = frontier.get()
		if is_goal(current_state):
			# Found the target
			debug("A* found goal")
			break
		elif priority >= limit:
			# Limit reached, stop the search
			debug("Search stop, limit(", limit,") reached")
			break

		# print "==="
		# print current_state, priority, cost_so_far[current_state]
		# print "==="

		# Traverse the adjacent nodes
		for action, next_state, cost in graph(current_state):
			new_cost = cost_so_far[current_state] + cost
			if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
				cost_so_far[next_state] = new_cost
				previous[next_state] = current_state
				action_to_state[next_state] = action
				priority = new_cost + heuristic(next_state)
				if priority < limit:
					frontier.put((priority, next_state))
					# print action
					# print next_state, priority

	# Build up the plan
	plan = []
	total_cost = float("inf")
	if is_goal(current_state):
		end_state = current_state
		total_cost = cost_so_far[current_state]
		while previous[current_state]:
			plan.append(action_to_state[current_state])
			current_state = previous[current_state]

		plan.reverse()

	return total_cost, plan
