import json
import logging
import random

import twitchio
from twitchio import eventsub
from twitchio.ext import commands

from bot_data import BotData
from commands_rules import CommandsRules
from commands_donos import CommandsDonos
from commands_misc import CommandsMisc

bot_secrets = open("secrets.json", encoding="utf8")
bot_secrets_json = json.load(bot_secrets)
CLIENT_ID = bot_secrets_json["client_id"]
CLIENT_SECRET = bot_secrets_json["client_secret"]
BOT_ID = bot_secrets_json["bot_id"]
OWNER_ID = bot_secrets_json["owner_id"]
bot_secrets.close()

LOGGER: logging.Logger = logging.getLogger("Bot")

class Bot(commands.Bot):
	def __init__(self) -> None:
		self.bot_data = BotData()
		super().__init__(
			client_id=CLIENT_ID,
			client_secret=CLIENT_SECRET,
			bot_id=BOT_ID,
			owner_id=OWNER_ID,
			prefix="!",
			case_insensitive=True
		)

	# Do some async setup, as an example we will load a component and subscribe to some events...
	# Passing the bot to the component is completely optional...
	async def setup_hook(self) -> None:

		# Listen for messages on our channel...
		# You need appropriate scopes, see the docs on authenticating for more info...
		payload = eventsub.ChatMessageSubscription(broadcaster_user_id=self.owner_id, user_id=self.bot_id)
		await self.subscribe_websocket(payload=payload)

		await self.add_component(CommandsRules(self.bot_data))
		await self.add_component(CommandsChat(self, self.bot_data))
		await self.add_component(CommandsDonos(self.bot_data))
		await self.add_component(CommandsMisc(self.bot_data))
		LOGGER.info("Finished setup hook!")

class CommandsChat(commands.Component):
	def __init__(self, bot: Bot, bot_data: BotData):
		self.bot = bot
		self.bot_data = bot_data

	@commands.Component.listener()
	async def event_message(self, payload: twitchio.ChatMessage):
		if payload.chatter.user == self.bot.user:
			return
		
		if "tangent is a fox" in payload.text.lower():
			tangent_form = random.choice([
				"human",
				"kitsune",
				"squirrel",
				"displacer beast",
			])

			user = self.bot.create_partialuser(user_id=OWNER_ID)
			await user.send_message(sender=self.bot.user, message=f"An echo passes through the room. Distance and location unknown. But the sound of a confused {tangent_form} can be heard.") # type: ignore
		
		if payload.chatter.display_name == "TheZaffreHammer" and "bless" in payload.text.lower():
			self.bot_data.bless_count += 1

	@commands.command(aliases=["so"])
	async def shoutout(self, context: commands.Context):
		if context.author.moderator or context.author.broadcaster:	 # type: ignore
			whom = context.message.text.split()[1] # type: ignore
			user = self.bot.create_partialuser(user_id=OWNER_ID)
			await user.send_shoutout(to_broadcaster=whom, moderator=context.author)
			