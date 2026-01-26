import random
import asyncio
from twitchio.ext import commands

from bot_data import BotData

class CommandsRules(commands.Component):
	def __init__(self, bot_data: BotData):
		self.bot_data = bot_data

	@commands.command()
	async def foxrule(self, context: commands.Context):
		rule = self.bot_data.get_foxrule()
		await context.send(rule["rule"])

	@commands.command()
	async def foxrulecount(self, context: commands.Context):
		message_text = f"There are currently {"1" * len(self.bot_data.foxrules)} Fox Rules."
		for slic in [message_text[i:i + 500] for i  in range(0, len(message_text), 500)]: # evil magic to divide it into 500-character chunks
			await context.send(slic)

	@commands.command()
	async def runaryrule(self, context: commands.Context):
		await context.send("Thank you for all that you do, Runary.")

	@commands.command(aliases=["cerbirule"])
	async def malrule(self, context: commands.Context):
		await context.send("The Cerbi is a very good boy.")

	@commands.command()
	async def petcerbi(self, context: commands.Context):
		await context.send("Cerbi has been pet!")

	@commands.command()
	async def saberrule(self, context: commands.Context):
		await context.send("Do you ever wonder how it feels to have beans like Saber? The texture of them on objects? Think about it.")

	@commands.command()
	async def florule(self, context: commands.Context):
		await context.send("There are no Flo Rules. Flo is unstoppable.")

	@commands.command()
	async def tangentrule(self, context: commands.Context):
		await context.send("If you hug a Tangent tight enough...")

	@commands.command()
	async def kapolrule(self, context: commands.Context):
		await context.send("Everything's fine. It's just that... where there was previously a small red panda, is now a tall golden kitsune. But such changes are pretty normal here. Probably don't ask her for advice.")

	@commands.command()
	async def zaffrerule(self, context: commands.Context):
		await context.send(f"Zaffre has said Bless {self.bot_data.bless_count} times this stream.")

	@commands.command()
	async def displacerrule(self, context: commands.Context):
		await context.send(f"{context.author.display_name}, did you just try that because you saw it on Sammi?")
		await asyncio.sleep(300)
		await context.reply("Displacer Rule: Displacer Beasts are never where you expect them to be. Same for their rules.")
