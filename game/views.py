from django.shortcuts import render
from account.models import Account, Character, CharacterHistory

from game.models import Arena
from team.models import Team
from django.http import JsonResponse
from core.constants import *
import math

from django.core import serializers
import json

from account.utils import EncodeAccountObject, EncodeCharacterObjectInDetail

from django.shortcuts import redirect

import random


def game_choice_view(request):
	context = {}

	return render(request, 'game/game_choice.html', context)



def easy_game_view(request):
	context = {}
	correct_field_values = ['2','4', '5', '6']
	game_field_size = request.GET.get('jatek_tabla_meret')

	if not game_field_size:
		game_field_size = 4
	elif game_field_size not in correct_field_values:
		game_field_size = 4 # alapértelmezett érték, hogyha a linken keresztül indítja el a játékot

	print('game_field_size', game_field_size)

	game_field_size = int(game_field_size)

	if game_field_size == 4:
		minutes = 0
		seconds = 45
	elif game_field_size == 5:
		minutes = 1
		seconds = 10
	elif game_field_size == 6:
		minutes = 2
		seconds = 10
	elif game_field_size == 2: #bemutató
		minutes = 0
		seconds = 10
	else:
		minutes = 0
		seconds = 45


	user = Account.objects.get(id=request.user.id)

	context = {
		'user_id': user.id,
		'game_field_size': game_field_size,
		'minutes': minutes,
		'seconds': seconds,
	}

	return render(request, 'game/easy_game.html', context)


def medium_game_view(request):
	context = {}

	correct_field_values = ['2', '3', '4', '5']
	game_field_size = request.GET.get('jatek_tabla_meret')

	if not game_field_size:
		game_field_size = 3
	elif game_field_size not in correct_field_values:
		game_field_size = 3 # alapértelmezett érték, hogyha a linken keresztül indítja el a játékot

	print('game_field_size', game_field_size)

	game_field_size = int(game_field_size)

	if game_field_size == 2:
		minutes = 0
		seconds = 10
	elif game_field_size == 3:
		minutes = 0
		seconds = 50
	elif game_field_size == 4:
		minutes = 1
		seconds = 30
	elif game_field_size == 5:
		minutes = 2
		seconds = 50
	else:
		minutes = 0
		seconds = 10

	user = Account.objects.get(id=request.user.id)

	context = {
		'user_id': user.id,
		'game_field_size': game_field_size,
		'minutes': minutes,
		'seconds': seconds,
	}

	return render(request, 'game/medium_game.html', context)



def hard_game_view(request):
	context = {}

	correct_field_values = ['2', '10', '20', '30']
	game_field_size = request.GET.get('bombak_szama')

	if not game_field_size:
		game_field_size = 10
	elif game_field_size not in correct_field_values:
		game_field_size = 10 # alapértelmezett érték, hogyha a linken keresztül indítja el a játékot

	print('game_field_size', game_field_size)

	game_field_size = int(game_field_size)

	if game_field_size == 10:
		minutes = 1
		seconds = 35
	elif game_field_size == 20:
		minutes = 2
		seconds = 20
	elif game_field_size == 30:
		minutes = 3
		seconds = 10
	elif game_field_size == 2: #bemutató
		minutes = 0
		seconds = 10
	else:
		minutes = 1
		seconds = 35




	user = Account.objects.get(id=request.user.id)

	context = {
		'user_id': user.id,
		'game_field_size': game_field_size,
		'minutes': minutes,
		'seconds': seconds,
	}

	return render(request, 'game/hard_game.html', context)



def increase_attributes_on_level_up(character):
	"""
	Szintlépéskor az összes tulajdonság értéke 8%-al nő
	"""
	character.strength = math.ceil(float(character.strength) * DEFAULT_ATTRIBUTE_INCREASE_PERCENTAGE)
	character.skill = math.ceil(float(character.skill) * DEFAULT_ATTRIBUTE_INCREASE_PERCENTAGE)
	character.intelligence = math.ceil(float(character.intelligence) * DEFAULT_ATTRIBUTE_INCREASE_PERCENTAGE)
	character.health_point = math.ceil(float(character.health_point) * DEFAULT_ATTRIBUTE_INCREASE_PERCENTAGE)
	character.fortune = math.ceil(float(character.fortune) * DEFAULT_ATTRIBUTE_INCREASE_PERCENTAGE)
	#print(math.ceil(float(character.strength) * DEFAULT_ATTRIBUTE_INCREASE_PERCENTAGE))



def finished_game(request):
	data = {}
	user_id = None
	game_type = 'easy'
	game_level = '1'

	try:
		user_id=request.GET.get('user_id')
		game_type=request.GET.get('game_type')
		game_level = request.GET.get('game_level')
		game_level_puzzle = request.GET.get('game_level_puzzle')
		game_level_bombs = request.GET.get('game_level_bombs')
	except Exception as e:
		print(e)
		pass


	# easy game-hez
	multiplier = 0

	if game_level == '2':
		multiplier = 10
	elif game_level == '3':
		multiplier = 20
	else:
		multiplier = 0

	####
	#second game-hez
	increaser = 0
	#if game_level_puzzle == '2':
	#	pass
	if game_level_puzzle == '4':
		increaser = 30
	elif game_level_puzzle == '5':
		increaser = 40

	###
	#third gamehez
	increaserBombs = 0
	if game_level_bombs == '20':
		increaserBombs = 30
	elif game_level_bombs == '30':
		increaserBombs = 50


	if user_id:
		character = Character.objects.get(account=user_id)

		# játék fajták megkülönböztetése --> mindegyikért eltérő mennyiségű XP jár
		if game_type == 'easy':
			if game_level == '0':
				got_gold = 0
				got_xp = 0
			else:
				character.current_xp += DEFAULT_XP_INCREASE_EASY_GAME + multiplier
				character.gold += DEFAULT_GOLD_INCREASE_EASY_GAME + multiplier
				got_gold = DEFAULT_GOLD_INCREASE_EASY_GAME + multiplier
				got_xp = DEFAULT_XP_INCREASE_EASY_GAME + multiplier
		elif game_type == 'second':
			if game_level_puzzle == '2':
				got_gold = 0
				got_xp = 0
			else:
				character.current_xp += DEFAULT_XP_INCREASE_MEDIUM_GAME + increaser
				character.gold += DEFAULT_GOLD_INCREASE_MEDIUM_GAME + increaser
				got_gold = DEFAULT_GOLD_INCREASE_MEDIUM_GAME + increaser
				got_xp = DEFAULT_XP_INCREASE_MEDIUM_GAME + increaser
		elif game_type == 'third':
			if game_level_bombs == '2':
				got_gold = 0
				got_xp = 0
			else:
				character.current_xp += DEFAULT_XP_INCREASE_HARD_GAME + increaserBombs
				character.gold += DEFAULT_GOLD_INCREASE_HARD_GAME + increaserBombs
				got_gold = DEFAULT_GOLD_INCREASE_HARD_GAME + increaserBombs
				got_xp = DEFAULT_XP_INCREASE_HARD_GAME + increaserBombs

		# szintlépés, ilyenkor növekszik a szint 1-el, az xp 0-zódik, az elérendő xp növekszik az előzőhöz képest, és a tulajdonsagok is nonek
		if character.current_xp >= character.next_level_xp:
			character.level += 1
			character.current_xp = 0
			character.next_level_xp += DEFAULT_NEXT_LEVEL_XP_INCREASE
			increase_attributes_on_level_up(character)

		character.save()

	data = {
		'message': 'Success',
		'got_gold': got_gold,
		'got_xp': got_xp,
	}

	return JsonResponse(data)


def check_profile_image(character):
	if character.account.profile_image:
		profile_image = character.account.profile_image.url
	else:
		profile_image = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET

	return profile_image



def arena_view(request):
	context = {}

	user_to_attack_id = request.GET.get(('ellenfel_id')) # a profilon keresztül
	user_id = request.user.id # a támadó user
	current_character = Character.objects.get(account=user_id)

	current_character_profile_image = check_profile_image(current_character)

	if user_to_attack_id:
		try:
			user_to_attack = Character.objects.get(account=user_to_attack_id)
		except:
			user_to_attack = None
			pass

		user_to_attack_profile_image = check_profile_image(user_to_attack) 

		context = {
			'left_character': '',
			'left_character_id': '',
			'right_character': '',
			'right_character_id': '',
			'current_character': current_character,
			'current_character_id': current_character.account.id,
			'current_character_profile_image': current_character_profile_image,
			'is_user_to_attack': True,
			'user_to_attack_id': user_to_attack_id,
			'user_to_attack': user_to_attack,
			'user_to_attack_profile_image': user_to_attack_profile_image,
		}
	else:
		characters = Character.objects.get_all_characters_in_ordered_list_without_admins()


		characters_count = len(characters)
		current_character_index = None
		left_side = None
		right_side = None
		left_side_id = None
		right_side_id = None
		# az adminok nem lesznek benne
		if current_character in characters:
			for i, value in enumerate(characters):
				if current_character == value:
					current_character_index = i
			# legalább 3 karakternek lennie kell az arénához
			if characters_count >= 3:
				if current_character_index is not None:
					if current_character_index == 0:
						# ha 0, akkor ő az első, ezért a két mögötte lévőt tesszük az arénába
						left_side = characters[current_character_index + 1] 
						right_side = characters[current_character_index + 2]

					elif current_character_index == characters_count - 1:
						# ha characters_count - 1-el egyenlő, azt jelenti, ő az utolsó, a két előtte lévőt kérjük
						left_side = characters[current_character_index - 1]
						right_side = characters[current_character_index - 2]

					else:
						# ha se nem első, se nem utolsó, akkor van egy előtte és utána lévő, ezeket tesszük az arénába
						left_side = characters[current_character_index + 1]
						right_side = characters[current_character_index - 1]

					#print(left_side, right_side)
					left_side_id = left_side.account.id
					right_side_id = right_side.account.id
					left_side_profile_image = check_profile_image(left_side)
					right_side_profile_image = check_profile_image(right_side)
					#print("IDK: ", left_side_id, right_side_id)
				else:
					# ha valamiért a current_character_index None, akkor csak menjen tovább a program
					# elvileg ez sem lehetséges
					pass
			else:
				# ha csak 1 vagy 2 karakter van akkor mi történjen
				# ha 0 karakter van, akkor csak az admin léphet be, viszont azt már fentebb lekezeljük
				# így nem fordulhat elő, hogy ide jusson a program, hogyha nincs karakter
				pass


		else:
			# adminoknak mi történjen
			pass

		context = {
			'left_character': left_side,
			'left_character_id': left_side_id,
			'left_character_profile_image': left_side_profile_image,
			'right_character_profile_image': right_side_profile_image,
			'right_character': right_side,
			'right_character_id': right_side_id,
			'current_character': current_character,
			'current_character_id': current_character.account.id,
			'current_character_profile_image': current_character_profile_image,
			'is_user_to_attack': False,

		}


	return render(request, 'game/arena.html', context)


def decide_winner(attacker, defender):
	attacker_role = attacker.character_type
	attacker_health = attacker.health_point * 30
	attacker_luck_value = attacker.fortune
	
	defender_role = defender.character_type
	defender_health = defender.health_point * 30
	defender_luck_value = defender.fortune

	attacker_health_value_list = []
	defender_health_value_list = []
	attacker_health_value_list.append(attacker_health)
	defender_health_value_list.append(defender_health)

	print('KEZDO ÉLETERO: ATTACKER - DEFENDER', attacker_health, defender_health)

	# a casthoz tartozó fő tulajdonságok meghatározása
	"""
	harcos - harcos
	harcos - mágus
	harcos - íjász
	mágus - mágus
	mágus - íjász
	íjász - íjász


	mágus - harcos
	íjász - harcos
	íjász - mágus
	"""
	if attacker_role == 'warrior' and defender_role == 'warrior':
		attacker_main_attr_value = attacker.strength
		defender_main_attr_value = defender.strength
		attacker_protect_attr_value = 0
		defender_protect_attr_value = 0

	elif attacker_role == 'warrior' and defender_role == 'mage':
		attacker_main_attr_value = attacker.strength
		defender_main_attr_value = defender.intelligence
		attacker_protect_attr_value = attacker.intelligence
		defender_protect_attr_value = defender.strength

	elif attacker_role == 'warrior' and defender_role == 'scout':
		attacker_main_attr_value = attacker.strength
		defender_main_attr_value = defender.skill
		attacker_protect_attr_value = attacker.skill
		defender_protect_attr_value = defender.strength

	elif attacker_role == 'mage' and defender_role == 'mage':
		attacker_main_attr_value = attacker.intelligence
		defender_main_attr_value = defender.intelligence
		attacker_protect_attr_value = 0
		defender_protect_attr_value = 0

	elif attacker_role == 'mage' and defender_role == 'scout':
		attacker_main_attr_value = attacker.intelligence
		defender_main_attr_value = defender.skill
		attacker_protect_attr_value = attacker.skill
		defender_protect_attr_value = defender.intelligence

	elif attacker_role == 'scout' and defender_role == 'scout':
		attacker_main_attr_value = attacker.skill
		defender_main_attr_value = defender.skill
		attacker_protect_attr_value = 0
		defender_protect_attr_value = 0

	elif attacker_role == 'mage' and defender_role == 'warrior':
		attacker_main_attr_value = attacker.intelligence
		defender_main_attr_value = defender.strength
		attacker_protect_attr_value = attacker.strength
		defender_protect_attr_value = defender.intelligence

	elif attacker_role == 'scout' and defender_role == 'warrior':
		attacker_main_attr_value = attacker.skill
		defender_main_attr_value = defender.strength
		attacker_protect_attr_value = attacker.strength
		defender_protect_attr_value = defender.skill

	elif attacker_role == 'scout' and defender_role == 'mage':
		attacker_main_attr_value = attacker.skill
		defender_main_attr_value = defender.intelligence
		attacker_protect_attr_value = attacker.intelligence
		defender_protect_attr_value = defender.skill


	did_attacker_win = False
	print("did_attacker_win")
	
	#kiszámoljuk hány % eséllyel sebez többet 
	if attacker_luck_value > defender_luck_value:
		attacker_bonus_damage_percent = round((defender_luck_value / attacker_luck_value) * 100)
		if attacker_bonus_damage_percent > 50:
			attacker_bonus_damage_percent = 50
		defender_bonus_damage_percent = 50 - attacker_bonus_damage_percent
	elif attacker_luck_value < defender_luck_value:
		defender_bonus_damage_percent = round((attacker_luck_value / defender_luck_value) * 100)
		if defender_bonus_damage_percent > 50:
			defender_bonus_damage_percent = 50
		attacker_bonus_damage_percent = 50 - defender_bonus_damage_percent


	print(attacker_bonus_damage_percent, "----", defender_bonus_damage_percent)

	damage_multiplier = [0, 1]

	while True:
		"""
		a sebzés felépítése:
			- van egy alap fő sebző tulajdonság és egy fő védekező tulajdonság, karakter típusonként más és más
			- ennek a kettőnek a különbsége alkotja a fő sebzést 
			- ehhez hozzájön a szerencse attribútum, amely maximum 50% lehet
			- 0 és 1 szorzók közül választ ennek a %-nak megfelelően
			-> akinek nagyobb a szerencseje az kapja a nagyobb %-ot a másik csak a maradékot
			-> mivel a kalkuláció során a két értéket összehasonlítjük és ennek vesszük a százalékát
		"""
		# mindig a támadó kezd tehát mindig a védekező sérül először
		attacker_added_damage = random.choices(damage_multiplier, weights=(100-attacker_bonus_damage_percent, attacker_bonus_damage_percent), k=1)[0]


		attacker_damage = (attacker_main_attr_value * 10) - (defender_protect_attr_value * 4) + (200 * attacker_added_damage)
		if attacker_damage <= 0:
			attacker_damage = 10
		defender_health -= attacker_damage



		if defender_health <= 0:
			defender_health_value_list.append('0')
			did_attacker_win = True
			break

		defender_health_value_list.append(defender_health)

		# ha nem halt meg a védekező, akkor ő jön, a támadó sebződik
		defender_added_damage = random.choices(damage_multiplier, weights=(100-defender_bonus_damage_percent, defender_bonus_damage_percent), k=1)[0]


		defender_damage = (defender_main_attr_value * 10) - (attacker_protect_attr_value * 4) + (200 * defender_added_damage)
		if defender_damage <= 0:
			defender_damage = 10
		attacker_health -= defender_damage


		if attacker_health <= 0:
			attacker_health_value_list.append('0')
			break


		attacker_health_value_list.append(attacker_health)
		#print('DEF HEALTH', defender_health)
		#print('ATTACK HEALTH', attacker_health)


	#print('ATTACKER HEALTH LIST', attacker_health_value_list)
	#print('DEFENDER_HEALTH_LIST', defender_health_value_list)

	if did_attacker_win:
		return attacker, attacker_health_value_list, defender_health_value_list

	return defender, attacker_health_value_list, defender_health_value_list



def arena_fight(request):
	data = {}


	attacker_user_id = None
	defender_user_id = None

	user_win = None

	try:
		attacker_user_id=request.GET.get('attacker_user_id')
		defender_user_id=request.GET.get('defender_user_id')
	except Exception as e:
		print(e)
		pass


	attacker_user = Character.objects.get(account=attacker_user_id)
	defender_user = Character.objects.get(account=defender_user_id)


	winner, attacker_health_values, defender_health_values = decide_winner(attacker_user, defender_user)

	attacker_user_history = CharacterHistory.objects.get(account=attacker_user_id)
	defender_user_history = CharacterHistory.objects.get(account=defender_user_id)

	attacker_user_history.fights_played += 1
	defender_user_history.fights_played += 1


	#add arena matches
	Arena.objects.create_arena_match(attacker_user, defender_user, 	json.dumps([int(num) for num in attacker_health_values]), json.dumps([int(num) for num in defender_health_values]), winner)


	print('GYŐZTES', winner)
	serialized_winner = serializers.serialize('json', [winner.account])
	print('ATTACKER', attacker_health_values)
	print('DEFENDER', defender_health_values)
	print(type(attacker_health_values))
	if winner == attacker_user:
		user_win = 'attacker'
		gained_honor_points = DEFAULT_GAIN_HONOR_POINTS_ARENA_FIGHTS
		lost_honor_points = 0
		# becsületpont
		attacker_user.honor += DEFAULT_GAIN_HONOR_POINTS_ARENA_FIGHTS
		defender_user.honor -= DEFAULT_LOST_HONOR_POINTS_ARENA_FIGHTS
		if defender_user.honor < 0:
			defender_user.honor = 0

		# statisztika
		attacker_user_history.fights_won += 1
		defender_user_history.fights_lost += 1
	elif winner == defender_user:
		user_win = 'defender'
		gained_honor_points = 0
		lost_honor_points = DEFAULT_LOST_HONOR_POINTS_ARENA_FIGHTS

		defender_user.honor += DEFAULT_GAIN_HONOR_POINTS_ARENA_FIGHTS
		attacker_user.honor -= DEFAULT_LOST_HONOR_POINTS_ARENA_FIGHTS
		if attacker_user.honor < 0:
			attacker_user.honor = 0


		defender_user_history.fights_won += 1	
		attacker_user_history.fights_lost += 1


	attacker_user_history.save()
	attacker_user.save()
	defender_user.save()
	defender_user_history.save()

	# frissíti a karakterek helyezését
	updateRank()


	s = EncodeAccountObject()

	account_object = {}
	account_object['winner_id'] = s.serialize([winner.account])[0]
	#print(json.loads(json.dumps(account_object['winner_id'])))
	data = {
		'message': 'Success',
		'attacker_health_values': attacker_health_values,
		'defender_health_values': defender_health_values,
		'user_win': account_object['winner_id'], #átadjuk az account objectet jsonre serializaljuk eloszor
		'gained_honor_points': gained_honor_points,
		'lost_honor_points': lost_honor_points,

	}

	return JsonResponse(data)



def updateRank():
	print('updating ranks...')
	rank_counter = 1
	characters = Character.objects.get_all_characters_in_ordered_list_without_admins()

	for character in characters:
		character.rank = rank_counter
		rank_counter += 1
		character.save()




def update_team_rank():
	print('updating team ranks...')
	rank_counter = 1
	teams = Team.objects.all()
	teams = sorted(teams, key=lambda team: team.honor, reverse=True)

	for team in teams:
		team.rank = rank_counter
		rank_counter += 1
		team.save()



def set_team_arena_sessions(request):
	"""
	Beállítom a session-öket, hogy az arena_team_view-ban le tudjam kérdezni a két csapatot, akik harcolnak
	Ezzel nem kell a linken keresztül elküldeni az adatot
	"""

	data = {}

	attacker_team_id = request.GET.get('attacker_team_id')
	defender_team_id = request.GET.get('defender_team_id')

	try:
		attacker_team = Team.objects.get(id=attacker_team_id)
		defender_team = Team.objects.get(id=defender_team_id)
		data['error_in_teams'] = 0
	except Exception as exception:
		attacker_team = None
		defender_team = None
		print(exception)
		data['error_in_teams'] = 1

		return JsonResponse(data)


	request.session['attacker_team_id'] = attacker_team.id
	request.session['defender_team_id'] = defender_team.id


	return JsonResponse(data)


# team arena 
def team_arena_view(request):
	context = {}

	# a sessiönökből kiszedjük a csapat ID-kat, majd a csapatokat, kivételkezeléssel
	try:
		attacker_team_id = request.session['attacker_team_id']
		defender_team_id = request.session['defender_team_id']
	except Exception as exception:
		print(exception)
		attacker_team_id = None
		defender_team_id = None
		return redirect('team:user_team_view')

	try:
		# ha már nincs érvényes sessiön, akkor szintén visszairányítjuk a csapat oldalra
		# így nem lehet megnyitni a csapat arénát, csak ha ténylegesen harcot indíott valaki
		if request.session['attacker_team_id'] == None or request.session['defender_team_id'] == None:
			return redirect('team:user_team_view')
	except Exception as exception:
		return redirect('team:user_team_view')



	if attacker_team_id and defender_team_id:
		try:
			attacker_team = Team.objects.get(id=attacker_team_id)
			defender_team = Team.objects.get(id=defender_team_id)
		except Exception as exception:
			print(exception)
			return redirect('team:user_team_view')


	else:
		return redirect('team:user_team_view')


	# ha idáig eljut a program, megvan a 2 csapat objektum
	context['attacker_team'] = attacker_team
	context['defender_team'] = defender_team

	# csapattagok listája szint szerint növekvő sorrendben
	attackers_list = Character.objects.get_characters_from_list_in_ordered_list_by_level(attacker_team.users.all())
	defenders_list = Character.objects.get_characters_from_list_in_ordered_list_by_level(defender_team.users.all())

	attacker_length = len(attackers_list)
	defender_length = len(defenders_list)


	i = 0
	j = 0
	attacker_health_left = None
	defender_health_left = None

	#print(attacker_length, "--", defender_length)

	s = EncodeAccountObject()

	sc = EncodeCharacterObjectInDetail()

	rounds = []

	while True:
		print(i, j)
		print(attackers_list[i], "--", defenders_list[j] )
		winner, attacker_health_values, defender_health_values = decide_winner_team(attackers_list[i], defenders_list[j], attacker_health_left, defender_health_left)


		attacker = attackers_list[i].account
		defender = defenders_list[j].account

		attacker_character = attackers_list[i]
		defender_character = defenders_list[j]
		#s.serialize([attacker])[0]
		#s.serialize([defender])[0]

		rounds.append({
			'attacker': s.serialize([attacker])[0],
			'defender': s.serialize([defender])[0],
			'attacker_character': sc.serialize([attacker_character])[0],
			'defender_character': sc.serialize([defender_character])[0],
			'winner': serializers.serialize('json', [winner.account]),
			'attacker_health_values': attacker_health_values,
			'defender_health_values': defender_health_values,
		})

		print(attacker_health_values)

		if winner in attackers_list:
			j += 1
			attacker_health_left = attacker_health_values[-1]
			defender_health_left = None
		else:
			i += 1
			defender_health_left = defender_health_values[-1]
			attacker_health_left = None

		if j >= defender_length:
			print("defender csapat vesztett")
			context['winner_of_all'] = 'attacker'
			context['gained_honor_points'] = DEFAULT_GAIN_HONOR_POINTS_TEAM_FIGHTS
			context['lost_honor_points'] = 0

			attacker_team.honor += DEFAULT_GAIN_HONOR_POINTS_TEAM_FIGHTS
			if defender_team.honor >= DEFAULT_LOST_HONOR_POINTS_TEAM_FIGHTS:
				defender_team.honor -= DEFAULT_LOST_HONOR_POINTS_TEAM_FIGHTS
			else:
				defender_team.honor = 0

			defender_team.save()
			attacker_team.save()
			break

		if i >= attacker_length:
			print("attacker csapat vesztett")
			context['winner_of_all'] = 'defender'
			context['gained_honor_points'] = 0
			context['lost_honor_points'] = DEFAULT_LOST_HONOR_POINTS_TEAM_FIGHTS

			defender_team.honor += DEFAULT_GAIN_HONOR_POINTS_TEAM_FIGHTS
			if attacker_team.honor >= DEFAULT_LOST_HONOR_POINTS_TEAM_FIGHTS:
				attacker_team.honor -= DEFAULT_LOST_HONOR_POINTS_TEAM_FIGHTS
			else:
				attacker_team.honor = 0
				
			defender_team.save()
			attacker_team.save()
			break

		#print(i, j)

	#print(attackers_list, "--", defenders_list)
	#print(attacker_length)
	#print(defender_length)

	update_team_rank()

	for single_round in rounds:
		print(single_round)
		print()

	context['rounds'] = rounds

	# sessiönök visszaállítása
	request.session['attacker_team_id'] = None
	request.session['defender_team_id'] = None


	return render(request, "game/team_arena.html", context)



def decide_winner_team(attacker, defender, attacker_left_health, defender_left_health):
	attacker_role = attacker.character_type
	defender_role = defender.character_type
	attacker_luck_value = attacker.fortune
	defender_luck_value = defender.fortune


	if attacker_left_health:
		attacker_health = attacker_left_health
	else:
		attacker_health = attacker.health_point * 30
	
	if defender_left_health:
		defender_health = defender_left_health
	else:
		defender_health = defender.health_point * 30

	attacker_health_value_list = []
	defender_health_value_list = []
	attacker_health_value_list.append(int(attacker_health))
	defender_health_value_list.append(int(defender_health))

	print('KEZDO ÉLETERO: ATTACKER - DEFENDER', attacker_health, defender_health)

	# a casthoz tartozó fő tulajdonságok meghatározása
	"""
	harcos - harcos
	harcos - mágus
	harcos - íjász
	mágus - mágus
	mágus - íjász
	íjász - íjász


	mágus - harcos
	íjász - harcos
	íjász - mágus
	"""
	if attacker_role == 'warrior' and defender_role == 'warrior':
		attacker_main_attr_value = attacker.strength
		defender_main_attr_value = defender.strength
		attacker_protect_attr_value = 0
		defender_protect_attr_value = 0

	elif attacker_role == 'warrior' and defender_role == 'mage':
		attacker_main_attr_value = attacker.strength
		defender_main_attr_value = defender.intelligence
		attacker_protect_attr_value = attacker.intelligence
		defender_protect_attr_value = defender.strength

	elif attacker_role == 'warrior' and defender_role == 'scout':
		attacker_main_attr_value = attacker.strength
		defender_main_attr_value = defender.skill
		attacker_protect_attr_value = attacker.skill
		defender_protect_attr_value = defender.strength

	elif attacker_role == 'mage' and defender_role == 'mage':
		attacker_main_attr_value = attacker.intelligence
		defender_main_attr_value = defender.intelligence
		attacker_protect_attr_value = 0
		defender_protect_attr_value = 0

	elif attacker_role == 'mage' and defender_role == 'scout':
		attacker_main_attr_value = attacker.intelligence
		defender_main_attr_value = defender.skill
		attacker_protect_attr_value = attacker.skill
		defender_protect_attr_value = defender.intelligence

	elif attacker_role == 'scout' and defender_role == 'scout':
		attacker_main_attr_value = attacker.skill
		defender_main_attr_value = defender.skill
		attacker_protect_attr_value = 0
		defender_protect_attr_value = 0

	elif attacker_role == 'mage' and defender_role == 'warrior':
		attacker_main_attr_value = attacker.intelligence
		defender_main_attr_value = defender.strength
		attacker_protect_attr_value = attacker.strength
		defender_protect_attr_value = defender.intelligence

	elif attacker_role == 'scout' and defender_role == 'warrior':
		attacker_main_attr_value = attacker.skill
		defender_main_attr_value = defender.strength
		attacker_protect_attr_value = attacker.strength
		defender_protect_attr_value = defender.skill

	elif attacker_role == 'scout' and defender_role == 'mage':
		attacker_main_attr_value = attacker.skill
		defender_main_attr_value = defender.intelligence
		attacker_protect_attr_value = attacker.intelligence
		defender_protect_attr_value = defender.skill


	did_attacker_win = False

	
	
	#kiszámoljuk hány % eséllyel sebez többet 
	if attacker_luck_value > defender_luck_value:
		attacker_bonus_damage_percent = round((defender_luck_value / attacker_luck_value) * 100)
		if attacker_bonus_damage_percent > 50:
			attacker_bonus_damage_percent = 50
		defender_bonus_damage_percent = 50 - attacker_bonus_damage_percent
	elif attacker_luck_value < defender_luck_value:
		defender_bonus_damage_percent = round((attacker_luck_value / defender_luck_value) * 100)
		if defender_bonus_damage_percent > 50:
			defender_bonus_damage_percent = 50
		attacker_bonus_damage_percent = 50 - defender_bonus_damage_percent
	else:
		attacker_bonus_damage_percent = 0
		defender_bonus_damage_percent = 0 # a randomnal pedig mivel 100-0 az 100, ezért 100% hogy mindig a 0-as szorzót választja

	print(attacker_bonus_damage_percent, "----", defender_bonus_damage_percent)

	damage_multiplier = [0, 1]




	while True:
		# mindig a támadó kezd tehát mindig a védekező sérül először

		attacker_added_damage = random.choices(damage_multiplier, weights=(100-attacker_bonus_damage_percent, attacker_bonus_damage_percent), k=1)[0]


		attacker_damage = (attacker_main_attr_value * 10) - (defender_protect_attr_value * 4) + (200 * attacker_added_damage)
		if attacker_damage <= 0:
			attacker_damage = 10
		defender_health -= attacker_damage





		if defender_health <= 0:
			defender_health_value_list.append(int(0))
			did_attacker_win = True
			break

		defender_health_value_list.append(int(defender_health))

		# ha nem halt meg a védekező, akkor ő jön, a támadó sebződik
		defender_added_damage = random.choices(damage_multiplier, weights=(100-defender_bonus_damage_percent, defender_bonus_damage_percent), k=1)[0]

		defender_damage = (defender_main_attr_value * 10) - (attacker_protect_attr_value * 4) + (200 * defender_added_damage)
		if defender_damage <= 0:
			defender_damage = 10
		attacker_health -= defender_damage


		if attacker_health <= 0:
			attacker_health_value_list.append(int(0))
			break


		attacker_health_value_list.append(int(attacker_health))
		#print('DEF HEALTH', defender_health)
		#print('ATTACK HEALTH', attacker_health)


	#print('ATTACKER HEALTH LIST', attacker_health_value_list)
	#print('DEFENDER_HEALTH_LIST', defender_health_value_list)

	if did_attacker_win:
		return attacker, attacker_health_value_list, defender_health_value_list

	return defender, attacker_health_value_list, defender_health_value_list
