import json
from collections import namedtuple, Counter, defaultdict
import astar

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])
all_recipes = []

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

		# Load in the recipe rules
		for name, rule in crafting_data['Recipes'].items():
			checker = make_checker(rule)
			effector = make_effector(rule)
			recipe = Recipe(name, checker, effector, rule['Time'])
			self.all_recipes.append(recipe)

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

		

class State():
	"""An inventory state for the craftly minecraft crafting planner"""
	def __init__(self, inventory):
		self.inventory = Counter(inventory)
		# self.update()
		
	# def __hash__(self):
	# 	# return frozenset(self.inventory.items()).__hash__()
	# 	return self.hash

	# def __eq__(self, other):
	# 	return self.hash is other.hash

	def __str__(self):
		return self.inventory.__str__()

	def has_items(self, items):
		for item in items:
			amount = items[item]

			# Special case for Requires since the dictionary is True/False for a single item needed
			# An integer amount falls through both cases
			if amount is True:
				amount = 1
			elif amount is False:
				amount = 0

			if self.inventory[item] < amount:
				return False
		return True

	# def update(self):
	# 	self.hash = tuple(self.inventory.get(name, 0) for i,name in enumerate(Crafting.Items())).__hash__()

	def to_tuple(self):
		return tuple(self.inventory.get(name, 0) for i,name in enumerate(Crafting.Items()))

	def get_important_item_count(self, goalInv):
		total_items_remaining = 0
		for item in goalInv:
			total_items_remaining += max(goalInv[item] - self.inventory[item], 0)
		return total_items_remaining

	def next_state(self, consumes, produces):
		next = State(self.inventory)
		for name in consumes:
			amount = consumes[name]
			next.inventory[name] -= amount
		for name in produces:
			amount = produces[name]
			next.inventory[name] += amount
		# next.update()
		return next


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
		maximums[item] = p + c - 1

	# print maximums


	def RIKLS_heuristic(state):
		for item, amount in state.inventory.items():
			if amount > maximums[item]:
				return float("inf")
		return 0

	return RIKLS_heuristic

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
		return state.has_items(requirements) and state.has_items(consumes)

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
		return state.next_state(consumes, produces)

	return effect

def make_initial_state(inventory):
	# Do something to make a state
	return State(inventory)

def make_goal_checker(goal):
	def is_goal(state):
		return state.has_items(goal)
	return is_goal

init = Crafting.Initial()
fin = Crafting.Goal()

start = make_initial_state(init)
end = make_initial_state(fin)
is_goal = make_goal_checker(fin)

print astar.search(Crafting.Graph(), start, is_goal, 35, make_RIKLS_heuristic())
