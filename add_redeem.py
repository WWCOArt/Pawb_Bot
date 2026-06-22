import json
import asyncio
import logging
import twitchio
from twitchio.ext import commands

bot_secrets = open("secrets.json", encoding="utf8")
bot_secrets_json = json.load(bot_secrets)
CLIENT_ID = bot_secrets_json["client_id"]
CLIENT_SECRET = bot_secrets_json["client_secret"]
BOT_ID = bot_secrets_json["bot_id"]
OWNER_ID = bot_secrets_json["owner_id"]
CLOUD_WEBHOOK_URL = bot_secrets_json["cloud_webhook_url"]
bot_secrets.close()

LOGGER: logging.Logger = logging.getLogger("Bot")

# AVATAR REDEEM 1: fdbfd353-7828-4220-8351-53c9b61572a8
# AVATAR REDEEM 2: 97df88a8-4d76-4f82-b4ba-d221ae1457a2
# AVATAR REDEEM 3: 24a3f4af-1318-4da1-b728-5d57f01a81f5
# AVATAR REDEEM 4: 4f410a06-a112-47a7-a83a-fdfc434a2e0c
# AVATAR REDEEM 5: 171fc124-04dd-40d8-816a-4db8130ea25c

####### EDIT THESE
redeem_name = "AVATAR REDEEM 5"
redeem_color = "#bda8ff"
redeem_description = None
redeem_cost = 100
#######

class Bot(commands.Bot):
	def __init__(self) -> None:
		super().__init__(
			client_id=CLIENT_ID,
			client_secret=CLIENT_SECRET,
			bot_id=BOT_ID,
			owner_id=OWNER_ID,
			prefix="!",
			case_insensitive=True
		)

	async def setup_hook(self) -> None:
		user = self.create_partialuser(user_id=OWNER_ID)

		reward = await user.create_custom_reward(title=redeem_name, cost=redeem_cost, background_color=redeem_color)
		
		print("Redeem created!")
		print(reward.id)

b = Bot()
# Setup logging, this is optional, however a nice to have...
twitchio.utils.setup_logging(level=logging.INFO)

async def runner() -> None:
	async with b as bot:
		await bot.start()

asyncio.run(runner())
