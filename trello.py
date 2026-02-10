import json
import requests

def make_trello_request(method: str, url: str, secrets: dict, **kwargs):
	if len(secrets) == 0:
		secrets_file = open("secrets.json", encoding="utf8")
		secrets = json.load(secrets_file)
		secrets_file.close()

	headers = {
		"Accept": "application/json"
	}

	query = {
		"key": secrets["trello_api_key"],
		"token": secrets["trello_api_token"],
		**kwargs
	}

	response = requests.request(
		method,
		url,
		headers=headers,
		params=query,
	)

	return response

def get_trello_queue() -> list:
	secrets_file = open("secrets.json", encoding="utf8")
	secrets = json.load(secrets_file)
	secrets_file.close()

	response = make_trello_request("GET", f"https://api.trello.com/1/lists/{secrets["trello_queue_list"]}/cards", secrets)
	return json.loads(response.text)
