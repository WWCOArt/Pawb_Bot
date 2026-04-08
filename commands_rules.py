import random
import asyncio
from twitchio.ext import commands

from bot_data import BotData
from utility_functions import send_message_context

class CommandsRules(commands.Component):
	def __init__(self, bot_data: BotData):
		self.bot_data = bot_data

	@commands.command(aliases=["foxrules"])
	async def foxrule(self, context: commands.Context):
		rule = self.bot_data.get_foxrule()
		await send_message_context(context, rule)

	@commands.command()
	async def foxrulecount(self, context: commands.Context):
		message_text = f"There are currently {"1" * self.bot_data.get_foxrule_count()} Fox Rules."
		for slic in [message_text[i:i + 500] for i  in range(0, len(message_text), 500)]: # evil magic to divide it into 500-character chunks
			await send_message_context(context, slic)

	@commands.command()
	async def runaryrule(self, context: commands.Context):
		await send_message_context(context, "Thank you for all that you do, Runary.")

	@commands.command(aliases=["cerbirule"])
	async def malrule(self, context: commands.Context):
		await send_message_context(context, "The Cerbi is a very good boy.")

	@commands.command()
	async def petcerbi(self, context: commands.Context):
		await send_message_context(context, "Cerbi has been pet!")

	@commands.command()
	async def saberrule(self, context: commands.Context):
		await send_message_context(context, "Do you ever wonder how it feels to have beans like Saber? The texture of them on objects? Think about it.")

	@commands.command()
	async def florule(self, context: commands.Context):
		await send_message_context(context, "There are no Flo Rules. Flo is unstoppable.")

	@commands.command()
	async def tangentrule(self, context: commands.Context):
		await send_message_context(context, "If you hug a Tangent tight enough...")

	@commands.command()
	async def kapolrule(self, context: commands.Context):
		await send_message_context(context, "Everything's fine. It's just that... where there was previously a small red panda, is now a tall golden kitsune. But such changes are pretty normal here. Probably don't ask her for advice.")

	@commands.command()
	async def zaffrerule(self, context: commands.Context):
		await send_message_context(context, f"Zaffre has said Bless {self.bot_data.get_variable("bless_count")} times this stream.")

	@commands.command()
	async def displacerrule(self, context: commands.Context):
		await send_message_context(context, f"{context.author.display_name}, did you just try that because you saw it on Sammi?")
		await asyncio.sleep(300)
		await send_message_context(context, "Displacer Rule: Displacer Beasts are never where you expect them to be. Same for their rules.", reply=True)

	@commands.command()
	async def frenrule(self, context: commands.Context):
		await send_message_context(context, "⭕❗️😀🍴")
		