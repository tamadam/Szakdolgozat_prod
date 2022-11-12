from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from account.models import Account, Character
from .models import Team, Membership, TeamMessage, TeamJoinRequest
from .forms import TeamCreationForm
from django.conf import settings
import json

from core.constants import *

from django.http import HttpResponse, JsonResponse



# https://docs.djangoproject.com/en/4.0/topics/db/models/#extra-fields-on-many-to-many-relationships




@login_required(login_url='login')
def user_team_view(request):
	context = {}

	try:
		user = Account.objects.get(id=request.user.id)
	except Exception as exception:
		print(exception)
		return HttpResponse('A felhasználó nem található!')

	try:
		user_team_id = user.team_set.all()[0].id
	except Exception as exception:
		user_team_id = None
		pass

	# ha a felhasználónak van csapata, átirányítjuk a csapatának az oldalára
	if user_team_id:
		return redirect('team:individual_team_view', team_id=user_team_id)

	form = TeamCreationForm()

	# csapat létrehozása esetén
	if request.method == 'POST':
		form = TeamCreationForm(request.POST)

		if form.is_valid():
			team = form.save() # visszaadja a csapat objektumot
			Membership.objects.create(user=user, team=team) # hozzáadjuk a felhasználót a létrehozott csapathoz
			team.owner_of_team = user # beállítjuk a csapat tulajdonosának az aktuális usert
			team.save()
			update_team_rank()
			return redirect('team:individual_team_view', team_id=team.id)

	update_team_rank()
	
	context['form'] = form

	return render(request, 'team/team_page.html', context)



def leave_team(request):
	context = {}
	user_id = request.POST.get('user_id')
	print('user_id' + user_id)
	user = Account.objects.get(id=user_id)
	print('felhasznalo' + user.username)
	try:
		team_id = user.team_set.all()[0].id
	except Exception as e:
		print(f'Team id not found for user {request.user} ' + str(e))
	try:
		user_team = Team.objects.get(id=team_id)
	except Exception as e:
		print(f'Team id not found in leave team ' + str(e))

	# errort dobhat ha a try utan except van


	print('A CSAPAT TULAJDONOSA', user_team.owner_of_team)
	print(user_team.owner_of_team == user)

	# felhasználó törlése a csapatból
	user_team.users.remove(user)

	# ha a csapat tulajdonosa lép ki, az új tulajd átállítása
	if user_team.owner_of_team == user:
		# csak akkor tudunk kinevezni másik tulajt, ha van még valaki a csapatban
		if len(user_team.users.all()) > 0:
			print("ATIRAS")
			team_mates = Membership.objects.filter(team=user_team) # csapattagok 
			new_owner = sorted(team_mates, key=lambda team_mate: team_mate.date_joined)[0].user # a legrégebben csatlakozott felhasználó lesz az új tulaj
			user_team.owner_of_team = new_owner
			user_team.save()





	# ha a csapatnak nincs több tagja, a csapat is törlődik
	if len(user_team.users.all()) == 0:
		Team.objects.get(id=team_id).delete()
		context['team_is_deleted'] = True
	else:
		context['team_is_deleted'] = False


	context['message'] = 'siker'

	return HttpResponse(json.dumps(context), content_type='application/json')


def fire_team_mate(request):
	data = {}

	user_id = request.GET.get('user_id')
	user = Account.objects.get(id=user_id)

	try:
		team_id = user.team_set.all()[0].id
	except Exception as e:
		print(f'Team id not found for user {request.user} ' + str(e))
	try:
		user_team = Team.objects.get(id=team_id)
	except Exception as e:
		print(f'Team id not found in leave team ' + str(e))



	# felhasználó törlése a csapatból
	user_team.users.remove(user)

	
	return JsonResponse(data)


def accept_user_join(request):
	data = {}

	user_id = request.GET.get('user_id')
	user = Account.objects.get(id=user_id)

	team_id = request.GET.get('team_id')
	team = Team.objects.get(id=team_id)

	# hozzáadás a csapathoz
	#Membership.objects.create(user=user, team=team)


	# ha van a felhasználónak függő csatlakozási kérelme 
	if TeamJoinRequest.objects.filter(user=user).exists():
		# ha van a felhasználónak függő csatlakozási kérelme a csapathoz 
		if TeamJoinRequest.objects.filter(user=user, team=team).exists():
			# töröljük az összes csatlakozási kérelmet ami a felhasználóhoz köthető
			TeamJoinRequest.objects.filter(user=user).delete()
			# hozzáadás a csapathoz
			Membership.objects.create(user=user, team=team)
			data['is_joined'] = 'joined'
	else:
		data['is_joined'] = 'not_joined'

	data['message'] = 'success'

	return JsonResponse(data)


def decline_user_join(request):
	data = {}

	user_id = request.GET.get('user_id')
	user = Account.objects.get(id=user_id)

	team_id = request.GET.get('team_id')
	team = Team.objects.get(id=team_id)

	if TeamJoinRequest.objects.filter(user=user, team=team).exists():
		TeamJoinRequest.objects.filter(user=user, team=team).delete()

	data['message'] = 'success'

	return JsonResponse(data)


def send_join_request(request):
	data = {}

	user_id = request.GET.get('user_id')
	user = Account.objects.get(id=user_id)

	team_id = request.GET.get('team_id')
	team = Team.objects.get(id=team_id)

	print(user, team)

	# ha már van request az adott csapathoz, ne hozzon létre mégegyet
	if not TeamJoinRequest.objects.filter(user=user, team=team).exists():
		TeamJoinRequest.objects.create(user=user, team=team)
		data['request_state'] = "created"
	else:
		data['request_state'] = "exists"




	return JsonResponse(data)



@login_required(login_url='login')
def individual_team_view(request, *args, **kwargs):
	context = {}


	team_id = kwargs.get('team_id')

	try: 
		team = Team.objects.get(id=team_id)
	except Team.DoesNotExist:
		return HttpResponse('Team does not exists')
	try:
		user = Account.objects.get(id=request.user.id)
	except Account.DoesNotExist:
		return HttpResponse('Account does not exists')

	# ellenőrizzük, hogy az adott csapatban benne van-e a user
	# ha nincs, akkor ellenőrizzük azt, hogy van-e csapata 
	has_team = True
	is_own_team = True

	# ez a másik csapat támadásához szükséges
	# csak a csapat tulaja támadhat más csapatokat
	has_team_and_owner_of_team = False
	attacker_team = None

	try:
		team_membership = Membership.objects.get(user=user.id, team=team.id)
		#print('csapattag')
	except Membership.DoesNotExist:
		#print('nem csapattag')
		is_own_team = False
		try:
			membership = Membership.objects.get(user=user.id)
			#print('van csapata')
			if membership.team.owner_of_team == user:
				has_team_and_owner_of_team = True
				attacker_team = user.team_set.all()[0]

		except Membership.DoesNotExist:
			#print('nincs csapata')
			has_team = False

	try:
		account = Account.objects.get(id=request.user.id)
	except:
		account = None
		pass

	# a leíráshoz használom, hogy csakis a tulajdonos tudja módosítani
	# másik felhasználó, még a csapattársnak sem engedett
	is_team_owner_description = False
	if team.owner_of_team == user:
		is_team_owner_description = True


	team_members = []
	for team_member in team.users.all():
		print("csapattag", team_member)

		try:
			profile_image = team_member.profile_image.url
		except Exception as e:
			profile_image = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET

		is_team_owner = False
		if team.owner_of_team == team_member:
			is_team_owner = True


		team_members.append({
				'member': team_member,
				'member_profile_image': profile_image,
				'is_team_owner': is_team_owner,
			})

	
	pending_requests_all = TeamJoinRequest.objects.get_all_requests(team)

	pending_requests = []

	for pending_request in pending_requests_all:

		try:
			profile_image = pending_request.user.profile_image.url
		except Exception as e:
			profile_image = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET

		print('pending_request', pending_request)

		pending_requests.append({
				'user_id': pending_request.user.id,
				'user': pending_request.user,
				'profile_image': profile_image,
			})


	context = {
		'team': team,
		'team_members': team_members,
		'is_own_team': is_own_team,
		'has_team': has_team,
		'user_id': user.id,
		'account': account,
		'is_team_owner_description': is_team_owner_description,
		'pending_requests': pending_requests,
		'has_team_and_owner_of_team': has_team_and_owner_of_team,
		'attacker_team': attacker_team,
	}

	# CHAT RÉSZ ------------------------

	context['debug_mode'] = settings.DEBUG


	return render(request, 'team/individual_team.html', context)



def update_team_rank():
	print('updating team ranks...')
	rank_counter = 1
	teams = Team.objects.all()
	teams = sorted(teams, key=lambda team: team.honor, reverse=True)

	for team in teams:
		team.rank = rank_counter
		rank_counter += 1
		team.save()


def save_team_description(request):
	data = {}
	user_id = request.GET.get('user_id')
	description = request.GET.get('description')

	try:
		user = Account.objects.get(id=user_id)
		team = user.team_set.all()[0]
		team.description = description
		team.save()
		data['message'] = 'Success'
	except Exception as exception:
		print(exception)
		data['message'] = 'Error'
		pass


	return JsonResponse(data)