import json
import requests
from twitchio.ext import commands

from bot_data import BotData

class CommandsDonos(commands.Component):
	def __init__(self, bot_data: BotData):
		self.bot_data = bot_data

	@commands.command()
	async def kofi(self, context: commands.Context):
		await context.send("")

	@commands.command()
	async def queue(self, context: commands.Context):
		secrets_file = open("secrets.json", encoding="utf8")
		secrets = json.load(secrets_file)
		secrets_file.close()

		api_url = f"https://api.trello.com/1/lists/{secrets["trello_queue_list"]}/cards"
		query = {
			"key": secrets["trello_api_key"],
			"token": secrets["trello_api_token"],
		}

		response = requests.get(
			api_url,
			headers={"Accept": "application/json"},
			params=query,
		)

		queue_list = json.loads(response.text)
		queue_names = [card["name"] for card in queue_list]
		await context.reply(f"Here is the current queue: {','.join(queue_names)}")

	@commands.command(aliases=["cooldown"])
	async def donocheck(self, context: commands.Context):
		pass
