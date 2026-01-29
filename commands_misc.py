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
		self.bot_data.increment_variable("scronch_count")
		await context.send(f"A foxbird has been observed scronching {current_count + 1} times.")

	@commands.command()
	async def CHOMP(self, context: commands.Context):
		if context.author.name == "runary":
			self.bot_data.best_button_broken = True
			await context.send("The best button has been chomped and is now broken! :c")
			await asyncio.sleep(600)
			self.bot_data.best_button_broken = False
			await context.send("The best button has been repaired! c:")

	@commands.command()
	async def tirgatail(self, context: commands.Context):
		self.bot_data.database_cursor.execute("SELECT length FROM tirga_tail_lengths WHERE username = ?", (context.author.name)) # type: ignore
		your_length = self.bot_data.database_cursor.fetchone()
		your_length = 10 if your_length == None else your_length[0]

		self.bot_data.database_cursor.execute("SELECT length FROM tirga_tail_lengths WHERE username = 'tirgathemadcat'")
		tirgas_length = self.bot_data.database_cursor.fetchone()[0]

		is_steal = random.binomialvariate(p=0.5)
		length_change = max(random.randrange(-20, 20) * your_length / 100, 10) * (-1 if is_steal else 1)
		new_tirgas_length = tirgas_length + length_change
		new_your_length = your_length - length_change

		self.bot_data.database_cursor.execute("UPDATE tirga_tail_lengths SET length = ? WHERE username = ?", (new_your_length, context.author.name))
		self.bot_data.database_cursor.execute("UPDATE tirga_tail_lengths SET length = ? WHERE username = 'tirgathemadcat'", (new_tirgas_length))

		await context.send(f"{context.author.display_name} has {'stolen' if is_steal else 'gifted'} {abs(length_change)} cm {'from' if is_steal else 'to'} TirgaTheMadCat's tail! And her tail is now {new_tirgas_length} cm long!")
