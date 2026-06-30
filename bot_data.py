import random
import sqlite3
import re
from avatar_action import AvatarAction
import datetime
from collections import deque

import utility_functions

class BotData():
	def __init__(self, avatars: dict):
		self.current_avatar = "sphinx"
		self.current_queue_size = 0
		self.silly_mode = False
		self.best_button_broken = False
		self.peer_pressure_level = 0
		self.planks_disabled = False

		self.diane_dragon_level = 0

		self.action_queue = deque[AvatarAction]()
		self.stream_markers = list[tuple[str, int, int, int]]()

		self.database = sqlite3.connect("bot_data.db")
		self.database_cursor = self.database.cursor()

		self.current_avatar_rotation = []
		self.avatar_rotation_ids = [
			"fdbfd353-7828-4220-8351-53c9b61572a8",
			"97df88a8-4d76-4f82-b4ba-d221ae1457a2",
			"24a3f4af-1318-4da1-b728-5d57f01a81f5",
			"4f410a06-a112-47a7-a83a-fdfc434a2e0c",
			"171fc124-04dd-40d8-816a-4db8130ea25c",
		]

		self.queue_random_avatars(avatars)

		self.vars_regex = re.compile(r"\$\{(.+?)\}")

	def get_action_queue_string(self) -> str:
		return str(self.action_queue)
	
	def get_variable(self, name: str):
		self.database_cursor.execute("SELECT value FROM variables WHERE name = ?", (name,))
		result = self.database_cursor.fetchone()
		return result[0] if result != None else None
		
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
		self.database_cursor.execute("SELECT COUNT(*) FROM first_counts WHERE username = ?", (username,))
		count = self.database_cursor.fetchone()[0]
		if count > 0:
			self.database_cursor.execute("UPDATE first_counts SET count = count + 1 WHERE username = ?", (username,))
		else:
			self.database_cursor.execute("INSERT INTO first_counts VALUES (?, 1)", (username,))

		self.database.commit()

	def get_current_chatter_form(self, username: str) -> str:
		self.database_cursor.execute("SELECT form FROM chatter_forms_current WHERE username = ?", (username,))
		return self.database_cursor.fetchone()[0]

	def set_current_chatter_form(self, username: str, form: str):
		self.database_cursor.execute("UPDATE chatter_forms_current SET form = ? WHERE username = ?", (form, username))
		self.database.commit()

	def update_tail_length(self, username: str, amount: int):
		self.database_cursor.execute("UPDATE tirga_tail_lengths SET length = length + ? WHERE username = ?", (amount, username))
		self.database.commit()

	def queue_random_avatars(self, avatars: dict):
		self.random_avatars = [av for av in avatars.values() if av["allow_random"]]
		random.shuffle(self.random_avatars)

	def has_greeting_been_said(self, username: str) -> bool:
		self.database_cursor.execute("SELECT COUNT(*) FROM greetings_said WHERE name = ?", (username,))
		return self.database_cursor.fetchone()[0] > 0
	
	def add_greeting_said(self, username: str):
		self.database_cursor.execute("INSERT INTO greetings_said VALUES (?)", (username,))
		self.database.commit()

	def clear_greetings_said(self):
		self.database_cursor.execute("DELETE FROM greetings_said")
		self.database.commit()

	def get_last_start_time(self) -> datetime.datetime:
		self.database_cursor.execute("SELECT value FROM variables WHERE name = 'last_start_time'")
		string = self.database_cursor.fetchone()[0]
		return datetime.datetime.fromisoformat(string)

	def update_last_start_time(self):
		self.database_cursor.execute("UPDATE variables SET value = ? WHERE name = 'last_start_time'", (datetime.datetime.now().isoformat(),))
		self.database.commit()

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
