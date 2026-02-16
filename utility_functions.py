import datetime
import random
import requests
import json
from astral import moon
from num2words import num2words
from CnyZodiac import ChineseNewYearZodiac as cnyz

def string_to_leetspeak(string: str) -> str:
	table = {
		"o": "0",
		"i": "1",
		"z": "2",
		"e": "3",
		"a": "4",
		"s": "5",
		"g": "6",
		"t": "7",
		"O": "N",
		"I": "I",
		"Z": "II",
		"E": "III",
		"A": "IV",
		"S": "V",
		"G": "VI",
		"T": "VII",
	}

	result = ""
	for char in string:
		replacement = table.get(char)
		if replacement != None:
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
