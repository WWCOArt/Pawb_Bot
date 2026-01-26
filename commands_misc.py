import random
import asyncio
from twitchio.ext import commands

from bot_data import BotData

class CommandsMisc(commands.Component):
	def __init__(self, bot_data: BotData):
		self.bot_data = bot_data

	@commands.command()
	async def lurk(self, context: commands.Context):
		await context.send(f"{context.author.display_name} is taking a reading break. Thank you for the lurk!")

	@commands.command()
	async def unlurk(self, context: commands.Context):
		await context.send(f"Welcome back, {context.author.display_name}! Hope your break went well!")

	@commands.command()
	async def distracted(self, context: commands.Context):
		self.bot_data.distracted_count += 1
		await context.send(f"Sierra has been distracted {self.bot_data.distracted_count} time{"s" if self.bot_data.distracted_count != 1 else ""} this stream.")

	@commands.command()
	async def throne(self, context: commands.Context):
		await context.send("")

	@commands.command()
	async def CHOMP(self, context: commands.Context):
		if context.author.name == "runary":
			self.bot_data.best_button_broken = True
			await context.send("The best button has been chomped and is now broken! :c")
			await asyncio.sleep(600)
			self.bot_data.best_button_broken = False
			await context.send("The best button has been repaired! c:")
