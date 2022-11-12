from django.shortcuts import render
from django.conf import settings

from .models import *
from account.models import Account
from django.contrib.auth.decorators import login_required

from itertools import chain
from core.constants import *


from private_chat.utils import create_or_get_private_chat
import json
from django.http import HttpResponse

from datetime import datetime




@login_required(login_url='login')
def private_chat_page_view(request, *args, **kwargs):
	#print("SZOBA ID", request.GET.get('szoba_id'))
	user = request.user
	room_id = request.GET.get('szoba_id')

	context = {}

	if room_id:
		try:
			room = PrivateChatRoom.objects.get(id=room_id)
			context['room'] = room
		except PrivateChatRoom.DoesNotExist:
			print('PrivChatroomDoesNotExists')
			pass


	# Összes szoba amiben a felhasználó benne van
	rooms_parameter_user1 = PrivateChatRoom.objects.filter(user1=user)
	rooms_parameter_user2 = PrivateChatRoom.objects.filter(user2=user)

	rooms = list(chain(rooms_parameter_user1, rooms_parameter_user2)) # mergeli és eltávolítja a duplikált elemeket

	#[{'message:' 'mizu', 'user': 'tamadam'}, {'message:' 'semmi kul', 'user': 'harcos'}]
	messages_and_users = []
	users = []
	for room in rooms:
		if room.user1 == user:
			other_user = room.user2
		else:
			other_user = room.user1

		try:
			profile_image = other_user.profile_image.url
		except Exception as e:
			profile_image = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET

		try:
			recent_message = PrivateChatRoomMessage.objects.filter(room=room).order_by('-sending_time')[0]
		except:
			recent_message = (f'{room.user1} létrehozta a szobát')
		"""
		strhez a sending timeot is hozza kell adni
		print('heh')
		recent_message_list = str(recent_message).split()
		recent_message = recent_message_list[0] # csak a message
		date_string = recent_message_list[1] + " " + recent_message_list[2] # a dátum
		print(date_string)
		print('heh vege')
		#print(PrivateChatRoomMessage.objects.filter(room=room).order_by('-sending_time')[0])
		"""
		try:
			recent_message_sending_time = PrivateChatRoomMessage.objects.filter(room=room).order_by('-sending_time')[0].get_sending_time() # megkaptuk a legutolso uzenet kuldesi datumat
		except:
			# abban az esetben ha még nincs üzenet a szobában, küldési idő sem lehet, default érték
			recent_message_sending_time = DEFAULT_SENDING_TIME
		has_new_messages = False
		try:
			unread_messages_count = UnreadPrivateChatRoomMessages.objects.get(room=room, user=user).unread_messages_count
			#print(unread_messages_count)
			#print('letezik')

			if unread_messages_count > 0:
				has_new_messages = True
			else:
				has_new_messages = False
		except:
			#print('nem letezik')
			pass




		messages_and_users.append({
				'message': recent_message,
				'recent_message_sending_time': recent_message_sending_time,
				'other_user': other_user,
				'profile_image': profile_image,
				'has_new_messages': has_new_messages,
			})




	messages_and_users = sorted(messages_and_users, key=lambda x: x['recent_message_sending_time'], reverse=True)

	try:
		account = Account.objects.get(id=request.user.id)
	except:
		account = None
		pass



	context['debug_mode'] = settings.DEBUG
	context['messages_and_users'] = messages_and_users
	context['account'] = account
	context['len_messages_and_users'] = len(messages_and_users)

	return render(request, 'private_chat/private_chat_room.html', context)


@login_required(login_url='login')
def create_or_return_private_chat(request, *args, **kwargs):
	user1 = request.user
	context = {}
	if user1.is_authenticated:
		if request.method == 'POST':
			user2_id = request.POST.get('user2_id')
			try:
				user2 = Account.objects.get(id=user2_id)
				chat = create_or_get_private_chat(user1, user2)
				context['message'] = SUCCESS_MESSAGE_ON_FINDING_PRIVATE_CHAT
				context['private_chat_room_id'] = chat.id
			except Account.DoesNotExist:
				payload['message'] = 'Error when getting private chat'
	else:
		payload['message']: 'Authentication failure'

	return HttpResponse(json.dumps(context), content_type='application/json')



def refresh_page_part_view(request):
	
	user = request.user


	context = {}

	# Összes szoba amiben a felhasználó benne van
	rooms_parameter_user1 = PrivateChatRoom.objects.filter(user1=user)
	rooms_parameter_user2 = PrivateChatRoom.objects.filter(user2=user)

	rooms = list(chain(rooms_parameter_user1, rooms_parameter_user2)) # mergeli és eltávolítja a duplikált elemeket

	#[{'message:' 'mizu', 'user': 'tamadam'}, {'message:' 'semmi kul', 'user': 'harcos'}]
	messages_and_users = []
	users = []
	for room in rooms:
		if room.user1 == user:
			other_user = room.user2
		else:
			other_user = room.user1

		try:
			profile_image = other_user.profile_image.url
		except Exception as e:
			profile_image = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET

		try:
			recent_message = PrivateChatRoomMessage.objects.filter(room=room).order_by('-sending_time')[0]
		except:
			recent_message = (f'{room.user1} létrehozta a szobát')
		"""
		strhez a sending timeot is hozza kell adni
		print('heh')
		recent_message_list = str(recent_message).split()
		recent_message = recent_message_list[0] # csak a message
		date_string = recent_message_list[1] + " " + recent_message_list[2] # a dátum
		print(date_string)
		print('heh vege')
		#print(PrivateChatRoomMessage.objects.filter(room=room).order_by('-sending_time')[0])
		"""
		try:
			recent_message_sending_time = PrivateChatRoomMessage.objects.filter(room=room).order_by('-sending_time')[0].get_sending_time() # megkaptuk a legutolso uzenet kuldesi datumat
		except:
			# abban az esetben ha még nincs üzenet a szobában, küldési idő sem lehet, default érték
			recent_message_sending_time = DEFAULT_SENDING_TIME

		messages_and_users.append({
				'message': recent_message,
				'recent_message_sending_time': recent_message_sending_time,
				'other_user': other_user,
				'profile_image': profile_image,
			})




	messages_and_users = sorted(messages_and_users, key=lambda x: x['recent_message_sending_time'], reverse=True)



	context['debug_mode'] = settings.DEBUG
	context['messages_and_users'] = messages_and_users

	return HttpResponse(context)
