import json
import logging
import random
import subprocess

import twitchio
from twitchio import eventsub
from twitchio.ext import commands

from bot_data import BotData
from commands_rules import CommandsRules
from commands_donos import CommandsDonos
from commands_misc import CommandsMisc
from commands_characters import CommandsCharacters

bot_secrets = open("secrets.json", encoding="utf8")
bot_secrets_json = json.load(bot_secrets)
CLIENT_ID = bot_secrets_json["client_id"]
CLIENT_SECRET = bot_secrets_json["client_secret"]
BOT_ID = bot_secrets_json["bot_id"]
OWNER_ID = bot_secrets_json["owner_id"]
bot_secrets.close()

config_data = open("config.json", encoding="utf8")
config_data_json = json.load(config_data)
VEADOTUBE_PATH = config_data_json["veadotube_path"]
config_data.close()

avatars_file = open("avatars.json", encoding="utf8")
AVATARS = json.load(avatars_file)
avatars_file.close()

redeem_ids_file = open("redeems.json", encoding="utf8")
REDEEMS = json.load(redeem_ids_file)
redeem_ids_file.close()

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
		payload_chatmessage = eventsub.ChatMessageSubscription(broadcaster_user_id=self.owner_id, user_id=self.bot_id)
		payload_channelpoints = eventsub.ChannelPointsRedeemAddSubscription(broadcaster_user_id=self.owner_id)
		payload_hypetrain_progress = eventsub.HypeTrainProgressSubscription(broadcaster_user_id=self.owner_id)
		payload_hypetrain_end = eventsub.HypeTrainEndSubscription(broadcaster_user_id=self.owner_id)
		await self.subscribe_websocket(payload=payload_chatmessage)
		await self.subscribe_websocket(payload=payload_channelpoints)
		await self.subscribe_websocket(payload=payload_hypetrain_progress)
		await self.subscribe_websocket(payload=payload_hypetrain_end)

		await self.add_component(CommandsRules(self.bot_data))
		await self.add_component(CommandsChat(self, self.bot_data))
		await self.add_component(CommandsDonos(self.bot_data))
		await self.add_component(CommandsMisc(self.bot_data))
		await self.add_component(CommandsCharacters(self.bot_data))
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

	@commands.Component.listener()
	async def event_custom_redemption_add(self, payload: twitchio.ChannelPointsRedemptionAdd):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		if self.bot_data.silly_mode:
			for redeem in REDEEMS:
				if redeem["silly"]:
					new_cost = random.randrange(2, 1000)
					await user.update_custom_reward(redeem["id"], cost=new_cost)

		if payload.reward.title in AVATARS:
			avatar_info = AVATARS[payload.reward.title]
			avatar_name = payload.reward.title
			if avatar_name == "Kat Avatar":
				self.bot_data.avatar = random.choices(["katMale", "katFemale", "katNanite"], weights=[90, 90, 20], k=1)[0]
			elif avatar_name == "Gremlin":
				if self.bot_data.avatar == "dragonSmall" or self.bot_data.avatar == "dragonOverload" or self.bot_data.avatar == "dragonMacro":
					self.bot_data.avatar = "gremlinDragon"
				else:
					self.bot_data.avatar = "gremlinSphinx"
			else:
				self.bot_data.avatar = avatar_info["veadotube_name"]

			subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents avatarSwap set "{self.bot_data.avatar}"')   
		elif payload.reward.title == "Memory Leak":
			self.bot_data.silly_mode ^= True
			await user.send_message(sender=self.bot.user, message=f"Silly Mode {'activated' if self.bot_data.silly_mode else 'deactivated'}") # type: ignore

	@commands.Component.listener()
	async def event_hype_train_progress(self, payload: twitchio.HypeTrainProgress):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		if payload.level > self.bot_data.current_hype_level:
			if payload.level == 1:
				await user.update_custom_reward(REDEEMS["HypeDragon1"], enabled=True)
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 1 unlocked.") # type: ignore
			elif payload.level == 2:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 1 unlocked for rest of stream.") # type: ignore
			elif payload.level == 3:
				await user.update_custom_reward(REDEEMS["HypeDragon3"], enabled=True)
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 3 unlocked.") # type: ignore
			elif payload.level == 4:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 3 unlocked for rest of stream.") # type: ignore
			elif payload.level == 5:
				await user.update_custom_reward(REDEEMS["HypeDragon5"], enabled=True)
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 5 unlocked.") # type: ignore
			elif payload.level >= 6:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 5 unlocked for rest of stream.") # type: ignore

			self.bot_data.current_hype_level = payload.level
			self.bot_data.highest_hype_level = payload.level

	@commands.Component.listener()
	async def event_hype_train_end(self, payload: twitchio.HypeTrainEnd):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		if self.bot_data.highest_hype_level < 6:
			await user.update_custom_reward(REDEEMS["HypeDragon5"], enabled=False)
			if self.bot_data.current_hype_level > 4:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 5 disabled.") # type: ignore

		if self.bot_data.highest_hype_level < 4:
			await user.update_custom_reward(REDEEMS["HypeDragon3"], enabled=False)
			if self.bot_data.current_hype_level > 2:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 3 disabled.") # type: ignore

		if self.bot_data.highest_hype_level < 2:
			await user.update_custom_reward(REDEEMS["HypeDragon1"], enabled=False)
			if self.bot_data.current_hype_level > 0:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 1 disabled.") # type: ignore

		self.bot_data.current_hype_level = 0


	@commands.command(aliases=["so"])
	async def shoutout(self, context: commands.Context):
		if context.author.moderator or context.author.broadcaster:	 # type: ignore
			whom = context.message.text.split()[1] # type: ignore
			user = self.bot.create_partialuser(user_id=OWNER_ID)
			await user.send_shoutout(to_broadcaster=whom, moderator=context.author)
			
			