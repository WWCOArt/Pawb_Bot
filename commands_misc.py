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
	async def undocount(self, context: commands.Context):
		await context.send(f"Sierra has pressed ctrl+z {self.bot_data.undo_count} times this stream.")

	@commands.command()
	async def throne(self, context: commands.Context):
		if random.binomialvariate(p=0.167):
			await context.send("Runary's wishlist can be viewed at: https://throne.com/runary")
		else:
			await context.send("Sierra's wishlist can be viewed at: https://throne.com/whenwolvescryout")

	@commands.command()
	async def cc(self, context: commands.Context):
		await context.send("If you use OBS Studio for streaming, I highly recommend checking out RatWithACompiler's captions plugin. Setup is basically drag and drop, and doesn't require you to have a separate window open while streaming. https://github.com/ratwithacompiler/OBS-captions-plugin")

	@commands.command()
	async def bleen(self, context: commands.Context):
		await context.reply("What are you doing?? You're going to attract the Runary!")

	@commands.command()
	async def scronch(self, context: commands.Context):
		current_count = self.bot_data.get_variable("scronch_count")
		self.bot_data.store_variable("scronch_count", current_count + 1)
		await context.send(f"A foxbird has been observed scronching {current_count + 1} times.")

	@commands.command()
	async def CHOMP(self, context: commands.Context):
		if context.author.name == "runary":
			self.bot_data.best_button_broken = True
			await context.send("The best button has been chomped and is now broken! :c")
			await asyncio.sleep(600)
			self.bot_data.best_button_broken = False
			await context.send("The best button has been repaired! c:")
