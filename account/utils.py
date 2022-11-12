from django.core.serializers.python import Serializer
from core.constants import *

class EncodeAccountObject(Serializer):
	def get_dump_object(self, obj):
		"""
		Szerializáljuk az account objectet JSON formátumra, amelyet utána visszaküldünk a viewhoz
		"""


		try:
			profile_image = obj.profile_image.url
		except Exception as e:
			profile_image = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET

		account_object = {
			'id': str(obj.id),
			'username': str(obj.username),
			'email': str(obj.email),
			'profile_image': str(profile_image),
		}

		return account_object


class EncodeCharacterObject(Serializer):
	def get_dump_object(self, obj):
		"""
		Szerializáljuk a character objectet JSON formátumra, amelyet utána visszaküldünk a viewhoz
		"""

		try:
			team = str(obj.account.team_set.all()[0].name)
		except Exception as e:
			# ha nincs csapata
			team = '-'



		character_object = {
			'id': str(obj.account.id),
			'account': str(obj.account),
			'character_type': str(obj.character_type),
			'level': str(obj.level),
			'rank': str(obj.rank),
			'honor': str(obj.honor),
			'team': team
		}

		return character_object


class EncodeCharacterObjectInDetail(Serializer):
	def get_dump_object(self, obj):
		"""
		Szerializáljuk a character objectet JSON formátumra, amelyet utána visszaküldünk a viewhoz, az attributumokkal együtt
		"""

		character_object = {
			'id': str(obj.account.id),
			'account': str(obj.account),
			'character_type': str(obj.character_type),
			'level': str(obj.level),
			'strength': str(obj.strength),
			'skill': str(obj.skill),
			'intelligence': str(obj.intelligence),
			'health_point': str(obj.health_point),
			'fortune': str(obj.fortune),
		}

		return character_object