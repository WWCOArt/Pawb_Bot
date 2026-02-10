import json
import requests
from twitchio.ext import commands

import trello
from bot_data import BotData

class CommandsDonos(commands.Component):
	def __init__(self, bot_data: BotData):
		self.bot_data = bot_data

	@commands.command()
	async def kofi(self, context: commands.Context):
		await context.send("https://ko-fi.com/whenwolvescryout/commissions")

	@commands.command()
	async def queue(self, context: commands.Context):
		queue_list = trello.get_trello_queue()
		queue_names = [card["name"] for card in queue_list]
		await context.reply(f"Here's the current queue: {', '.join(queue_names)}")

	@commands.command(aliases=["cooldown", "dono", "donos"])
	async def donocheck(self, context: commands.Context):
		pass
