from django.core.serializers.python import Serializer
from core.constants import *

class EncodeTeamObject(Serializer):
	def get_dump_object(self, obj):
		"""
		Szerializáljuk a team objectet JSON formátumra, amelyet utána visszaküldünk a viewhoz
		"""

		team_object = {
			'id': str(obj.id),
			'name': str(obj.name),
			'description': str(obj.description),
			'members_number': str(len(obj.users.all())),
			'rank': str(obj.rank),
			'honor': str(obj.honor),
		}

		return team_object