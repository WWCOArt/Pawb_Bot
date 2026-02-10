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
		bot.randomize_connection_offline.start()
		bot.poll_trello_queue.start()
		asyncio.run(runner())
	except KeyboardInterrupt:
		bot.LOGGER.warning("Shutting down due to Keyboard Interrupt...")

if __name__ == "__main__":
	main()
