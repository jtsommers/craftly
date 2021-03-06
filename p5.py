import json
from collections import namedtuple, Counter, defaultdict
import astar

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])
all_recipes = []

file_name = "crafting.json"
# file_name = "plutonium.json"

# Create a function to check whether a given state has the tools necessary to create a complex item
# It doesn't check consumable resources since using up resources could be considered progress toward the goal
def create_tool_check(items):
	# items is list of lists
	# Recurse once to add a second layer of prerequisites
	# This will count some tools multiple times, but give them a higher weight because each is used for multiple recipes
	extra_items = []
	for req_list in items:
		extra_items.extend(tool_reqs.get(req_list[0], []))
	items.extend(extra_items)

	# print "Required Items: ", items

	def tool_check(state):
		inventory = dict(state)
		# print "Inventory ", inventory
		tools_needed = len(items)
		for item_options in items:
			for item in item_options:
				if inventory[item] > 0:
					# A sufficient tool was found in the inventory check next tool tuple
					tools_needed -= 1
					break
		return tools_needed
	return tool_check


# Mapping from items that require tools to create to the tools necessary to make them
tool_reqs = { 
	"cart":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe"),("bench",),("furnace",)], 
	"coal":[("stone_pickaxe", "iron_pickaxe")],
	"cobble":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe")], 
	"furnace":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe"),("bench",)], 
	"ingot":[("stone_pickaxe", "iron_pickaxe"),("furnace",)], 
	"iron_axe":[("stone_pickaxe", "iron_pickaxe"),("furnace",),("bench",)], 
	"iron_pickaxe":[("stone_pickaxe", "iron_pickaxe"),("furnace",),("bench",)], 
	"ore":[("stone_pickaxe", "iron_pickaxe")],  
	"rail":[("stone_pickaxe", "iron_pickaxe"),("furnace",),("bench",)], 
	"stone_axe":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe"),("bench",)], 
	"stone_pickaxe":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe"),("bench",)], 
	"wooden_axe":[("bench",)], 
	"wooden_pickaxe":[("bench",)]
}

# Create a function for checking a state for tools still needed for that item
tool_check = {}
for item in tool_reqs:
	tool_check[item] = create_tool_check(tool_reqs[item])

# Return a function that checks whether a recipe can be used at a given state
def make_checker(rule):
	# This runs once per recipe
	# Write a checker function that examines rule['Consumes'] and rule['Requires']
	requirements = {}
	consumes = {}
	if rule.has_key('Requires'):
		requirements = rule['Requires']
	if rule.has_key('Consumes'):
		consumes = rule['Consumes']
	def check(state):
		# This runs a lot
		# Should return whether or not this recipe can be executed
		return has_items(state, requirements) and has_items(state, consumes)

	return check

# Return a function that generates the next state for a given recipe
def make_effector(rule):
	# This runs once per recipe
	# Write an effector function that examines rule['Consumes'] and rule['Produces']
	consumes = {}
	produces = {}
	if rule.has_key('Produces'):
		produces = rule['Produces']
	if rule.has_key('Consumes'):
		consumes = rule['Consumes']
	def effect(state):
		# This runs a lot
		# Should return the next state
		return next_state(state, produces, consumes)

	return effect

class Crafting:
	instance = None
	"""A crafting module that defines recipes and items"""
	def __init__(self):
		# Parse json into python
		# Crafting = {"Initial": {}, "Goal":{}, "Items":[], "Recipes":{}}
		with open(file_name) as f:
			crafting_data = json.load(f)

		self.crafting_data = crafting_data
		self.Initial = crafting_data['Initial']
		self.Items = crafting_data['Items']

		self.ItemMap = {}
		itemIndex = 0;
		for itemName in self.Items:
			self.ItemMap[itemName] = itemIndex
			itemIndex += 1
		
		self.Goal = crafting_data['Goal']
		self.Recipes = crafting_data['Recipes']
		self.all_recipes = []
		self.product_ingredients = defaultdict(lambda:{})

		# Load in the recipe rules
		for name, rule in crafting_data['Recipes'].items():
			checker = make_checker(rule)
			effector = make_effector(rule)
			recipe = Recipe(name, checker, effector, rule['Time'])
			self.all_recipes.append(recipe)
			# Add to a reference of materials required for a product
			for item, amount in rule.get('Produces', {}).items():
				reqs = rule.get('Consumes', {})
				self.product_ingredients[item] = reqs

		# print self.product_ingredients

	@classmethod
	def Maximums(cls, start, goal):
		instance = cls.GetInstance()

		maximums = defaultdict(lambda: 1)
		consumes = defaultdict(lambda: 1)
		produces = defaultdict(lambda: 0)

		for name, rule in instance.Recipes.items():
			products = rule.get('Produces', {})
			ingredients = rule.get('Consumes', {})
			for item, amount in products.items():
				produces[item] = max(amount, produces[item])
			for item, amount in ingredients.items():
				consumes[item] = max(amount, consumes[item])

		# Calculate maximums based on production/consumption
		for item in produces: # This should cover all the items as you can start from scratch to obtain anything
			p = produces[item]
			c = consumes[item]
			# print item, p, c
			# If current inventory is one less than required consumption, we would have to produce another batch
			# maximums[item] = p + max(c, goal.inventory[item]) - 1
			mx = p + c - 1
			g = goal.get(item, 0)
			# Make sure we can make enough things to get to the goal state
			while mx < g:
				mx += p
			# Account for a potentially higher starting inventory
			maximums[item] = max(mx, start.get(item, 0))

		print "Max allowed: ", maximums
		return (maximums, consumes, produces)


	@classmethod
	def GetInstance(cls):
		if not cls.instance:
			cls.instance = cls()
		return cls.instance

	@classmethod
	def Items(cls):
		instance = cls.GetInstance()
		return instance.Items

	@classmethod
	def ItemMap(cls):
		instance = cls.GetInstance()
		return instance.ItemMap

	@classmethod
	def Recipes(cls):
		instance = cls.GetInstance()
		return instance.Recipes

	@classmethod
	def Initial(cls):
		instance = cls.GetInstance()
		return instance.Initial

	@classmethod
	def Goal(cls):
		instance = cls.GetInstance()
		return instance.Goal

	@classmethod
	def Graph(cls):
		instance = cls.GetInstance()
		def graph(state):
			for r in instance.all_recipes:
				if r.check(state):
					yield (r.name, r.effect(state), r.cost)
		return graph

	@classmethod
	def RequirementsForItem(cls, item):
		instance = cls.GetInstance()

def magic_box(item_state, produces = {}, consumes = {}):
	item_list = Crafting.Items()
	state = []
	itemIndex = 0
	for item in item_list:
		amount = item_state[itemIndex][1] - consumes.get(item, 0) + produces.get(item, 0)
		state.append((item, amount))
		itemIndex += 1
	return tuple(state)
		
def has_items(state, items):
	# print "state: ", state
	# print "item_state: ", item_state
	for itemName in items:
		itemAmount = items[itemName]
		itemIndex = Crafting.ItemMap()[itemName]
		if state[itemIndex][1] < itemAmount:
			return False
	return True

def has_item(state, item):
	name, needed = item
	for item, value in state:
		if item == name:
			if value < needed:
				return False
			else:
				return True
	return False

def next_state(state, produces, consumes):
	return magic_box(state, produces, consumes)

def get_important_item_count(inventory, goalInv):
		total_items_remaining = 0
		for item in goalInv:
			# TODO/thought: maybe max isn't necessary and a negative count would incentivize minimum viable inventory
			total_items_remaining += max(goalInv[item] - inventory[item], 0)
		return total_items_remaining


def make_RIKLS_heuristic(start, goal):
	# Discourage states with more than the necessary amount of items in inventory
	maximums, consumes, produces = Crafting.Maximums(start, goal)

	def RIKLS_heuristic(state):
		tool_counter = 0
		ingredient_counter = 0

		# Prune states with more than max necessary amount of an item
		for item, amount in state:
			if amount > maximums[item]:
				return float("inf")
		# return 0
		
		inventory = dict(state)

		for item in goal:
			if not has_item(state, (item,goal[item])):
				goal_ingredients = Crafting.GetInstance().product_ingredients[item]
				if not has_items(state, goal_ingredients):
					ingredient_counter += get_important_item_count(inventory, goal_ingredients)
		# print state
		return ingredient_counter

	return RIKLS_heuristic


def make_initial_state(inventory):
	# Create a state tuple from the starting inventory dictionary
	item_list = Crafting.Items()
	state = []
	for item in item_list:
		amount = inventory.get(item, 0)
		state.append((item, amount))
	return tuple(state)

def make_goal_checker(goal):
	def is_goal(state):
		return has_items(state, goal)
	return is_goal

def make_tool_goal_checker(goal):
	def is_goal(state):
		tool_counter = 0
		for item in goal:
			tool_counter += tool_check.get(item, lambda x:0)(state)
		return tool_counter == 0
	return is_goal

init = Crafting.Initial()
fin = Crafting.Goal()

maximums, max_consumes, max_produces = Crafting.Maximums(init, fin)

start = make_initial_state(init)
end = make_initial_state(fin)
is_goal = make_goal_checker(fin)

full_path = []
total_cost = 0

# Create subgoals for the planner to search
# First goal, get all necessary tools
if file_name == "crafting.json":
	is_goal = make_tool_goal_checker(fin)
	cost, path = astar.search(Crafting.Graph(), start, is_goal, 1000, make_RIKLS_heuristic(init, fin))
	full_path.extend(path)
	total_cost += cost
	start = astar.end_state

	# Look for one item at a time
	subgoal = Counter()
	for item in fin:
		amount = fin[item]
		chunk = max_produces[item]
		while amount > 0:
			subgoal[item] += chunk
			print "Searching for subgoal: ", subgoal
			is_goal = make_goal_checker(subgoal)
			cost, path = astar.search(Crafting.Graph(), start, is_goal, 1000, make_RIKLS_heuristic(init, subgoal))
			if cost > 1000:
				print "COST OVERFLOW ", subgoal
			full_path.extend(path)
			total_cost += cost
			start = astar.end_state
			# Do one chunk of production at a time
			amount -= chunk
else:
	# Search for the remaining goal starting from previous subgoal
	is_goal = make_goal_checker(fin)
	cost, path = astar.search(Crafting.Graph(), start, is_goal, 1000, make_RIKLS_heuristic(init, fin))
	full_path.extend(path)
	total_cost += cost

print ""
print "=== FINAL RESULTS ==="
print "Total cost: ", total_cost
print "Action path: ", full_path
print "Final Inventory: ", astar.end_state

# print astar.search(Crafting.Graph(), start, is_goal, 1000, make_RIKLS_heuristic(init, fin))

# print astar.end_state

