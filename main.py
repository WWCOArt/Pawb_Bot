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

	try:
		asyncio.run(runner())
		bot.randomize_connection_offline.start()
	except KeyboardInterrupt:
		bot.LOGGER.warning("Shutting down due to Keyboard Interrupt...")

if __name__ == "__main__":
	main()
