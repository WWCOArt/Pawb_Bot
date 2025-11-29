import random
import asyncio
from twitchio.ext import commands

from bot_data import BotData

class CommandsMisc(commands.Component):
	def __init__(self, bot_data: BotData):
		self.bot_data = bot_data

	@commands.command()
	async def distracted(self, context: commands.Context):
		self.bot_data.distracted_count += 1
		await context.send(f"Sierra has been distracted {self.bot_data.distracted_count} time{"s" if self.bot_data.distracted_count != 1 else ""} this stream.")

	@commands.command()
	async def throne(self, context: commands.Context):
		await context.send("")
