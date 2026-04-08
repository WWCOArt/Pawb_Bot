import json
import requests
from twitchio.ext import commands

import trello
from bot_data import BotData
from utility_functions import send_message_context

class CommandsDonos(commands.Component):
	def __init__(self, bot_data: BotData):
		self.bot_data = bot_data

	@commands.command(aliases=["dono", "donos"])
	async def kofi(self, context: commands.Context):
		await send_message_context(context, "https://ko-fi.com/whenwolvescryout/commissions")

	@commands.command()
	async def queue(self, context: commands.Context):
		queue_list = trello.get_trello_queue()
		queue_names = [card["name"] for card in queue_list]
		await send_message_context(context, f"Here's the current queue: {', '.join(queue_names)}", reply=True)

	@commands.command(aliases=["cooldown"])
	async def donocheck(self, context: commands.Context):
		pass
