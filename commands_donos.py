import json
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
		with open("queue.json", encoding="utf8") as queue_file:
			queue = json.load(queue_file)
			await context.reply(f"Here is the current queue: {', '.join(queue)}")

	@commands.command(aliases=["cooldown"])
	async def donocheck(self, context: commands.Context):
		with open("dono_cooldowns.json", encoding="utf8") as cooldown_file:
			cooldowns: dict = json.load(cooldown_file)
			cooldown = cooldowns.get(context.author.display_name, 0)
			if cooldown != 0:
				await context.send(f"{context.author.display_name}, you currently have {cooldown} days until you may get a dono at any price.")
			else:
				await context.send(f"{context.author.display_name}, you may currently get a dono at any price.")
				