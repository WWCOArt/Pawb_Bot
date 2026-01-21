import json

class BotData():
	def __init__(self):
		self.bless_count = 0
		self.distracted_count = 0
		self.silly_mode = False
		self.avatar = "sphinx"
		self.current_hype_level = 0
		self.highest_hype_level = 0

		with open("foxrules.json", encoding="utf8") as foxrules_file:
			self.foxrules = json.load(foxrules_file)
	