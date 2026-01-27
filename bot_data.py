import json
import random

class BotData():
	def __init__(self, avatars: dict):
		self.bless_count = 0
		self.undo_count = 0
		self.distracted_count = 0
		self.silly_mode = False
		self.avatar = "sphinx"
		self.current_hype_level = 0
		self.highest_hype_level = 0
		self.best_button_broken = False
		self.greetings_said = set()

		with open("foxrules.json", encoding="utf8") as foxrules_file:
			self.foxrules = json.load(foxrules_file)
		
		with open("variables.json", encoding="utf8") as variables_file:
			self.variables = json.load(variables_file)

		self.queue_random_avatars(avatars)
	
	def get_variable(self, name: str):
		return self.variables[name]
		
	def store_variable(self, name: str, value):
		self.variables[name] = value
		variables_file = open("variables.json", "w", encoding="utf8")
		json.dump(self.variables, variables_file)
		variables_file.close()

	def get_foxrule(self):
		return random.choice(self.foxrules)
	
	def add_foxrule(self, author: str, rule: str):
		self.foxrules.append({"author": author, "rule": rule})
		foxrules_file = open("foxrules.json", "w", encoding="utf8")
		json.dump(self.foxrules, foxrules_file)
		foxrules_file.close()

	def queue_random_avatars(self, avatars: dict):
		self.random_avatars = [av for av in avatars.values() if av["allow_random"]]
		random.shuffle(self.random_avatars)
