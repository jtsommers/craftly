import json
from collections import namedtuple, Counter
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
		
	def __hash__(self):
		return frozenset(self.inventory.items()).__hash__()
		# return tuple(self.inventory.get(name, 0) for i,name in enumerate(Crafting.Items())).__hash__()

	def __eq__(self, other):
		return self.__hash__() is other.__hash__()

	def __str__(self):
		return self.inventory.__str__()

	def has_items(self, items):
		for item, amount in items.items():
			if amount is True:
				amount = 1
			elif amount is False:
				amount = 0
			if self.inventory[item] < amount:
				return False
		return True

	def next_state(self, consumes, produces):
		next = State(self.inventory)
		for name, amount in consumes.items():
			next.inventory[name] -= amount
		for name, amount in produces.items():
			next.inventory[name] += amount
		return next

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

init = {}
fin = {'wooden_pickaxe': 1}

start = make_initial_state(init)
is_goal = make_goal_checker(fin)

print astar.search(Crafting.Graph(), start, is_goal, 35)
