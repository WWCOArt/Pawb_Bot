import datetime
import random
import requests
import json
import math
import platform
from astral import moon
from num2words import num2words
from CnyZodiac import ChineseNewYearZodiac as cnyz

from twitchio import PartialUser
from twitchio.ext import commands

from enum import Enum

class PronounType(Enum):
	THEY = 0
	THEM = 1
	THEIR = 2
	THEIRS = 3

class CheckType(Enum):
	PROGRESSION = 0
	FILLER = 1
	TRAP = 2

PRONOUNS_THEY = {
	PronounType.THEY: "they",
	PronounType.THEM: "them",
	PronounType.THEIR: "their",
	PronounType.THEIRS: "theirs",
}

PRONOUNS = {
	"hehim": {
		PronounType.THEY: "he",
		PronounType.THEM: "him",
		PronounType.THEIR: "his",
		PronounType.THEIRS: "his",
	},
	"sheher": {
		PronounType.THEY: "she",
		PronounType.THEM: "her",
		PronounType.THEIR: "her",
		PronounType.THEIRS: "hers",
	},
	"itits": {
		PronounType.THEY: "it",
		PronounType.THEM: "it",
		PronounType.THEIR: "its",
		PronounType.THEIRS: "its",
	},
	"faefaer": {
		PronounType.THEY: "fae",
		PronounType.THEM: "fae",
		PronounType.THEIR: "faer",
		PronounType.THEIRS: "faers",
	},
	"xexem": {
		PronounType.THEY: "xe",
		PronounType.THEM: "xem",
		PronounType.THEIR: "xir",
		PronounType.THEIRS: "xirs",
	},
	"aeaer": {
		PronounType.THEY: "ae",
		PronounType.THEM: "ae",
		PronounType.THEIR: "aer",
		PronounType.THEIRS: "aers",
	},
	"eem": {
		PronounType.THEY: "e",
		PronounType.THEM: "em",
		PronounType.THEIR: "eir",
		PronounType.THEIRS: "eirs",
	},
	"perper": {
		PronounType.THEY: "per",
		PronounType.THEM: "per",
		PronounType.THEIR: "per",
		PronounType.THEIRS: "pers",
	},
	"vever": {
		PronounType.THEY: "ve",
		PronounType.THEM: "ver",
		PronounType.THEIR: "ver",
		PronounType.THEIRS: "vers",
	},
	"ziehir": {
		PronounType.THEY: "zie",
		PronounType.THEM: "hir",
		PronounType.THEIR: "hir",
		PronounType.THEIRS: "hirs",
	},
	"theythem": PRONOUNS_THEY,
	"other": PRONOUNS_THEY,
	"any": PRONOUNS_THEY,
}

def get_pronouns(username: str, type_: PronounType, capitalize: bool = False) -> str:
	result = requests.get(f"https://pronouns.alejo.io/v1/users/{username}").text

	pronoun = "theythem"
	if result != "not_found":
		json1 = json.loads(result)
		pronoun = json1["pronoun_id"]

	retval = PRONOUNS.get(pronoun, PRONOUNS_THEY)[type_]
	return retval.capitalize() if capitalize else retval


def string_to_leetspeak(string: str) -> str:
	table = {
		"o": "0",
		"i": "1",
		"l": "1",
		"z": "2",
		"e": "3",
		"a": "4",
		"s": "5",
		"g": "6",
		"t": "7",
		"b": "8",
		"O": "N",
		"I": "I",
		"L": "I",
		"Z": "II",
		"E": "III",
		"A": "IV",
		"S": "V",
		"G": "VI",
		"T": "VII",
		"B": "VIII",
	}

	result = ""
	for char in string:
		replacement = table.get(char)
		if replacement != None and random.choice([True, False]):
			result += replacement
		else:
			result += char

	return result

def get_mainecoone_name(person_talking: str) -> str:
	today = datetime.datetime.today()
	weekday = today.weekday()
	if weekday == 0: # Monday - person talking
		return person_talking
	elif weekday == 1: # Tuesday - season
		if today.month >= 12:
			return "Winter"
		elif today.month >= 9:
			return "Autumn"
		elif today.month >= 6:
			return "Summer"
		elif today.month >= 3:
			return "Spring"
		else:
			return "Winter"
	elif weekday == 2: # Wednesday - weather
		latitude = random.uniform(34.0, 42.0)
		longitude = random.uniform(-118.0, -84.0)

		response1 = requests.get(f"https://api.weather.gov/points/{latitude},{longitude}")
		json1 = json.loads(response1.text)
		url = json1["properties"]["forecast"]

		response2 = requests.get(url)
		json2 = json.loads(response2.text)
		result = json2["properties"]["periods"][0]["shortForecast"]
		return result.replace("Chance", "").replace("Partly", "").replace("Mostly", "").replace("Slight", "").strip()
	elif weekday == 3: # Thursday - hour rounded down
		return num2words(today.hour).capitalize()
	elif weekday == 4: # Friday - last two digits of year - 50
		return str(today.year - 50)[2:]
	elif weekday == 5: # Saturday - zodiac animal
		return cnyz().zodiac_now()
	else: # Sunday - most recent neopagan full moon name
		if today.month == 1:
			return "Ice"
		elif today.month == 2:
			return "Snow"
		elif today.month == 3:
			return "Death"
		elif today.month == 4:
			return "Awakening"
		elif today.month == 5:
			return "Grass"
		elif today.month == 6:
			return "Planting"
		elif today.month == 7:
			return "Rose"
		elif today.month == 8:
			return "Lightening"
		elif today.month == 9:
			return "Harvest"
		elif today.month == 10:
			return "Blood"
		elif today.month == 11:
			return "Tree"
		else:
			return "Long Night"

def is_full_moon() -> bool:
	phase = moon.phase(datetime.datetime.now())
	return phase > 13.4 and phase < 14.6

async def send_message(user: PartialUser, sender: str | int | PartialUser, message: str):
	await user.send_message(sender=sender, message=message)

async def send_message_context(context: commands.Context, message: str, reply: bool = False):
	if reply:
		await context.reply(message)
	else:
		await context.send(message)

def convert_units(number: float, unit: str) -> str:
	if unit == "c" or unit == "celsius" or unit == "centigrade":
		return f"{number * 1.8 + 32:.03g} °F"
	elif unit == "f" or unit == "fahrenheit":
		return f"{(number - 32) / 1.8:.03g} °C"
	elif unit == "g" or unit == "gram" or unit == "grams":
		return f"{number / 453.59237:.03g} lbs"
	elif unit == "lb" or unit == "lbs" or unit == "pounds":
		return f"{number * 453.59237:.03g} g"
	elif unit == "m" or unit == "meter" or unit == "meters":
		result = number * 3.280839895
		return f"{result:.03g} ft ({math.trunc(result)} ft {math.trunc(result % 1 * 12)} in)"
	elif unit == "ft" or unit == "foot" or unit == "feet":
		return f"{number / 3.280839895:.03g} m"
	elif unit == "km" or unit == "kilometer" or unit == "kilometers" or unit == "kph" or unit == "km/h":
		return f"{number / 1.609344:.03g} mi"
	elif unit == "mi" or unit == "mile" or unit == "miles" or unit == "mph" or unit == "mi/h":
		return f"{number * 1.609344:.03g} km"
	elif unit == "cm" or unit == "centimeter" or unit == "centimeters":
		return f"{number / 2.54:.03g} in"
	elif unit == "in" or unit == "inch" or unit == "inches":
		return f"{number * 2.54:.03g} cm"
	elif unit == "l" or unit == "liter" or unit == "litre" or unit == "liters" or unit == "litres":
		return f"{number / 3.785411784:.03g} gal"
	elif unit == "gal" or unit == "gallon" or unit == "gallons":
		return f"{number * 3.785411784:.03g} L"
	else:
		return ""

def is_on_linux() -> bool:
	return platform.system() == "Linux"
