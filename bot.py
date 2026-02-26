import json
import logging
import random
import subprocess
import datetime
import keyboard
import asyncio
import re
import requests
from collections import deque

VERSION_NUMBER = "2.0"

import twitchio
from twitchio import eventsub
from twitchio.ext import commands, routines
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

import trello
from bot_data import BotData
from avatar_action import ActionType, AvatarAction
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
CLOUD_WEBHOOK_URL = bot_secrets_json["cloud_webhook_url"]
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

########################################################################################################################

def get_avatar_info_by_veadotube_name(veadotube_name: str) -> dict:
		matches = [av for av in AVATARS.values() if av["veadotube_name"] == veadotube_name]
		return matches[0] if len(matches) > 0 else {}

########################################################################################################################

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
		payload_online = eventsub.StreamOnlineSubscription(broadcaster_user_id=self.owner_id)
		payload_offline = eventsub.StreamOfflineSubscription(broadcaster_user_id=self.owner_id)
		payload_chatmessage = eventsub.ChatMessageSubscription(broadcaster_user_id=self.owner_id, user_id=self.bot_id)
		payload_channelpoints = eventsub.ChannelPointsRedeemAddSubscription(broadcaster_user_id=self.owner_id)
		payload_hypetrain_progress = eventsub.HypeTrainProgressSubscription(broadcaster_user_id=self.owner_id)
		payload_hypetrain_end = eventsub.HypeTrainEndSubscription(broadcaster_user_id=self.owner_id)
		await self.subscribe_websocket(payload=payload_online)
		await self.subscribe_websocket(payload=payload_offline)
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

		#await user.update_custom_reward(REDEEMS["First!"]["id"], title="First!", prompt="Show everyone you were the fastest.")
		#await user.update_custom_reward(REDEEMS["Planks!"]["id"], enabled=False)

		keyboard.add_hotkey("ctrl+z", increment_undo, args=[self]) # type: ignore
		self.bot_data.current_queue_size = len(trello.get_trello_queue())

		self.randomize_connection_offline.start()
		self.poll_trello_queue.start()

		LOGGER.info("Finished setup hook!")

		# streamer command input
		session = PromptSession()
		while True:
			with patch_stdout():
				inp = await session.prompt_async("> ")
				await self.process_input(inp)

	async def shut_down(self):
		self.bot_data.database.close()

	async def process_input(self, inp: str):
		user = self.create_partialuser(user_id=OWNER_ID)

		input_split = inp.split()
		command = input_split[0].lower().lstrip("/! \t")
		if command == "say":
			await user.send_message(sender=self.user, message=" ".join(input_split[1:])) # type: ignore
		elif command == "best" or command == "bestbutton":
			if not self.bot_data.best_button_broken:
				await user.send_announcement(moderator=self.user, message="Go check out the heckin' good bean that is Runary! They stream at https://twitch.tv/Runary, and you can buy their art at https://ko-fi.com/Runary", color="purple") # type: ignore
		elif command == "next":
			requests.post(f"{CLOUD_WEBHOOK_URL}?advance_queue")
			queue = trello.get_trello_queue()
			next_person = queue[0]["name"]
			await user.send_announcement(moderator=self.user, message=f"{next_person} is up!") # type: ignore
			await user.send_whisper(to_user=next_person.lower(), message=f"Sierra is starting on your dono, {next_person}")
		elif command == "avatar":
			if len(input_split) > 1:
				await self.get_component("CommandsChat").queue_action(AvatarAction(ActionType.AVATAR_CHANGE, input_split[1], 2.0)) # type: ignore
			else:
				print('Missing parameters for command "avatar"')
		elif command == "headpats" or command == "hug":
			is_hug = command == "hug"
			all_interact_timings = get_avatar_info_by_veadotube_name(self.bot_data.avatar).get("interact_timings", 2.5)
			this_interact_timings = all_interact_timings if isinstance(all_interact_timings, float) else all_interact_timings.get(command, 2.5)
			duration = this_interact_timings if isinstance(this_interact_timings, float) else this_interact_timings.get(("default", 2.5))
			await self.get_component("CommandsChat").queue_action(AvatarAction(ActionType.HUG if is_hug else ActionType.HEADPATS, self.bot_data.avatar, duration)) # type: ignore
		else:
			print(f'Unknown command "{command}"')

	@routines.routine(delta=datetime.timedelta(seconds=2))
	async def randomize_connection_offline(self):
		user = self.create_partialuser(user_id=OWNER_ID)
		#await user.update_custom_reward(REDEEMS["ConnectionOffline"]["id"], cost=random.randint(100000000, 999999999))

	@routines.routine(delta=datetime.timedelta(seconds=2), wait_first=True)
	async def poll_trello_queue(self):
		user = self.create_partialuser(user_id=OWNER_ID)
		new_queue = trello.get_trello_queue()
		if len(new_queue) != self.bot_data.current_queue_size:
			if len(new_queue) > self.bot_data.current_queue_size:
				latest_donor = new_queue[-1]["name"].split("###")
				if len(latest_donor) > 1:
					if latest_donor[1].isdigit():
						await user.send_message(sender=self.user, message=f"{latest_donor[0]}, you submitted a donation of less than $25, but you currently have a cooldown of {latest_donor[1]} days on getting an under $25 dono. You will be refunded.") # type: ignore
					else:
						await user.send_message(sender=self.user, message=f"{latest_donor[0]}, you are already on the queue. You will be refunded.") # type: ignore
				else:
					await user.send_announcement(moderator=self.user, message=f"{latest_donor[0]} has been added to the queue.", color="orange") # type: ignore

			current_stream_title = (await user.fetch_channel_info()).title
			if "queue size" in current_stream_title:
				await user.modify_channel(title=re.sub(r"\[\d+\]", f"[{len(new_queue)}]", current_stream_title))
				self.bot_data.current_queue_size = len(new_queue)

	@routines.routine(delta=datetime.timedelta(hours=1), iterations=1)
	async def enable_planks(self):
		user = self.create_partialuser(user_id=OWNER_ID)
		#await user.update_custom_reward(REDEEMS["Planks!"]["id"], enabled=True)

########################################################################################################################

class CommandsChat(commands.Component):
	def __init__(self, bot: Bot, bot_data: BotData):
		self.bot = bot
		self.bot_data = bot_data

	async def avatar_transition(self, avatar: str, is_switched_to: bool):
		avatar_info = get_avatar_info_by_veadotube_name(avatar)
		redeems_disabled = avatar_info.get("disable_redeems", [])
		redeems_enabled = avatar_info.get("enable_redeems", [])

		user = self.bot.create_partialuser(user_id=OWNER_ID)
		#for redeem in redeems_disabled:
			#await user.update_custom_reward(REDEEMS[redeem]["id"], enabled=not is_switched_to)
		
		#for redeem in redeems_enabled:
			#await user.update_custom_reward(REDEEMS[redeem]["id"], enabled=is_switched_to)

	async def update_redeem_availability(self, previous_avatar: str, new_avatar: str):
		await self.avatar_transition(previous_avatar, False)
		await self.avatar_transition(new_avatar, True)

	async def advance_action_queue(self):
		action = self.bot_data.action_queue[0]
		if action.type == ActionType.AVATAR_CHANGE:
			previous_avatar = self.bot_data.avatar
			avatar_info = get_avatar_info_by_veadotube_name(action.avatar)
			avatar_name = action.avatar
			if len(avatar_info) > 0:
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
		elif action.type == ActionType.RANDOM_AVATAR:
			previous_avatar = self.bot_data.avatar
			self.bot_data.avatar = self.bot_data.random_avatars.pop()["veadotube_name"]
			if len(self.bot_data.random_avatars) == 0:
				self.bot_data.queue_random_avatars(AVATARS)

			subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents avatarSwap set "{self.bot_data.avatar["veadotube_name"]}"')
			await user.send_message(sender=self.bot.user, message=self.bot_data.replace_vars_in_string(avatar["description"])) # type: ignore
			await self.update_redeem_availability(previous_avatar, self.bot_data.avatar)
		elif action.type == ActionType.HEADPATS:
			pass
		else:
			pass

		await asyncio.sleep(action.duration)
		self.bot_data.action_queue.popleft()
		if len(self.bot_data.action_queue) > 0:
			await self.advance_action_queue()

	async def queue_action(self, action: AvatarAction):
		self.bot_data.action_queue.append(action)
		if len(self.bot_data.action_queue) == 1:
			await self.advance_action_queue()

	####################################################################################################################

	# Stream Startup. Add the following when time permitted:
	# Start 1 hour wait to activate planks ⚠️ (Bot.setup_hook)
	# Set dragonstage to 0 (can we just do a 'pressure reset' function?)
	# Trigger Sphinx Avatar ✅ (this function)
	# Check if first stream for today. 
	# reset the First Redeem ⚠️ (Bot.setup_hook)
	# Future stuff. Set plush to idle. 
	# Start the Searching For connection Redeem. ⚠️ (Bot.setup_hook)
	# Reset the welcome string if first stream of day.
	# disable any active hype dragons. Set current hype level to 0
	# set distraction and undo to 0 ✅ (BotData.__init__)
	# Ask diane if this would be under the same async def above the messages, or in a separate one.
	# Pawb_bot startup messages ✅ (this function)
	@commands.Component.listener()
	async def event_stream_online(self, payload: twitchio.StreamOnline):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		await self.queue_action(AvatarAction(ActionType.AVATAR_CHANGE, "sphinx", 1.0))

		await user.send_message(sender=self.user, message=f"PawbOS v{VERSION_NUMBER} booting up.") # type: ignore
		await asyncio.sleep(0.5)
		await user.send_message(sender=self.user, message="PawbBot terminal online.") # type: ignore
		await asyncio.sleep(0.5)
		await user.send_message(sender=self.user, message="Avatar system online.") # type: ignore
		await asyncio.sleep(1.0)
		await user.send_message(sender=self.user, message="Video feed online.") # type: ignore
		await asyncio.sleep(1.0)
		await user.send_message(sender=self.user, message="Audio feed online.") # type: ignore
		await asyncio.sleep(1.0)
		await user.send_message(sender=self.user, message="Low bandwidth detected. Searching for connection...") # type: ignore

	# pawb_bot shutdown messages
	@commands.Component.listener()
	async def event_stream_offline(self, payload: twitchio.StreamOffline):
		user = self.bot.create_partialuser(user_id=OWNER_ID)
		await user.send_message(sender=self.user, message="PawbOS shutting down.") # type: ignore

	# listening for chat messages
	@commands.Component.listener()
	async def event_message(self, payload: twitchio.ChatMessage):
		if payload.chatter.user == self.bot.user:
			return
		
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		#Zaffre Bless
		if payload.chatter.name == "thezaffrehammer" and "bless" in payload.text.lower():
			self.bot_data.bless_count += 1

		#Runary Yeeting the skunk.
		if payload.chatter.name == "runary" and "yeets the zaffre" in payload.text.lower():
			message = random.choices(list(enumerate([
				"The skunk has been yeeted.",
				"The skunk has been yeeted through a portal.",
				"The skunk has been yeeted through a broken portal.",
				"The skunk has been yeeted into the past.",
				"The skunk has been yeeted into the future.",
				"The skunk has dodged the yeet.",
				"The chimera has been yeeted.",
				"Countered! Zaffre yeets Runary instead!",
				"The skunk has been greeted.",
				"The skunk has been gently tossed about 5 feet.",
				"Runary got too excited and tripped.",
				"7H3 5KUNK H45 B33N Y3373D.",
			])), weights=[30, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], k=1)[0]

			await user.send_message(sender=self.bot.user, message=message[1]) # type: ignore
			if message[0] == 1:
				await asyncio.sleep(120)
				await user.send_message(sender=self.bot.user, message="The skunk has been yeeted out of a portal and lands at runary's feet.") # type: ignore

		# User greetings.
		if payload.chatter.name in GREETINGS and not payload.chatter.name in self.bot_data.greetings_said:
			if payload.chatter.name == "flomuffin":
				self.bot_data.increment_variable("door_count")

			if isinstance(GREETINGS[payload.chatter.name], str): # string = single greeting
				await user.send_message(sender=self.bot.user, message=self.bot_data.replace_vars_in_string(GREETINGS[payload.chatter.name])) # type: ignore
			elif isinstance(GREETINGS[payload.chatter.name], list): # list = randomly pick from multiple greetings
				await user.send_message(sender=self.bot.user, message=self.bot_data.replace_vars_in_string(random.choice(GREETINGS[payload.chatter.name]))) # type: ignore
			else: # dictionary = pick greeting based on form
				await user.send_message(sender=self.bot.user, message=self.bot_data.replace_vars_in_string(GREETINGS[payload.chatter.name][self.bot_data.get_current_chatter_form(payload.chatter.name)]["greeting"])) # type: ignore

			self.bot_data.greetings_said.add(payload.chatter.name)

	# channel point stuff
	@commands.Component.listener()
	async def event_custom_redemption_add(self, payload: twitchio.ChannelPointsRedemptionAdd):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		# silly mode
		if self.bot_data.silly_mode:
			for redeem in REDEEMS.values():
				if redeem["silly"]:
					new_cost = random.randrange(2, 999)
					await user.update_custom_reward(redeem["id"], cost=new_cost)

		# When redeem is triggered, first check if the title matches any of the avatar redeems. If so, add the avatar swap to the queue.
		if payload.reward.title in AVATARS:
			await self.queue_action(AvatarAction(ActionType.AVATAR_CHANGE, AVATARS[payload.reward.title]["veadotube_name"], 2.0))
		#if it's not in the avatar list, compare to other redeems
		elif payload.reward.id == REDEEMS["Random Avatar"]["id"]:
			await self.queue_action(AvatarAction(ActionType.RANDOM_AVATAR, "", 2.0))
		# headpats and hugs.
		elif payload.reward.id == REDEEMS["HeadPats (WIP)"]["id"] or payload.reward.id == REDEEMS["Hug!"]["id"]:
			is_hug = payload.reward.id == REDEEMS["Hug!"]["id"]
			all_interact_timings = get_avatar_info_by_veadotube_name(self.bot_data.avatar).get("interact_timings", 2.5)
			this_interact_timings = all_interact_timings if isinstance(all_interact_timings, float) else all_interact_timings.get("hug" if is_hug else "headpats", 2.5)
			duration = this_interact_timings if isinstance(this_interact_timings, float) else this_interact_timings.get(payload.user.name, this_interact_timings.get("default", 2.5))
			await self.queue_action(AvatarAction(ActionType.HUG if is_hug else ActionType.HEADPATS, self.bot_data.avatar, duration))
		elif payload.reward.id == REDEEMS["Memory Leak"]["id"]:
			self.bot_data.silly_mode ^= True
			for redeem in REDEEMS.values():
				if redeem["silly"]:
					await user.update_custom_reward(redeem["id"], cost=random.randrange(2, 999) if self.bot_data.silly_mode else redeem["base_price"])

			await user.send_message(sender=self.bot.user, message=f"Silly Mode {'activated' if self.bot_data.silly_mode else 'deactivated'}") # type: ignore
		elif payload.reward.id == REDEEMS["This Redeem does nothing"]["id"]:
			nothing_cost = self.bot_data.get_variable("nothing_cost")
			self.bot_data.store_variable("nothing_cost", nothing_cost + 1)
			await user.update_custom_reward(REDEEMS["This Redeem does nothing"]["id"], cost=nothing_cost)
		elif payload.reward.id == REDEEMS["Create a Fox Rule!"]["id"]:
			self.bot_data.add_foxrule(payload.user.display_name, payload.user_input) # type: ignore
			await user.send_message(sender=self.bot.user, message="Fox Rules have been updated!") # type: ignore
		elif payload.reward.id == REDEEMS["First!"]["id"]:
			self.bot_data.increment_first_count(payload.user.name) # type: ignore
			await user.update_custom_reward(REDEEMS["First!"]["id"], title=f"{payload.user.display_name} was first this stream!", prompt=f"They've been first {self.bot_data.get_first_count(payload.user.name)} times!") # type: ignore

	# hype dragons
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

	# Hype train end
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

	# I think this is the shoutout
	@commands.command(aliases=["so"])
	async def shoutout(self, context: commands.Context):
		if context.author.moderator or context.author.broadcaster:	 # type: ignore
			whom = context.message.text.split()[1] # type: ignore
			user = self.bot.create_partialuser(user_id=OWNER_ID)
			await user.send_shoutout(to_broadcaster=whom, moderator=context.author)

########################################################################################################################

def increment_undo(bot: Bot):
	bot.bot_data.undo_count += 1
