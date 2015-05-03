import json
from collections import namedtuple

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])
all_recipes = []

# Return a function that checks whether a recipe can be used at a given state
def make_checker(rule):
	# This runs once per recipe
	# Write a checker function that examines rule['Consumes'] and rule['Requires']
	def check(state):
		# This runs a lot
		# Should return whether or not this recipe can be executed
		return True

	return check

# Return a function that generates the next state for a given recipe
def make_effector(rule):
	# This runs once per recipe
	# Write an effector function that examines rule['Consumes'] and rule['Produces']
	def effect(state):
		# This runs a lot
		# Should return the next state
		return state

	return effect


# An adjacency function for traversing a recipe state
def graph(state):
	for r in all_recipes:
		if r.check(state):
			yield (r.name, r.effect(state), r.cost)

# Parse json into python
# Crafting = {"Initial": {}, "Goal":{}, "Items":[], "Recipes":{}}
with open('crafting.json') as f:
	Crafting = json.load(f)

# Load in the recipe rules
for name, rule in Crafting['Recipes'].items():
	checker = make_checker(rule)
	effector = make_effector(rule)
	recipe = Recipe(name, checker, effector, rule['Time'])
	all_recipes.append(recipe)