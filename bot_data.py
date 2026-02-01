import json
import random
import sqlite3
import re

import utility_functions

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

		self.database = sqlite3.connect("bot_data.db")
		self.database_cursor = self.database.cursor()

		self.queue_random_avatars(avatars)

		self.vars_regex = re.compile(r"\$\{(.+?)\}")
	
	def get_variable(self, name: str):
		self.database_cursor.execute("SELECT value FROM variables WHERE name = ?", (name,))
		return self.database_cursor.fetchone()[0]
		
	def store_variable(self, name: str, value):
		self.database_cursor.execute("UPDATE variables SET value = ? WHERE name = ?", (value, name))
		self.database.commit()

	def increment_variable(self, name: str):
		self.database_cursor.execute("UPDATE variables SET value = value + 1 WHERE name = ?", (name,))
		self.database.commit()

	def get_foxrule(self) -> str:
		self.database_cursor.execute("SELECT rule FROM fox_rules ORDER BY RANDOM() LIMIT 1")
		return self.database_cursor.fetchone()[0]
	
	def add_foxrule(self, author: str, rule: str):
		self.database_cursor.execute("SELECT MAX(num) FROM fox_rules")
		new_num = self.database_cursor.fetchone()[0] + 1
		self.database_cursor.execute("INSERT INTO fox_rules VALUES (?, ?, ?, DATETIME('now', 'localtime'))", (new_num, rule, author))
		self.database.commit()

	def get_foxrule_count(self) -> int:
		self.database_cursor.execute("SELECT COUNT(*) FROM fox_rules")
		return self.database_cursor.fetchone()[0]

	def get_first_count(self, username: str) -> int:
		self.database_cursor.execute("SELECT count FROM first_counts WHERE username = ?", (username,))
		return self.database_cursor.fetchone()[0]

	def increment_first_count(self, username: str):
		self.database_cursor.execute("UPDATE first_counts SET count = count + 1 WHERE username = ?", (username,))
		self.database.commit()

	def get_current_chatter_form(self, username: str) -> str:
		self.database_cursor.execute("SELECT current_form FROM chatter_forms WHERE username = ?", (username,))
		return self.database_cursor.fetchone()[0]

	def update_tail_length(self, username: str, amount: int):
		self.database_cursor.execute("UPDATE tirga_tail_lengths SET length = length + ? WHERE username = ?", (amount, username))
		self.database.commit()

	def queue_random_avatars(self, avatars: dict):
		self.random_avatars = [av for av in avatars.values() if av["allow_random"]]
		random.shuffle(self.random_avatars)

	def replace_vars_in_string(self, string: str) -> str:
		result = string
		matches = self.vars_regex.findall(string)
		for mat in matches:
			value = ""
			if mat == "mainecoone_name":
				value = utility_functions.get_mainecoone_name("pawb_bot")
			else:
				self.database_cursor.execute("SELECT value FROM variables WHERE name = ?", (mat,))
				value = self.database_cursor.fetchone()[0]

			result = self.vars_regex.sub(str(value), result, 1)

		return result
