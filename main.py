import asyncio
import aioconsole
import logging

import twitchio
from twitchio import eventsub
from twitchio.ext import commands

import bot

def main() -> None:
	b = bot.Bot()
	# Setup logging, this is optional, however a nice to have...
	twitchio.utils.setup_logging(level=logging.INFO)

	async def runner() -> None:
		async with b as bot:
			await bot.start()

	async def console() -> None:
		while True:
			console_input = await aioconsole.ainput()
			b.process_input(console_input)

	try:
		asyncio.get_event_loop().run_until_complete(asyncio.wait([
			runner(),
			console(),
		])) # type: ignore

		bot.randomize_connection_offline.start()
	except KeyboardInterrupt:
		bot.LOGGER.warning("Shutting down due to Keyboard Interrupt...")

if __name__ == "__main__":
	main()
