import json
from collections import namedtuple, Counter, defaultdict
import astar

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])
all_recipes = []

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

	def tool_check(state):
		inventory = dict(state)
		tools_needed = len(items)
		for item_options in items:
			for item in inventory:
				if item in item_options:
					# A sufficient tool was found in the inventory check next tool tuple
					tools_needed -= 1
					break
		return tools_needed
	return tool_check


# Mapping from items that require tools to create to the tools necessary to make them
tool_reqs = { 
	"cart":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe"),("bench"),("furnace")], 
	"coal":[("stone_pickaxe", "iron_pickaxe")],
	"cobble":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe")], 
	"furnace":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe"),("bench")], 
	"ingot":[("stone_pickaxe", "iron_pickaxe"),("furnace")], 
	"iron_axe":[("stone_pickaxe", "iron_pickaxe"),("furnace"),("bench")], 
	"iron_pickaxe":[("stone_pickaxe", "iron_pickaxe"),("furnace"),("bench")], 
	"ore":[("stone_pickaxe", "iron_pickaxe")],  
	"rail":[("stone_pickaxe", "iron_pickaxe"),("furnace"),("bench")], 
	"stone_axe":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe"),("bench")], 
	"stone_pickaxe":[("wooden_pickaxe", "stone_pickaxe", "iron_pickaxe"),("bench")], 
	"wooden_axe":[("bench")], 
	"wooden_pickaxe":[("bench")]
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
		with open('crafting.json') as f:
			crafting_data = json.load(f)

		self.crafting_data = crafting_data
		self.Initial = crafting_data['Initial']
		self.Items = crafting_data['Items']
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

		print self.product_ingredients

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

def magic_box(items = {}, produces = {}, consumes = {}):
	item_list = Crafting.Items()
	state = []
	for item in item_list:
		amount = items.get(item, 0) - consumes.get(item, 0) + produces.get(item, 0)
		state.append((item, amount))
	return tuple(state)

empty_state = magic_box()
		
def has_items(state, items):
	# print "state: ", state
	# print "item_state: ", item_state
	item_state = magic_box(items)
	for i in range(len(state)):
		if state[i][1] < item_state[i][1]:
			return False
	return True

def next_state(state, produces, consumes):
	return magic_box(dict(state), produces, consumes)


def make_RIKLS_heuristic(goal):
	# discourage states with more than the necessary amount of items in inventory

	maximums = defaultdict(lambda: 1)
	consumes = defaultdict(lambda: 1)
	produces = defaultdict(lambda: 0)

	for name, rule in Crafting.Recipes().items():
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
		maximums[item] = p + max(c, goal.get(item, 0)) - 1

	print maximums


	def RIKLS_heuristic(state):
		tool_counter = 0
		ingredient_counter = 0
		for item, amount in state:
			if amount > maximums[item]:
				return float("inf")
		return 0

		# Doesn't help enough yet
		for item in goal:
			tool_counter += tool_check.get(item, lambda x:0)(state)
			goal_ingredients = Crafting.GetInstance().product_ingredients[item]
			# ingredient_counter += state.get_important_item_count(goal_ingredients)
		
		if tool_counter > 0:
			return 10*tool_counter
		# elif not is_goal(state):
		# 	return ingredient_counter * 2
		else:
			return 0

	return RIKLS_heuristic

def make_goal_heuristic(goal):
	pass



def make_initial_state(inventory):
	# Do something to make a state
	return magic_box(inventory)

def make_goal_checker(goal):
	def is_goal(state):
		return has_items(state, goal)
	return is_goal

init = Crafting.Initial()
fin = Crafting.Goal()

start = make_initial_state(init)
end = make_initial_state(fin)
is_goal = make_goal_checker(fin)

print astar.search(Crafting.Graph(), start, is_goal, 1000, make_RIKLS_heuristic(fin))

