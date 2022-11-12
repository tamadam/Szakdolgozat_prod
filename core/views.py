from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from account.models import *
from operator import attrgetter
from django.conf import settings

import json
from django.http import HttpResponse, JsonResponse

from core.constants import *
from team.models import Team

from django.core.serializers.python import Serializer
from django.core.paginator import Paginator
from django.core.serializers import serialize


from account.utils import EncodeAccountObject, EncodeCharacterObject
from team.utils import EncodeTeamObject

@login_required(login_url='login')
def home_page_view(request):
	#user = Character.objects.get(account=request.user)
	#print(user.health_point, user.character_type)
	context = {} 

	user = Character.objects.get(account=request.user)

	context = {
		'user_id': user.account.id,
		'username': user.account.username,
		'character_type': user.character_type,
	}

	print("CHARTYPE",user.character_type)

	return render(request, 'core/home_page.html', context)





# beepitve mar a modellben, törlendo
def get_all_characters_without_admins():
	"""
	users = Account.objects.exclude(is_admin=True)
	characters = []
	for user in users:
		characters.append(Character.objects.get(account=user))
	return characters
	"""

	return [Character.objects.get(account=user) for user in Account.objects.exclude(is_admin=True)]



@login_required(login_url='login')
def users_search_view(request):
	"""
	characters = get_all_characters_without_admins()

	#characters = sorted(characters, key=lambda character: character.level, reverse=True)
	# docs : https://wiki.python.org/moin/HowTo/Sorting#Sortingbykeys

	try:
		characters = sorted(characters, key=lambda character: character.account.date_joined) # először date szerint orderelünk
		characters = sorted(characters, key=attrgetter('honor','level'), reverse=True) # utana a mar rendezett listat honor és level szerint
	except:
		characters = sorted(characters, key=attrgetter('honor','level', 'account.username'), reverse=True)  # minimális az esély arra, hogy 2 felhasználó ms-re pontosan 
													# egyszerre regisztráljon, de ilyen esetben ez egy alternativ rendezési lehetőség,
													# a sorrend lényegén nem fog változtatni
	"""
	# EZ IS A MODELLBEN VAN MAR BEEPITVE
	#for character in characters:
		#dates_tmp.append(character.account.date_joined)
	#print(characters)
	search_team = request.GET.get('csapat')
	characters = Character.objects.get_all_characters_in_ordered_list_without_admins()


	try:
		account_id = request.user.id
		account = Account.objects.get(id=account_id)
		try:
			account_team_id = account.team_set.all()[0].id
		except:
			account_team_id = None

	except Exception as e:
		account_id = None
		account_team_id = None


	teams = Team.objects.all()

	if search_team:
		search_team = 'exists'
	else:
		search_team = 'none'

	context = {
		'characters': characters,
		'teams': teams,
		'account_id': account_id,
		'account_team_id': account_team_id,
		'search_team': search_team,
		}


	#try_pagination()

	return render(request, 'core/search_users.html', context)


"""
def list_accounts(request):
	characters = Account.objects.exclude(is_admin=True)
	print(type(characters))
	context = {
		'characters': characters,
	}
	return JsonResponse({'characters': list(characters.values())})
"""



def load_users_pagination(request):
	try:

		accounts = Character.objects.get_all_accounts_in_ordered_list_without_admins()

		characters = Character.objects.get_all_characters_in_ordered_list_without_admins()

		data = {}
		page_number = request.GET.get('page_number')

		load_page_number = int(page_number)

		print('PAGE NUMBER' + page_number)
		p = Paginator(characters, 8) # 8 azt jelenti hogy ennyi profilt jelenitunk meg egyszerre a felületen(8-esével)


		print('numpages', p.num_pages)

		if load_page_number <= p.num_pages:
			load_page_number = load_page_number + 1

			s = EncodeCharacterObject()

			print(s.serialize(p.page(page_number).object_list))
			print('next')

			data['users'] = s.serialize(p.page(page_number).object_list)
		else:
			data['users'] = 'None'

		data['load_page_number'] = load_page_number



		return JsonResponse(data)

	except Exception as exception:
		print('Error when getting users' + str(exception))

	return None


def load_teams_pagination(request):
	try:

		teams = Team.objects.get_all_teams_in_ordered_list()

		data = {}
		page_number = request.GET.get('page_number')

		load_page_number = int(page_number)

		print('PAGE NUMBER' + page_number)
		p = Paginator(teams, 8) 


		print('numpages', p.num_pages)

		if load_page_number <= p.num_pages:
			load_page_number = load_page_number + 1

			s = EncodeTeamObject()

			print(s.serialize(p.page(page_number).object_list))
			print('next')
			print(load_page_number)

			data['teams'] = s.serialize(p.page(page_number).object_list)
		else:
			data['teams'] = 'None'

		data['load_page_number'] = load_page_number



		return JsonResponse(data)

	except Exception as exception:
		print('Error when getting users' + str(exception))

	return None


def get_search_results(request):
	data = {}

	searched_text = request.GET.get('searched_text')
	search_bar_users = request.GET.get('search_bar_users')

	results = None
	if search_bar_users == 'true':
		print('USER SEARCH')
		#s = EncodeAccountObject()
		s = EncodeCharacterObject()

		character_results = []

		if len(searched_text) > 0:
			accounts = Account.objects.filter(is_admin=False).filter(username__icontains=searched_text) # a kis/nagybetű nem számít
			character_results = [Character.objects.get(account=account.id) for account in accounts]
			character_results = sorted(character_results, key=lambda character: character.rank)
			results = s.serialize(character_results)
			#results = s.serialize(Account.objects.filter(is_admin=False).filter(username__icontains=searched_text)) # a kis/nagybetű nem számít


		#print(searched_text)
		print('USER RESULTS')
		print(results)

		print(character_results)
	else:
		print('TEAM SEARCH')
		t = EncodeTeamObject()

		team_results = []

		if len(searched_text) > 0:
			teams = Team.objects.filter(name__icontains=searched_text)
			team_results = sorted(teams, key=lambda team: team.honor, reverse=True) 
			results = t.serialize(team_results)

		print(results)

	data = {
		'results': results,
	}

	return JsonResponse(data)