import json
import logging
import random
import subprocess
import datetime
import keyboard
import asyncio
import re
import requests
import traceback

VERSION_NUMBER = "0.3.8"

DIANE_TEST_MODE = False

import twitchio
from twitchio import eventsub
from twitchio.ext import commands, routines
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from utility_functions import send_message, send_message_context, string_to_leetspeak

import trello
from bot_data import BotData
from avatar_action import ActionType, AvatarAction
from commands_rules import CommandsRules
from commands_donos import CommandsDonos
from commands_misc import CommandsMisc
from commands_characters import CommandsCharacters

########################################################################################################################
# Global variable + JSON setup
########################################################################################################################

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
	CURRENT_SONG_PATH = config_data_json["current_song_path"]

with open("avatars.json", encoding="utf8") as avatars_file:
	AVATARS = json.load(avatars_file)

	REDEEMS_DEFAULT_ENABLED = set()
	REDEEMS_DEFAULT_DISABLED = set()
	for avatar in AVATARS.values():
		REDEEMS_DEFAULT_DISABLED.update(avatar.get("enable_redeems", []))
		REDEEMS_DEFAULT_ENABLED.update(avatar.get("disable_redeems", []))

with open("redeems.json", encoding="utf8") as redeem_ids_file:
	REDEEMS = json.load(redeem_ids_file)

with open("greetings.json", encoding="utf8") as greetings_file:
	GREETINGS = json.load(greetings_file)

LOGGER: logging.Logger = logging.getLogger("Bot")

########################################################################################################################
# Utility functions
########################################################################################################################

#def get_current_avatar() -> str:
#	if DIANE_TEST_MODE:
#		return current_avatar
#	else:
#		result = subprocess.Popen("veadotube -i 0 nodes stateEvents avatarSwap peek", stdout=subprocess.PIPE)
#		return result.stdout.read().decode() # type: ignore

def set_current_avatar(bot_data: BotData, av: str):
	bot_data.current_avatar = av
	if not DIANE_TEST_MODE:
		subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents avatarSwap set "{av}"')

def get_avatar_info_by_veadotube_name(veadotube_name: str) -> dict:
	matches = [av for av in AVATARS.values() if av["veadotube_name"] == veadotube_name]
	return matches[0] if len(matches) > 0 else {}

########################################################################################################################
# Initial setup + bot start/shutdown
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

	# ignore "command not found" errors because why does it even throw those
	async def event_command_error(self, payload: commands.CommandErrorPayload) -> None:
		if not type(payload.exception) is commands.exceptions.CommandNotFound:
			await super().event_command_error(payload)

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

		# alerts
		payload_follow = eventsub.ChannelFollowSubscription(broadcaster_user_id=self.owner_id, moderator_user_id=self.owner_id)
		payload_subscribe = eventsub.ChannelSubscribeSubscription(broadcaster_user_id=self.owner_id)
		payload_resubscribe = eventsub.ChannelSubscribeMessageSubscription(broadcaster_user_id=self.owner_id)
		payload_giftsubs = eventsub.ChannelSubscriptionGiftSubscription(broadcaster_user_id=self.owner_id)
		payload_raid = eventsub.ChannelRaidSubscription(to_broadcaster_user_id=self.owner_id)
		payload_bits = eventsub.ChannelBitsUseSubscription(broadcaster_user_id=self.owner_id)

		await self.subscribe_websocket(payload=payload_online)
		await self.subscribe_websocket(payload=payload_offline)
		await self.subscribe_websocket(payload=payload_chatmessage)
		await self.subscribe_websocket(payload=payload_channelpoints)
		await self.subscribe_websocket(payload=payload_hypetrain_progress)
		await self.subscribe_websocket(payload=payload_hypetrain_end)

		#await self.subscribe_websocket(payload=payload_follow)
		#await self.subscribe_websocket(payload=payload_subscribe)
		#await self.subscribe_websocket(payload=payload_resubscribe)
		#await self.subscribe_websocket(payload=payload_giftsubs)
		#await self.subscribe_websocket(payload=payload_raid)
		#await self.subscribe_websocket(payload=payload_bits)

		await self.add_component(CommandsRules(self.bot_data))
		await self.add_component(CommandsChat(self, self.bot_data))
		await self.add_component(CommandsDonos(self.bot_data))
		await self.add_component(CommandsMisc(self.bot_data))
		await self.add_component(CommandsCharacters(self.bot_data))

		user = self.create_partialuser(user_id=OWNER_ID)

		if DIANE_TEST_MODE:
			await self.get_component("CommandsChat").queue_action(AvatarAction(ActionType.AVATAR_CHANGE, "sphinx", 1.0)) # type: ignore

		# reset everything if this is a new stream day
		last_start_time = self.bot_data.get_last_start_time()
		current_time = datetime.datetime.now()
		if last_start_time.month != current_time.month or last_start_time.day != current_time.day or last_start_time.year != current_time.year:
			self.bot_data.store_variable("undo_count", 0)
			self.bot_data.store_variable("bless_count", 0)
			self.bot_data.store_variable("distracted_count", 0)
			self.bot_data.store_variable("current_hype_level", 0)
			self.bot_data.store_variable("highest_hype_level", 0)

			await user.update_custom_reward(REDEEMS["First!"]["id"], title="First!", prompt="Show everyone you were the fastest.")
			await user.update_custom_reward(REDEEMS["Planks!"]["id"], enabled=False)
			await user.update_custom_reward(REDEEMS["HypeDragon1"]["id"], enabled=False)
			await user.update_custom_reward(REDEEMS["HypeDragon3"]["id"], enabled=False)
			await user.update_custom_reward(REDEEMS["HypeDragon5"]["id"], enabled=False)
			await user.update_custom_reward(REDEEMS["Winter Mode"]["id"], enabled=False)
			await user.update_custom_reward(REDEEMS["Blink"]["id"], enabled=False)
			await user.update_custom_reward(REDEEMS["What if Big?"]["id"], enabled=False)

			self.bot_data.clear_greetings_said()

		self.bot_data.update_last_start_time()

		keyboard.add_hotkey("ctrl+z", increment_undo, args=[self, asyncio.get_event_loop()]) # type: ignore
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

########################################################################################################################
# Streamer console commands
########################################################################################################################

	async def process_input(self, inp: str):
		user = self.create_partialuser(user_id=OWNER_ID)

		input_split = inp.split()
		if len(input_split) == 0:
			return

		command = input_split[0].lower().lstrip("/! \t")
		if command == "say":
			await send_message(user, sender=self.user, message=" ".join(input_split[1:])) # type: ignore
		elif command == "best" or command == "best_button":
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
				if input_split[1] == "random":
					await self.get_component("CommandsChat").queue_action(AvatarAction(ActionType.RANDOM_AVATAR, "", 2.0)) # type: ignore
				else:
					await self.get_component("CommandsChat").queue_action(AvatarAction(ActionType.AVATAR_CHANGE, input_split[1], 2.0)) # type: ignore
			else:
				print(f"Current avatar: {self.bot_data.current_avatar}")
		elif command == "veado" or command == "veadotube":
			if len(input_split) == 2:
				subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents {input_split[1]} set "{input_split[2]}"')
			else:
				print('Missing parameters for command "veado"')
		elif command == "show" or command == "variable":
			if len(input_split) > 1:
				var = input_split[1]
				try:
					value = self.bot_data.__getattribute__(var) # THIS IS HORRIBLE
				except AttributeError:
					value = self.bot_data.get_variable(var)

				print(f"{var} = {value}")
			else:
				print('Missing parameters for command "show"')
		elif command == "queue_random":
			if len(input_split) > 1:
				avatar = get_avatar_info_by_veadotube_name(input_split[1])
				self.bot_data.random_avatars.append(avatar)
			else:
				print('Missing parameters for command "queue_random"')
		elif command == "headpats" or command == "hug":
			is_hug = command == "hug"
			all_interact_timings = get_avatar_info_by_veadotube_name(self.bot_data.current_avatar).get("interact_timings", 2.5)
			this_interact_timings = all_interact_timings if isinstance(all_interact_timings, float) else all_interact_timings.get(command, 2.5)
			duration = this_interact_timings if isinstance(this_interact_timings, float) else this_interact_timings.get(("default", 2.5))
			await self.get_component("CommandsChat").queue_action(AvatarAction(ActionType.HUG if is_hug else ActionType.HEADPATS, self.bot_data.avatar, duration)) # type: ignore
		elif command == "noplanks":
			await user.update_custom_reward(REDEEMS["Planks!"]["id"], enabled=False)
			self.bot_data.planks_disabled = True
		elif command == "technology_connections":
			await user.send_announcement(moderator=self.user, message="Technology Connections is a great channel and you should go watch it https://www.youtube.com/@TechnologyConnections", color="purple") # type: ignore
		elif command == "help":
			print("""List of commands:
	say [message] - Make pawb_bot say something in chat.
	best_button - Press the best button.
	next - Advance the dono queue. (DOES NOT CURRENTLY WORK)
	avatar [avatar_name] - Switch to an avatar by its veadotube name. "avatar random" triggers random avatar.
	veado [node] [request] - Send a request to Veadotube in the format: veadotube -i 0 nodes stateEvents [node] set "[request]"
	show [variable_name] - Show the current value of a variable.
	queue_random [avatar_name] - Add an avatar to the random avatar queue by its veadotube name.
	headpats - Trigger headpats.
	hug - Trigger hug.
	noplanks - Disable the planks redeem for the rest of this stream.
	technology_connections - Technology Connections.
	help - Show this list.
				""")
		else:
			print(f'Unknown command "{command}" (Type "help" for all commands)')

########################################################################################################################
# Routines that run on a timer
########################################################################################################################

	@routines.routine(delta=datetime.timedelta(seconds=2))
	async def randomize_connection_offline(self):
		user = self.create_partialuser(user_id=OWNER_ID)
		await user.update_custom_reward(REDEEMS["Connection Offline. . ."]["id"], cost=random.randint(100000000, 999999999))

	@routines.routine(delta=datetime.timedelta(seconds=2), wait_first=True)
	async def poll_trello_queue(self):
		user = self.create_partialuser(user_id=OWNER_ID)
		new_queue = trello.get_trello_queue()
		if len(new_queue) != self.bot_data.current_queue_size:
			if len(new_queue) > self.bot_data.current_queue_size:
				latest_donor = new_queue[-1]["name"].split("###")
				if len(latest_donor) > 1:
					if latest_donor[1].isdigit():
						await send_message(user, sender=self.user, message=f"{latest_donor[0]}, you submitted a donation of less than $25, but you currently have a cooldown of {latest_donor[1]} days on getting an under $25 dono. You will be refunded.") # type: ignore
					else:
						await send_message(user, sender=self.user, message=f"{latest_donor[0]}, you are already on the queue. You will be refunded.") # type: ignore
				else:
					await user.send_announcement(moderator=self.user, message=f"{latest_donor[0]} has been added to the queue.", color="orange") # type: ignore

			current_stream_title = (await user.fetch_channel_info()).title
			if "queue size" in current_stream_title:
				await user.modify_channel(title=re.sub(r"\[\d+\]", f"[{len(new_queue)}]", current_stream_title))
				self.bot_data.current_queue_size = len(new_queue)

	@routines.routine(delta=datetime.timedelta(hours=1), iterations=1)
	async def enable_planks(self):
		if not self.bot_data.planks_disabled:
			user = self.create_partialuser(user_id=OWNER_ID)
			await user.update_custom_reward(REDEEMS["Planks!"]["id"], enabled=True)

########################################################################################################################

class CommandsChat(commands.Component):
	def __init__(self, bot: Bot, bot_data: BotData):
		self.bot = bot
		self.bot_data = bot_data

########################################################################################################################
# Avatar transitions + avatar action queue
########################################################################################################################

	async def avatar_transition(self, avatar: str):
		avatar_info = get_avatar_info_by_veadotube_name(avatar)
		redeems_disabled = avatar_info.get("disable_redeems", [])
		redeems_enabled = avatar_info.get("enable_redeems", [])

		user = self.bot.create_partialuser(user_id=OWNER_ID)

		for redeem in REDEEMS_DEFAULT_DISABLED:
			redeem_id = REDEEMS[redeem]["id"]
			already_enabled = (await user.fetch_custom_rewards(ids=[redeem_id]))[0].enabled
			if not already_enabled and redeem in redeems_enabled:
				await user.update_custom_reward(redeem_id, enabled=True)
			elif not redeem in redeems_enabled:
				await user.update_custom_reward(redeem_id, enabled=False)

		for redeem in REDEEMS_DEFAULT_ENABLED:
			redeem_id = REDEEMS[redeem]["id"]
			already_enabled = (await user.fetch_custom_rewards(ids=[redeem_id]))[0].enabled
			if not already_enabled and not redeem in redeems_disabled:
				await user.update_custom_reward(redeem_id, enabled=True)
			elif redeem in redeems_disabled:
				await user.update_custom_reward(redeem_id, enabled=False)

	async def update_redeem_availability(self, previous_avatar: str, new_avatar: str):
		await self.avatar_transition(new_avatar)

	async def advance_action_queue(self):
		user = self.bot.create_partialuser(user_id=OWNER_ID)
		
		#print(f"Advancing queue ({self.bot_data.get_action_queue_string()})")
		#print(traceback.print_stack())
		action = self.bot_data.action_queue[0]
		if action.type == ActionType.AVATAR_CHANGE:
			previous_avatar = self.bot_data.current_avatar
			avatar_info = get_avatar_info_by_veadotube_name(action.avatar)
			avatar_name = action.avatar
			new_avatar = str()
			if len(avatar_info) > 0:
				if avatar_name == "Kat":
					new_avatar = random.choices(["katMale", "katFemale", "katNanite"], weights=[90, 90, 20], k=1)[0]
				elif avatar_name == "Gremlin":
					if previous_avatar == "dragonSmall" or previous_avatar == "dragonOverload" or previous_avatar == "dragonMacro":
						new_avatar = "gremlinDragon"
					else:
						new_avatar = "gremlinSphinx"
				else:
					new_avatar = avatar_info["veadotube_name"]

				set_current_avatar(self.bot_data, new_avatar)
				await self.update_redeem_availability(previous_avatar, new_avatar)
		elif action.type == ActionType.RANDOM_AVATAR:
			with open(CURRENT_SONG_PATH) as song_file:
				current_song = song_file.read().strip()
			
			previous_avatar = self.bot_data.current_avatar
			new_avatar = {}
			song_override = False
			for avatar in AVATARS.values():
				this_song = avatar.get("song")
				if this_song != None and this_song in current_song:
					new_avatar = avatar
					song_override = True
					break

			if not song_override:
				new_avatar = self.bot_data.random_avatars.pop()
				if len(self.bot_data.random_avatars) == 0:
					self.bot_data.queue_random_avatars(AVATARS)

			set_current_avatar(self.bot_data, new_avatar["veadotube_name"])
			await send_message(user, sender=self.bot.user, message=self.bot_data.replace_vars_in_string(new_avatar["description"])) # type: ignore
			await self.update_redeem_availability(previous_avatar, new_avatar["veadotube_name"])
		# elif action.type == ActionType.HEADPATS:
		# 	subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents expression set "headpats"')
		# elif action.type == ActionType.HUG:
		# 	subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents expression set "hug"')
		elif action.type == ActionType.PEER_PRESSURE:
			if self.bot_data.current_avatar == "peerPressure":
				if not DIANE_TEST_MODE:
					subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents pressure set {float(self.bot_data.peer_pressure_level) + 0.5}')
				await asyncio.sleep(1.05)
				self.bot_data.peer_pressure_level += 1
				if not DIANE_TEST_MODE:
					subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents pressure set {self.bot_data.peer_pressure_level}')
				if self.bot_data.peer_pressure_level == 5:
					set_current_avatar(self.bot_data, "dragonSmall")
					await self.update_redeem_availability(self.bot_data.current_avatar, "dragonSmall")
			elif self.bot_data.current_avatar == "dragonSmall":
				self.bot_data.peer_pressure_level += 1
				if not DIANE_TEST_MODE:
					subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents pressure set {self.bot_data.peer_pressure_level}')
				await asyncio.sleep(0.5)
				if not DIANE_TEST_MODE:
					subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents pressure set {float(self.bot_data.peer_pressure_level + 0.5)}')
				set_current_avatar(self.bot_data, "peerPressure")
				await asyncio.sleep(11)
				set_current_avatar(self.bot_data, "dragonOverload")
				await self.update_redeem_availability(self.bot_data.current_avatar, "dragonOverload")
			else:
				set_current_avatar(self.bot_data, "peerPressure")
				await self.update_redeem_availability(self.bot_data.current_avatar, "peerPressure")
				self.bot_data.peer_pressure_level = 1
				if not DIANE_TEST_MODE:
					subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents pressure set {self.bot_data.peer_pressure_level}')

		await asyncio.sleep(action.duration)

		if action.type == ActionType.HEADPATS or action.type == ActionType.HUG and not DIANE_TEST_MODE:
			subprocess.run(f'{VEADOTUBE_PATH} -i 0 nodes stateEvents expression set "neutral"')

		self.bot_data.action_queue.popleft()
		if len(self.bot_data.action_queue) > 0:
			await self.advance_action_queue()

	async def queue_action(self, action: AvatarAction):
		self.bot_data.action_queue.append(action)
		#print(f"Adding to queue ({self.bot_data.get_action_queue_string()})")
		if len(self.bot_data.action_queue) == 1:
			await self.advance_action_queue()

########################################################################################################################
# Stream start
########################################################################################################################

	@commands.Component.listener()
	async def event_stream_online(self, payload: twitchio.StreamOnline):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		await self.queue_action(AvatarAction(ActionType.AVATAR_CHANGE, "sphinx", 1.0))

		await send_message(user, sender=self.bot.user, message=f"PawbOS v{VERSION_NUMBER} booting up.") # type: ignore
		await asyncio.sleep(0.5)
		await send_message(user, sender=self.bot.user, message="PawbBot terminal online.") # type: ignore
		await asyncio.sleep(0.5)
		await send_message(user, sender=self.bot.user, message="Avatar system online.") # type: ignore
		await asyncio.sleep(1.0)
		await send_message(user, sender=self.bot.user, message="Video feed online.") # type: ignore
		await asyncio.sleep(1.0)
		await send_message(user, sender=self.bot.user, message="Audio feed online.") # type: ignore
		await asyncio.sleep(1.0)
		await send_message(user, sender=self.bot.user, message="Low bandwidth detected. Searching for connection...") # type: ignore

########################################################################################################################
# Stream end
########################################################################################################################

	@commands.Component.listener()
	async def event_stream_offline(self, payload: twitchio.StreamOffline):
		user = self.bot.create_partialuser(user_id=OWNER_ID)
		await send_message(user, sender=self.bot.user, message="PawbOS shutting down.") # type: ignore
		if len(self.bot_data.stream_markers) > 0:
			all_markers = ", ".join([f"{marker[1]:02}:{marker[2]:02}:{marker[3]:02}: {marker[0]}" for marker in self.bot_data.stream_markers])
			print(f"Reminder to add these stream markers: {all_markers}")

########################################################################################################################
# Chat message functionality
########################################################################################################################

	@commands.Component.listener()
	async def event_message(self, payload: twitchio.ChatMessage):
		if payload.chatter.user == self.bot.user:
			return
		
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		# Zaffre Bless
		if payload.chatter.name == "thezaffrehammer" and "bless" in payload.text.lower():
			self.bot_data.increment_variable("bless_count")

		# Runary Yeeting the skunk.
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

			await send_message(user, sender=self.bot.user, message=message[1]) # type: ignore
			if message[0] == 1:
				await asyncio.sleep(120)
				await send_message(user, sender=self.bot.user, message="The skunk has been yeeted out of a portal and lands at runary's feet.") # type: ignore

		# User greetings.
		if payload.chatter.name in GREETINGS and not self.bot_data.has_greeting_been_said(payload.chatter.name): # type: ignore
			if payload.chatter.name == "flomuffin":
				self.bot_data.increment_variable("door_count")

			if isinstance(GREETINGS[payload.chatter.name], str): # string = single greeting
				await send_message(user, sender=self.bot.user, message=self.bot_data.replace_vars_in_string(GREETINGS[payload.chatter.name])) # type: ignore
			elif isinstance(GREETINGS[payload.chatter.name], list): # list = randomly pick from multiple greetings
				await send_message(user, sender=self.bot.user, message=self.bot_data.replace_vars_in_string(random.choice(GREETINGS[payload.chatter.name]))) # type: ignore
			else: # dictionary = pick greeting based on form
				await send_message(user, sender=self.bot.user, message=self.bot_data.replace_vars_in_string(GREETINGS[payload.chatter.name][self.bot_data.get_current_chatter_form(payload.chatter.name)]["greeting"])) # type: ignore

			self.bot_data.add_greeting_said(payload.chatter.name) # type: ignore

########################################################################################################################
# Redeems
########################################################################################################################

	@commands.Component.listener()
	async def event_custom_redemption_add(self, payload: twitchio.ChannelPointsRedemptionAdd):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		# When redeem is triggered, first check if the title matches any of the avatar redeems. If so, add the avatar swap to the queue.
		if payload.reward.title in AVATARS:
			if payload.reward.title == "Peer Pressure":
				await self.queue_action(AvatarAction(ActionType.PEER_PRESSURE, "", 5.0))
			else:
				await self.queue_action(AvatarAction(ActionType.AVATAR_CHANGE, AVATARS[payload.reward.title]["veadotube_name"], 2.0))
		#if it's not in the avatar list, compare to other redeems
		elif payload.reward.id == REDEEMS["Random Avatar"]["id"]:
			await self.queue_action(AvatarAction(ActionType.RANDOM_AVATAR, "", 2.0))
		# headpats and hugs.
		elif payload.reward.id == REDEEMS["HeadPats"]["id"] or payload.reward.id == REDEEMS["Hug!"]["id"]:
			is_hug = payload.reward.id == REDEEMS["Hug!"]["id"]
			all_interact_timings = get_avatar_info_by_veadotube_name(self.bot_data.current_avatar).get("interact_timings", 2.5)
			this_interact_timings = all_interact_timings if isinstance(all_interact_timings, float) else all_interact_timings.get("hug" if is_hug else "headpats", 2.5)
			duration = this_interact_timings if isinstance(this_interact_timings, float) else this_interact_timings.get(payload.user.name, this_interact_timings.get("default", 2.5))
			await self.queue_action(AvatarAction(ActionType.HUG if is_hug else ActionType.HEADPATS, self.bot_data.current_avatar, duration))
		elif payload.reward.id == REDEEMS["Peer Pressure"]["id"]:
			await self.queue_action(AvatarAction(ActionType.PEER_PRESSURE, "", 2.0))
		elif payload.reward.id == REDEEMS["Pressure Overload"]["id"]:
			await self.queue_action(AvatarAction(ActionType.PEER_PRESSURE, "", 11.0))
		elif payload.reward.id == REDEEMS["Memory Leak"]["id"]:
			self.bot_data.silly_mode ^= True
			await send_message(user, sender=self.bot.user, message=f"Silly Mode {'activated' if self.bot_data.silly_mode else 'deactivated'}") # type: ignore
			for redeem in REDEEMS.values():
				if redeem["silly"]:
					await user.update_custom_reward(redeem["id"], cost=random.randrange(2, 999) if self.bot_data.silly_mode else redeem["base_price"])
		elif payload.reward.id == REDEEMS["This Redeem does nothing"]["id"]:
			nothing_cost = self.bot_data.get_variable("nothing_cost")
			if nothing_cost != None:
				self.bot_data.store_variable("nothing_cost", nothing_cost + 1)
				await user.update_custom_reward(REDEEMS["This Redeem does nothing"]["id"], cost=nothing_cost, prompt=f"But each time it's redeemed, the cost becomes one higher. How high will it go? Last redeemed by {payload.user.display_name}.")
		elif payload.reward.id == REDEEMS["Create a Fox Rule!"]["id"]:
			self.bot_data.add_foxrule(payload.user.display_name, payload.user_input) # type: ignore
			await send_message(user, sender=self.bot.user, message="Fox Rules have been updated!") # type: ignore
		elif payload.reward.id == REDEEMS["First!"]["id"]:
			self.bot_data.increment_first_count(payload.user.name) # type: ignore
			await user.update_custom_reward(REDEEMS["First!"]["id"], title=f"{payload.user.display_name} was first this stream!", prompt=f"They've been first {self.bot_data.get_first_count(payload.user.name)} times!") # type: ignore

		# silly mode
		if self.bot_data.silly_mode:
			for redeem in REDEEMS.values():
				if redeem["silly"]:
					new_cost = random.randrange(2, 999)
					await user.update_custom_reward(redeem["id"], cost=new_cost)

########################################################################################################################
# Hype trains + hype dragons
########################################################################################################################

	@commands.Component.listener()
	async def event_hype_train_progress(self, payload: twitchio.HypeTrainProgress):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		current_hype_level = self.bot_data.get_variable("current_hype_level")
		if current_hype_level != None and payload.level > current_hype_level:
			if payload.level == 1:
				await user.update_custom_reward(REDEEMS["HypeDragon1"]["id"], enabled=True)
				await send_message(user, sender=self.bot.user, message="Hype Dragon Level 1 unlocked.") # type: ignore
			elif payload.level == 2:
				await send_message(user, sender=self.bot.user, message="Hype Dragon Level 1 unlocked for rest of stream.") # type: ignore
			elif payload.level == 3:
				await user.update_custom_reward(REDEEMS["HypeDragon3"]["id"], enabled=True)
				await send_message(user, sender=self.bot.user, message="Hype Dragon Level 3 unlocked.") # type: ignore
			elif payload.level == 4:
				await send_message(user, sender=self.bot.user, message="Hype Dragon Level 3 unlocked for rest of stream.") # type: ignore
			elif payload.level == 5:
				await user.update_custom_reward(REDEEMS["HypeDragon5"]["id"], enabled=True)
				await send_message(user, sender=self.bot.user, message="Hype Dragon Level 5 unlocked.") # type: ignore
			elif payload.level >= 6:
				await send_message(user, sender=self.bot.user, message="Hype Dragon Level 5 unlocked for rest of stream.") # type: ignore

			self.bot_data.store_variable("current_hype_level", payload.level)
			self.bot_data.store_variable("highest_hype_level", payload.level)

	@commands.Component.listener()
	async def event_hype_train_end(self, payload: twitchio.HypeTrainEnd):
		user = self.bot.create_partialuser(user_id=OWNER_ID)
		current_level = self.bot_data.get_variable("current_hype_level")
		highest_level = self.bot_data.get_variable("highest_hype_level")

		if highest_level != None and current_level != None:
			if highest_level < 6:
				await user.update_custom_reward(REDEEMS["HypeDragon5"]["id"], enabled=False)
				if current_level > 4:
					await send_message(user, sender=self.bot.user, message="Hype Dragon Level 5 disabled.") # type: ignore

			if highest_level < 4:
				await user.update_custom_reward(REDEEMS["HypeDragon3"]["id"], enabled=False)
				if current_level > 2:
					await send_message(user, sender=self.bot.user, message="Hype Dragon Level 3 disabled.") # type: ignore

			if highest_level < 2:
				await user.update_custom_reward(REDEEMS["HypeDragon1"]["id"], enabled=False)
				if current_level > 0:
					await send_message(user, sender=self.bot.user, message="Hype Dragon Level 1 disabled.") # type: ignore

		self.bot_data.store_variable("current_hype_level", 0)

########################################################################################################################
# Alerts
########################################################################################################################

	#@commands.Component.listener()
	#async def event_

########################################################################################################################
# Other commands
########################################################################################################################

	@commands.command(aliases=["so"])
	async def shoutout(self, context: commands.Context):
		if context.author.moderator or context.author.broadcaster:	 # type: ignore
			whom = context.message.text.split()[1] # type: ignore
			user = self.bot.create_partialuser(user_id=OWNER_ID)
			await user.send_shoutout(to_broadcaster=whom, moderator=context.author)

	@commands.command(aliases=["highlight", "hl"])
	@commands.cooldown(rate=1, per=120.0, key=commands.BucketType.default)
	async def marker(self, context: commands.Context):
		user = self.bot.create_partialuser(user_id=OWNER_ID)

		# the stream marker description will be everything the user typed after the !marker command
		# " ".join() means combine everything in the array you pass to it into one string, separated by a space
		# context.message.text.split() splits context.message.text into an array of words, and [1:] returns all its elements starting with the second one (this gets rid of the !marker)
		description = " ".join(context.message.text.split()[1:]) # type: ignore

		await user.create_stream_marker(token_for=OWNER_ID, description=description)

		start_time = (await user.fetch_stream()).started_at # type: ignore
		uptime = datetime.datetime.now() - start_time
		mm, ss = divmod(uptime.seconds, 60)
		hh, mm = divmod(mm, 60)

		self.bot_data.stream_markers.append((description, hh, mm, ss))

		await send_message_context(context, "Stream Marker has been created!", reply=True)

########################################################################################################################
# Undo-related functions
########################################################################################################################

def increment_undo_actual(bot: Bot):
	bot.bot_data.increment_variable("undo_count")

def increment_undo(bot: Bot, event_loop: asyncio.AbstractEventLoop):
	event_loop.call_soon_threadsafe(increment_undo_actual, bot)
