import unittest
from unittest.mock import patch

import bot

class TestJsonFunctions(unittest.TestCase):
	@patch("bot.Bot.setup_hook")
	def setUp(self, setup_hook_mock):
		self.bot = bot.Bot()
		self.bot.INTERACT_DURATIONS = {
			"default_headpats": 2.510,
			"default_hug": 2.510,
			"avatars": {
				"bigFox": {
					"headpats": {
						"default": 4.010,
						"__example_user__": 5.000
					}
				}
			}
		}

	def test_interact_duration_avatar_doesnt_exist(self):
		self.assertEqual(self.bot.get_interact_duration(False, "blah", ""), 2.510)
		self.assertEqual(self.bot.get_interact_duration(True, "blah", ""), 2.510)

	def test_interaction_duration_avatar_action_default(self):
		self.assertEqual(self.bot.get_interact_duration(False, "bigFox", ""), 4.010)

	def test_interact_duration_avatar_action_doesnt_exist(self):
		self.assertEqual(self.bot.get_interact_duration(True, "bigFox", ""), 2.510)

	def test_interaction_duration_avatar_user_action(self):
		self.assertEqual(self.bot.get_interact_duration(False, "bigFox", "__example_user__"), 5.000)

	def test_interaction_duration_user_doesnt_exist(self):
		self.assertEqual(self.bot.get_interact_duration(False, "bigFox", "blah"), 4.010)

	def test_interaction_duration_user_empty_action(self):
		self.assertEqual(self.bot.get_interact_duration(True, "bigFox", "blah"), 2.510)
		

if __name__ == "__main__":
	unittest.main()
