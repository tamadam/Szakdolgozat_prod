from django.db import models
from django.conf import settings

from account.models import *


class ArenaManager(models.Manager):
	def create_arena_match(self, attacker, defender, attacker_health_values, defender_health_values, winner_of_fight):
		"""
		json.dumpssal kerülnek a health valuek ide, tehat kinyeréskor vissza kell alakítani json.loads-al --> visszakapjuk az eredeti listát
		"""
		arena_match = self.model(
				attacker = attacker,
				defender = defender,
				attacker_health_values = attacker_health_values,
				defender_health_values = defender_health_values,
				winner_of_fight = winner_of_fight
			)

		arena_match.save()

		return arena_match



class Arena(models.Model):

	attacker				= models.ForeignKey(Character, on_delete=models.CASCADE, related_name='attacker')
	defender				= models.ForeignKey(Character, on_delete=models.CASCADE, related_name='defender')

	attacker_health_values 	= models.TextField(null=True)
	defender_health_values 	= models.TextField(null=True)

	winner_of_fight			= models.ForeignKey(Character, on_delete=models.CASCADE, related_name='winner')

	date_of_fight 			= models.DateTimeField(verbose_name='date of fight', auto_now_add = True)


	objects 				= ArenaManager()


	def __str__(self):
		return f'Arena fight between {self.attacker} and {self.defender}'