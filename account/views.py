from django.shortcuts import render, redirect
from .models import *
from .forms import AccountRegistrationForm, AccountEditForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .decorators import anonymous_user

from django.views.generic import ListView
import json

from django.http import HttpResponse, JsonResponse
from django.contrib import messages

from core.constants import STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET
from django.conf import settings 
import os
import re

from datetime import datetime
from core.constants import *

@anonymous_user
def register_page_view(request):
	form = AccountRegistrationForm()
	character_type = None
	if request.method == 'POST':
		form = AccountRegistrationForm(request.POST)

		if form.is_valid():
			user = form.save()
			character_type = form.cleaned_data.get('character_type')
			if character_type == Character.ROLES[0][0]: #'warrior'
				set_warrior(user)
			elif character_type == Character.ROLES[1][0]: # 'mage'
				set_mage(user)
			elif character_type == Character.ROLES[2][0]:# 'scout'
				set_scout(user)
			else:
				pass # admin user has the default values


			updateRank()


			return redirect('login')
		
		else:
			character_type = form.cleaned_data.get('character_type')

	context = {
			'form':form,
			'character_type': character_type,
		}


	return render(request, 'account/register.html', context)


@anonymous_user
def login_page_view(request):

	if request.method == 'POST':
		username = request.POST['username'] # input name-ből jön
		password = request.POST['password']

		user = authenticate(request, username=username, password=password)

		if user is not None:
			login(request, user)
			return redirect('home_page')
		else:
			messages.info(request, 'Hibás adatok!')


	context = {}

	return render(request, 'account/login.html', context)

@login_required(login_url='login')
def logout_view(request):
	logout(request)

	return redirect('login')


@login_required(login_url='login')
def profile_view(request, *args, **kwargs):
	context = {}

	user_id = kwargs.get('user_id')
	try:
		account = Account.objects.get(id=user_id)
	except Account.DoesNotExist:
		return HttpResponse('Account does not exist')

	owner_of_the_profile = False

	if request.user.id == account.id: 
		owner_of_the_profile = True


	# ha az adott felhasználói profilnak van profilképe állítsa be amúgy az alap
	if account.profile_image:
		profile_image = account.profile_image.url
		#print(account.get_profile_image_filename())
	else:
		profile_image = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET

	if not len(account.team_set.all()) == 0:
		team = account.team_set.all()[0]
		member_count = len(team.users.all())
	else:
		team = None
		member_count = None

	character_history = CharacterHistory.objects.get(account=account.id)
	character_fights_played = character_history.fights_played
	character_fights_won = character_history.fights_won
	character_fights_lost = character_history.fights_lost

	last_login_date = account.last_login.strftime("%Y-%m-%d %H:%M")
	date_joined_date = account.date_joined.strftime("%Y-%m-%d")

	context = {
		'user_id': account.id,
		'username': account.username,
		'date_joined': date_joined_date,
		'last_login': last_login_date,
		'description': account.description,
		'profile_image': profile_image,
		'character_type': account.character.character_type,
		'level': account.character.level,
		'strength': account.character.strength,
		'skill': account.character.skill,
		'intelligence': account.character.intelligence,
		'health_point': account.character.health_point,
		'fortune': account.character.fortune,
		'rank': account.character.rank,
		'honor': account.character.honor,
		'gold': account.character.gold,
		'current_xp': account.character.current_xp,
		'next_level_xp': account.character.next_level_xp,
		'team': team,
		'team_member_count': member_count,
		'is_owner': owner_of_the_profile,
		'fights_count': character_fights_played,
		'fights_won_count': character_fights_won,
		'fights_lost_count': character_fights_lost,
	}





	return render(request, 'account/profile.html', context)


@login_required(login_url='login')
def edit_profile_view(request, *args, **kwargs):
	context = {}
	#print(','.join('{0}={1!r}'.format(k,v) for k,v in kwargs.items()))
	user_id = kwargs.get('user_id')


	try:
		account = Account.objects.get(id=user_id)
	except Account.DoesNotExist:
		return HttpResponse('A felhasználó nem létezik!')

	if request.user.id != account.id:
		return HttpResponse('Nem szerkesztheted más játékosok profilját!')


	# itt már biztosan mi akarjuk szerkeszteni a profilunkat
	
	form = AccountEditForm(instance=account)

	error_message = ""

	if request.method == 'POST':
		form = AccountEditForm(request.POST, request.FILES, instance=account)
		if form.is_valid():
			try:
				# a try-catch block a jelszó kezelést tartalmazza 
				password_value_1 = request.POST['password1']
				password_value_2 = request.POST['password2']

				if len(password_value_1) > 0:
					data = validate_password_edit_profile(password_value_1, password_value_2)
					if data['error_code'] == 0:
						if not account.check_password(password_value_1):
							# a check_password igaz, hogyha a megadott jelszó egyezik a jelenlegi jelszóval
							print('megfelelo erossegu és nem egyezik az elozovel')
							account.set_password(password_value_1)
							account.save()
							form.save()

							return redirect('profile', user_id=account.id)
						else:
							print('megfelelo erossegu de egyezik az elozovel')
							error_message = 'A jelszó megegyezik az előzővel'
					else:
						print('nem megfelelo erossegu')
						error_message = data['message']
				else:
					form.save()
					return redirect('profile', user_id=account.id)

			except Exception as exception:
				form.save()
				return redirect('profile', user_id=account.id)
				



	current_username = account.username
	current_email = account.email

	if account.profile_image:
		current_profile_image = account.profile_image.url
	else:
		current_profile_image = ""


	context = {
		'form': form,
		'username': current_username,
		'email': current_email,
		'profile_image': current_profile_image,
		'error_message': error_message,
	}

	return render(request, 'account/edit_profile.html', context)


def validate_password_edit_profile(password1, password2):
	data = {}

	if len(password1) < 6:
		data['error_code'] = 1
		data['message'] = 'A jelszónak legalább 6 karakternek kell legyen'
		return data
	if sum(character.isdigit() for character in password1) < 1:
		data['error_code'] = 1
		data['message'] = 'A jelszónak tartalmaznia kell legalább 1 számot'
		return data
	if not any (character.islower() for character in password1):
		data['error_code'] = 1
		data['message'] = 'A jelszónak tartalmaznia kell legalább 1 kisbetűt'
		return data
	if not any (character.isupper() for character in password1):
		data['error_code'] = 1
		data['message'] = 'A jelszónak tartalmaznia kell legalább 1 nagybetűt'
		return data

	if password1 != password2:
		data['error_code'] = 1
		data['message'] = 'A két jelszó nem egyezik'
		return data


	data['error_code'] = 0
	data['message'] = 'Megfelelő'
	return data


def validate_username_realtime(request):
	username = request.GET.get('username')

	is_long_enough = False
	is_available = not Account.objects.filter(username=username).exists()
	if len(username) > 0:
		is_long_enough = True

	data = {
		'is_available': is_available,
		'is_long_enough': is_long_enough,
	}

	return JsonResponse(data)

# https://www.geeksforgeeks.org/check-if-email-address-valid-or-not-in-python/

def validate_email_realtime(request):
	email = request.GET.get('email')


	is_valid = False
	is_available = not Account.objects.filter(email=email).exists()

	regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
	value = re.fullmatch(regex, email)

	if value:
		is_valid = True

	data = {
		'is_available': is_available,
		'is_valid': is_valid,
	}

	return JsonResponse(data)


def validate_password_realtime(request):
	password = request.GET.get('password')

	is_strong = False

	print(len(password))

	if len(password) >= 6:
		if sum(character.isdigit() for character in password) >= 1:
			if any (character.islower() for character in password):
				if any (character.isupper() for character in password):
					is_strong = True

	return JsonResponse({'is_strong': is_strong})




def increase_attribute_value(request, *args, **kwargs):
	data = {}
	if request.method == 'POST':	
		user_id = request.POST.get('user_id')
		attr_type = request.POST.get('attribute_type')
		user = Character.objects.get(account=user_id)
		print('USERNAME ', user.account.username, ' ATTR ', attr_type)

		if (user.gold)- DEFAULT_ATTRIBUTE_INCREASE_VALUE >= 0: 
			if attr_type == 'strength':
				user.strength += 1
				user.gold -= DEFAULT_ATTRIBUTE_INCREASE_VALUE
				user.save()
				data['new_attr_value'] = str(user.strength)

			elif attr_type == 'skill':
				user.skill += 1
				user.gold -= DEFAULT_ATTRIBUTE_INCREASE_VALUE
				user.save()
				data['new_attr_value'] = str(user.skill)

			elif attr_type == 'intelligence':
				user.intelligence += 1
				user.gold -= DEFAULT_ATTRIBUTE_INCREASE_VALUE
				user.save()
				data['new_attr_value'] = str(user.intelligence)

			elif attr_type == 'health_point':
				user.health_point += 1
				user.gold -= DEFAULT_ATTRIBUTE_INCREASE_VALUE
				user.save()
				data['new_attr_value'] = str(user.health_point)


			elif attr_type == 'fortune':
				user.fortune += 1
				user.gold -= DEFAULT_ATTRIBUTE_INCREASE_VALUE
				user.save()
				data['new_attr_value'] = str(user.fortune)

			data['new_gold_value'] = user.gold
			data['message'] = 'Success'
			data['attr_type'] = attr_type
		else: 
			data['message'] = 'Out of gold'


	return JsonResponse(data)


def save_description(request):
	data = {}
	user_id = request.GET.get('user_id')
	description = request.GET.get('description')

	try:
		user = Account.objects.get(id=user_id)
		user.description = description
		user.save()
		data['message'] = 'Success'
	except Exception as exception:
		print(exception)
		data['message'] = 'Error'
		pass



	return JsonResponse(data)




def set_warrior(user):
	profile = Character.objects.get(account=user)

	profile.character_type = Character.ROLES[0][0]

	#re-define attribute values based on role type
	profile.strength = 10
	profile.skill = 5
	profile.intelligence = 5
	profile.health_point = 12
	profile.fortune = 7



	profile.save()


def set_mage(user):
	profile = Character.objects.get(account=user)

	profile.character_type = Character.ROLES[1][0]

	#re-define attribute values based on role type
	profile.strength = 6
	profile.skill = 5
	profile.intelligence = 12
	profile.health_point = 8
	profile.fortune = 6

	profile.save()


def set_scout(user):
	profile = Character.objects.get(account=user)

	profile.character_type =  Character.ROLES[2][0]

	#re-define attribute values based on role type
	profile.strength = 7
	profile.skill = 11
	profile.intelligence = 7
	profile.health_point = 9
	profile.fortune = 8

	profile.save()



def updateRank():
	print('updating ranks...')
	rank_counter = 1
	characters = Character.objects.get_all_characters_in_ordered_list_without_admins()

	for character in characters:
		character.rank = rank_counter
		rank_counter += 1
		character.save()
