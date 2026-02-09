from enum import Enum

class ActionType(Enum):
	AVATAR_CHANGE = 0
	RANDOM_AVATAR = 1
	HEADPATS = 2
	HUG = 3

class AvatarAction:
	def __init__(self, type_: ActionType, avatar: str):
		self.type = type_
		self.avatar = avatar
