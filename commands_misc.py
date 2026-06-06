import random
import asyncio
from twitchio.ext import commands

from bot_data import BotData
from utility_functions import send_message_context

class CommandsMisc(commands.Component):
	def __init__(self, bot_data: BotData):
		self.bot_data = bot_data

	@commands.command()
	async def lurk(self, context: commands.Context):
		await send_message_context(context, f"{context.author.display_name} is taking a reading break. Thank you for the lurk!")

	@commands.command()
	async def unlurk(self, context: commands.Context):
		await send_message_context(context, f"Welcome back, {context.author.display_name}! Hope your break went well!")

	@commands.command(aliases=["distraction"])
	async def distracted(self, context: commands.Context):
		new_count = (self.bot_data.get_variable("distracted_count") or 0) + 1
		await send_message_context(context, f"Sierra has been distracted at least {new_count} time{"s" if new_count != 1 else ""} this stream.")
		self.bot_data.store_variable("distracted_count", new_count)

	@commands.command()
	async def undocount(self, context: commands.Context):
		await send_message_context(context, f"Sierra has pressed Ctrl+Z {self.bot_data.get_variable("undo_count")} times this stream.")

	@commands.command()
	async def throne(self, context: commands.Context):
		if random.binomialvariate(p=0.167):
			await send_message_context(context, "Runary's wishlist can be viewed at: https://throne.com/runary")
		else:
			await send_message_context(context, "Sierra's wishlist can be viewed at: https://throne.com/whenwolvescryout")

	@commands.command(aliases=["watch_together", "watch2gether", "watch_2_gether", "w2g"])
	async def watchtogether(self, context: commands.Context):
		await send_message_context(context, "The Library Watch2Gether is at: https://w2g.tv/?r=jmid672vy4qn35p0tc")

	@commands.command()
	async def cc(self, context: commands.Context):
		await send_message_context(context, "If you use OBS Studio for streaming, I highly recommend checking out RatWithACompiler's captions plugin. Setup is basically drag and drop, and doesn't require you to have a separate window open while streaming. https://github.com/ratwithacompiler/OBS-captions-plugin")

	@commands.command()
	async def bleen(self, context: commands.Context):
		await send_message_context(context, "What are you doing?? You're going to attract the Runary!", reply=True)

	@commands.command()
	async def scronch(self, context: commands.Context):
		current_count = self.bot_data.get_variable("scronch_count") or 0
		self.bot_data.increment_variable("scronch_count")
		await send_message_context(context, f"A foxbird has been observed scronching {current_count + 1} times.")

	@commands.command()
	async def CHOMP(self, context: commands.Context):
		if context.author.name == "runary" and not self.bot_data.best_button_broken:
			self.bot_data.best_button_broken = True
			await send_message_context(context, "The best button has been chomped and is now broken! :c")
			await asyncio.sleep(600)
			self.bot_data.best_button_broken = False
			await send_message_context(context, "The best button has been repaired! c:")

	@commands.command(aliases=["diane"])
	async def fractaldiane(self, context: commands.Context):
		await send_message_context(context, "Diane (They/She) is the grey familiar with the flower crown. She makes wonderful music and has contributed many songs to the stream including the ending themes, and any of the character themes you hear. Her music can be found at https://soundcloud.com/fractal-diane. She has also helped significantly in the creation of this bot.")

	@commands.command(aliases=["flo", "fwo"])
	async def flomuffin(self, context: commands.Context):
		await send_message_context(context, "Flomuffin (She/Pup) is Sierra's little sister. She is most often seen on the stream as a white spring wolf, or a gargoyle. She streams as well at https://twitch.tv/flomuffin")

	@commands.command(aliases=["games","distractions"])
	async def powerword(self, context: commands.Context):
		await send_message_context(context, "Available options for Powerword Distraction: Tetris Effect, Not Tetris 2, Sand Tetris, Broomsweeper, Raccooin, Suborbital Salvage, Pinball, Wireworks, Distance, Stackflow , Peglin, Race the Sun, Super hexagon, Gambonanza, Shotgun King.")

	# @commands.command()
	# async def tirgatail(self, context: commands.Context):
	# 	self.bot_data.database_cursor.execute("SELECT length FROM tirga_tail_lengths WHERE username = ?", (context.author.name)) # type: ignore
	# 	your_length = self.bot_data.database_cursor.fetchone()
	# 	your_length = 10 if your_length == None else your_length[0]

	# 	self.bot_data.database_cursor.execute("SELECT length FROM tirga_tail_lengths WHERE username = 'tirgathemadcat'")
	# 	tirgas_length = self.bot_data.database_cursor.fetchone()[0]

	# 	is_steal = random.binomialvariate(p=0.5)
	# 	length_change = max(random.randrange(-20, 20) * your_length / 100, 10) * (-1 if is_steal else 1)
	# 	new_tirgas_length = tirgas_length + length_change
	# 	new_your_length = your_length - length_change

	# 	self.bot_data.database_cursor.execute("UPDATE tirga_tail_lengths SET length = ? WHERE username = ?", (new_your_length, context.author.name))
	# 	self.bot_data.database_cursor.execute("UPDATE tirga_tail_lengths SET length = ? WHERE username = 'tirgathemadcat'", (new_tirgas_length))

	# 	await send_message_context(context, f"{context.author.display_name} has {'stolen' if is_steal else 'gifted'} {abs(length_change)} cm {'from' if is_steal else 'to'} TirgaTheMadCat's tail! And her tail is now {new_tirgas_length} cm long!")
