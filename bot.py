import json
import logging
import random
import subprocess
import datetime
import keyboard

import twitchio
from twitchio import eventsub
from twitchio.ext import commands, routines

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

with open("config.json", encoding="utf8") as config_data:
	config_data_json = json.load(config_data)
	VEADOTUBE_PATH = config_data_json["veadotube_path"]

with open("avatars.json", encoding="utf8") as avatars_file:
	AVATARS = json.load(avatars_file)

with open("redeems.json", encoding="utf8") as redeem_ids_file:
	REDEEMS = json.load(redeem_ids_file)

with open("greetings.json", encoding="utf8") as greetings_file:
	GREETINGS = json.load(greetings_file)

LOGGER: logging.Logger = logging.getLogger("Bot")

class Bot(commands.Bot):
	def __init__(self) -> None:
		self.bot_data = BotData(AVATARS)
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

		user = self.create_partialuser(user_id=OWNER_ID)
		await user.send_message(sender=self.user, message="PawbOS 2.0 booting up.") # type: ignore

		rewards = await user.fetch_custom_rewards(ids=["d4169fc0-17a8-447b-92da-3b928f75caa2"])
		power_word_tetris_reward = rewards[0]
		new_power_word_tetris = await user.create_custom_reward(
			title=power_word_tetris_reward.title,
			prompt=power_word_tetris_reward.prompt,
			cost=power_word_tetris_reward.cost,
			background_color=power_word_tetris_reward.color,
			global_cooldown=power_word_tetris_reward.cooldown.seconds,
		)

		await user.update_custom_reward(new_power_word_tetris.id, cost=25001)

		#await user.update_custom_reward(REDEEMS["First!"]["id"], title="First!", prompt="Show everyone you were the fastest.")

		keyboard.add_hotkey("ctrl+z", increment_undo, args=[self]) # type: ignore

		LOGGER.info("Finished setup hook!")

	async def close(self, **options):
		self.bot_data.database.close()

		user = self.create_partialuser(user_id=OWNER_ID)
		await user.send_message(sender=self.user, message="PawbOS 2.0 shutting down.") # type: ignore

		await super().close(**options)

	def process_input(self, inp: str):
		print(inp)

class CommandsChat(commands.Component):
	def __init__(self, bot: Bot, bot_data: BotData):
		self.bot = bot
		self.bot_data = bot_data

	async def avatar_transition(self, avatar: str, is_switched_to: bool):
		redeems_disabled = AVATARS[avatar]["disable_redeems"]
		redeems_enabled = AVATARS[avatar]["enable_redeems"]

		user = self.bot.create_partialuser(user_id=OWNER_ID)
		for redeem in redeems_disabled:
			await user.update_custom_reward(REDEEMS[redeem]["id"], enabled=not is_switched_to)
		
		for redeem in redeems_enabled:
			await user.update_custom_reward(REDEEMS[redeem]["id"], enabled=is_switched_to)

	async def update_redeem_availability(self, previous_avatar: str, new_avatar: str):
		await self.avatar_transition(previous_avatar, False)
		await self.avatar_transition(new_avatar, True)

	@commands.Component.listener()
	async def event_message(self, payload: twitchio.ChatMessage):
		if payload.chatter.user == self.bot.user:
			return
		
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		if payload.chatter.name == "thezaffrehammer" and "bless" in payload.text.lower():
			self.bot_data.bless_count += 1

		if payload.chatter.name in GREETINGS and not payload.chatter.name in self.bot_data.greetings_said:
			if isinstance(GREETINGS[payload.chatter.name], str): # string = single greeting
				await user.send_message(sender=self.bot.user, message=self.bot_data.replace_vars_in_string(GREETINGS[payload.chatter.name])) # type: ignore
			elif isinstance(GREETINGS[payload.chatter.name], list): # list = randomly pick from multiple greetings
				await user.send_message(sender=self.bot.user, message=self.bot_data.replace_vars_in_string(random.choice(GREETINGS[payload.chatter.name]))) # type: ignore
			else: # dictionary = pick greeting based on form
				await user.send_message(sender=self.bot.user, message=self.bot_data.replace_vars_in_string(GREETINGS[payload.chatter.name][self.bot_data.get_current_chatter_form(payload.chatter.name)]["greeting"])) # type: ignore

			self.bot_data.greetings_said.add(payload.chatter.name)

	@commands.Component.listener()
	async def event_custom_redemption_add(self, payload: twitchio.ChannelPointsRedemptionAdd):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		if self.bot_data.silly_mode:
			for redeem in REDEEMS.values():
				if redeem["silly"]:
					new_cost = random.randrange(2, 999)
					await user.update_custom_reward(redeem["id"], cost=new_cost)

		if payload.reward.title in AVATARS:
			previous_avatar = self.bot_data.avatar
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
			await self.update_redeem_availability(previous_avatar, self.bot_data.avatar)
		elif payload.reward.id == REDEEMS["Random Avatar"]["id"]:
			previous_avatar = self.bot_data.avatar
			self.bot_data.avatar = self.bot_data.random_avatars.pop()["veadotube_name"]
			if len(self.bot_data.random_avatars) == 0:
				self.bot_data.queue_random_avatars(AVATARS)

			subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents avatarSwap set "{self.bot_data.avatar["veadotube_name"]}"')
			await user.send_message(sender=self.bot.user, message=self.bot_data.replace_vars_in_string(avatar["description"])) # type: ignore
			await self.update_redeem_availability(previous_avatar, self.bot_data.avatar)
		elif payload.reward.title == REDEEMS["Memory Leak"]["id"]:
			self.bot_data.silly_mode ^= True
			for redeem in REDEEMS.values():
				if redeem["silly"]:
					await user.update_custom_reward(redeem["id"], cost=random.randrange(2, 999) if self.bot_data.silly_mode else redeem["base_price"])

			await user.send_message(sender=self.bot.user, message=f"Silly Mode {'activated' if self.bot_data.silly_mode else 'deactivated'}") # type: ignore
		elif payload.reward.title == REDEEMS["This Redeem does nothing"]["id"]:
			nothing_cost = self.bot_data.get_variable("nothing_cost")
			self.bot_data.store_variable("nothing_cost", nothing_cost + 1)
			await user.update_custom_reward(REDEEMS["This Redeem does nothing"]["id"], cost=nothing_cost)
		elif payload.reward.title == REDEEMS["Create a Fox Rule!"]["id"]:
			self.bot_data.add_foxrule(payload.user.display_name, payload.user_input) # type: ignore
			await user.send_message(sender=self.bot.user, message="Fox Rules have been updated!") # type: ignore
		elif payload.reward.title == REDEEMS["First!"]["id"]:
			self.bot_data.increment_first_count(payload.user.name) # type: ignore
			await user.update_custom_reward(REDEEMS["First!"]["id"], title=f"{payload.user.display_name} was first this stream!", prompt=f"They've been first {self.bot_data.get_first_count(payload.user.name)} times!") # type: ignore

	@commands.Component.listener()
	async def event_hype_train_progress(self, payload: twitchio.HypeTrainProgress):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		if payload.level > self.bot_data.current_hype_level:
			if payload.level == 1:
				await user.update_custom_reward(REDEEMS["HypeDragon1"]["id"], enabled=True)
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 1 unlocked.") # type: ignore
			elif payload.level == 2:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 1 unlocked for rest of stream.") # type: ignore
			elif payload.level == 3:
				await user.update_custom_reward(REDEEMS["HypeDragon3"]["id"], enabled=True)
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 3 unlocked.") # type: ignore
			elif payload.level == 4:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 3 unlocked for rest of stream.") # type: ignore
			elif payload.level == 5:
				await user.update_custom_reward(REDEEMS["HypeDragon5"]["id"], enabled=True)
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 5 unlocked.") # type: ignore
			elif payload.level >= 6:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 5 unlocked for rest of stream.") # type: ignore

			self.bot_data.current_hype_level = payload.level
			self.bot_data.highest_hype_level = payload.level

	@commands.Component.listener()
	async def event_hype_train_end(self, payload: twitchio.HypeTrainEnd):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		if self.bot_data.highest_hype_level < 6:
			await user.update_custom_reward(REDEEMS["HypeDragon5"]["id"], enabled=False)
			if self.bot_data.current_hype_level > 4:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 5 disabled.") # type: ignore

		if self.bot_data.highest_hype_level < 4:
			await user.update_custom_reward(REDEEMS["HypeDragon3"]["id"], enabled=False)
			if self.bot_data.current_hype_level > 2:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 3 disabled.") # type: ignore

		if self.bot_data.highest_hype_level < 2:
			await user.update_custom_reward(REDEEMS["HypeDragon1"]["id"], enabled=False)
			if self.bot_data.current_hype_level > 0:
				await user.send_message(sender=self.bot.user, message="Hype Dragon Level 1 disabled.") # type: ignore

		self.bot_data.current_hype_level = 0

	@commands.command(aliases=["so"])
	async def shoutout(self, context: commands.Context):
		if context.author.moderator or context.author.broadcaster:	 # type: ignore
			whom = context.message.text.split()[1] # type: ignore
			user = self.bot.create_partialuser(user_id=OWNER_ID)
			await user.send_shoutout(to_broadcaster=whom, moderator=context.author)

@routines.routine(delta=datetime.timedelta(seconds=2))
async def randomize_connection_offline(bot: Bot):
	user = bot.create_partialuser(user_id=OWNER_ID)
	#await user.update_custom_reward(REDEEMS["ConnectionOffline"]["id"], cost=random.randint(100000000, 999999999))

def increment_undo(bot: Bot):
	bot.bot_data.undo_count += 1
