from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

import json

# Az exception kezelő osztály és függvény
from public_chat.exceptions import ClientError, handle_client_error

# Gyakran használt konstansok
from core.constants import *

# Modellek
from .models import *

# Account object szerializálása
from account.utils import EncodeAccountObject

# Küldési idő kalkulálása
from public_chat.utils import *
from django.utils import timezone


# Chat üzenetek betöltése (pagination)
from django.core.serializers.python import Serializer
from django.core.paginator import Paginator
from django.core.serializers import serialize


# Értesítésekhez
from account.models import Account

# Aszinkron futtatáshoz
import asyncio



class PrivateChatRoomConsumer(AsyncJsonWebsocketConsumer):
	async def connect(self):
		"""
		Csatlakozáskor használjuk, a kezdeti fázisban mikor a szerver és a kliens websocket kapcsolatra vált
		Mindenkit hagyunk csatlakozni a websockethez, a jogot a chateléshez egy későbbi szakaszban ellenőrizzük
		"""

		print('PrivateChatConsumer: ' + str(self.scope['user']) + ' connected') 

		# csatlakozás elfogadása
		await self.accept()

		# definiáljuk a room_id változót, a későbiekkben ebben lesz eltárolva melyik szobában vagyunk
		self.room_id = None


	async def disconnect(self, code):
		"""
		Mikor bezáródik a websocket kapcsolat a szerver és kliens között
		"""

		print('PrivateChatConsumer: ' + str(self.scope['user']) + ' disconnected')

		try:
			if self.room_id != None:
				await self.leave_room(self.room_id)
		except Exception as exception:
			print('Exception during disconnect in PrivateChatConsumer' + str(exception))
			pass



	async def receive_json(self, content, **kwargs):
		"""
		Dekódolt JSON üzenet, akkor hívódik meg, mikor valamilyen parancs érkezik a template-től
		"""

		# https://www.w3schools.com/python/ref_dictionary_get.asp
		command = content.get('command', None) 
		room_id = content.get('room_id')
		user = self.scope['user']

		print('PrivateChatConsumer: receive_json called with command: ' + str(command))


		try:
			if command == 'send':
				message = content['message']
				if len(message.lstrip()) != 0: 
					await self.send_chat_message_to_room(room_id, message)
				else:
					raise ClientError('EMPTY_MESSAGE', 'Üres üzenet küldése nem lehetséges!')
			elif command == 'join':
				await self.join_room(room_id)
			elif command == 'leave':
				await self.leave_room(room_id)
			elif command == 'get_private_chat_room_messages':
				room = await get_private_chat_room(room_id, user)
				page_number = content['page_number']
				info_packet = await get_private_chat_room_messages(room, page_number)

				if info_packet != None:
					# JSON formátum átalakítása python szótárrá
					info_packet = json.loads(info_packet)

					await self.send_previous_messages_payload(info_packet['messages'], info_packet['load_page_number'])
				else:
					raise ClientError('NO_MESSAGES', 'Something went wrong when getting PrivateChatRoom messages')
			elif command == 'get_info_about_user':
				room = await get_private_chat_room(room_id, user)
				info_packet = await get_users(room, user)

				if info_packet != None:
					info_packet = json.loads(info_packet)

					await self.send_info_about_user_payload(info_packet['user_information'])
				else:
					raise ClientError('INFO_ERROR', 'Error when send info about user')
		except ClientError as exception:
			error = await handle_client_error(exception)
			await self.send_json(error)
			return



	async def send_chat_message_to_room(self, room_id, message):
		"""
		receive_json függvény hívja meg, mikor valaki üzenetet küld a chatszobába
		Ez a függvény kezdi meg azt a folyamatot, amely az üzenetet az egész csoportnak elküldi
		(privát chat révén jelen esetben a másik felhasználónak)
		"""
		user = self.scope['user']
		print('PrivateChatConsumer: send_chat_message_to_room from user: ' + user.username)

		# ellenőrizzük, hogy a szobában van-e az adott felhasználó
		if self.room_id != None:
			if str(room_id) != str(self.room_id):
				raise ClientError('ROOM_ACCESS_DENIED', 'You are not allowed to be in this room')
		else:
			raise ClientError('ROOM_ACCESS_DENIED', 'You are not allowed to be in this room')

		
		room = await get_private_chat_room(room_id, user)

		# értesiteshez
		# ASYNC consumer itt gyorsabb a három most következo async fuggveny lefuttathato egymastol fuggetlenul
		current_users = room.current_users.all()

		"""
		await asyncio.gather(*[
				add_or_update_unread_message(room.user1, room, current_users, message),
				add_or_update_unread_message(room.user2, room, current_users, message),
				save_private_chat_room_message(user, room, message)
			])
		print('HEY')
		"""


		user1, user2 = await get_user1_and_user2(room, user)

		await add_or_update_unread_message(user1, room, current_users, message)
		await add_or_update_unread_message(user2, room, current_users, message)

		# üzenet mentése az adatbázisba
		await save_private_chat_room_message(user, room, message)

		# ha valakinek nincs profilképe, az alapértelmezett profilképet kapja
		try:
			profile_image = user.profile_image.url
		except Exception as e:
			profile_image = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET


		await self.channel_layer.group_send(
			room.group_name,
			{
				'type': 'chat.message', # chat_message
				'user_id': user.id,
				'username': user.username,
				'profile_image': profile_image,
				'message': message
			}
		)

	async def chat_message(self, event):
		"""
		Akkor fut le, mikor valaki üzenetet küld a chatbe
		Itt történik a tényleges üzenet elküldés a templatehez(a kliensnek) 
		"""

		print('PrivateChatConsumer: chat_message from user: ' + str(event['username']))

		sending_time = create_sending_time(timezone.now())

		await self.send_json({
				'message_type': MESSAGE_TYPE_MESSAGE,
				'user_id': event['user_id'],
				'username': event['username'],
				'profile_image': event['profile_image'],
				'message': event['message'],
				'sending_time': sending_time,
			})


	async def join_room(self, room_id):
		"""
		Miután létrejött a websocket kapcsolat, küldünk egy payload-ot hogy a felhasználó csatlakozzon a szobához
		Mikor valaki join parancsot küld, akkor hívódik meg
		"""
		print('PrivateChatConsumer: join_room')
		user = self.scope['user']

		try:
			room = await get_private_chat_room(room_id, user)
		except ClientError as exception:
			error = await handle_client_error(exception)
			await self.send_json(error)
			return

		# tároljuk hogy a szobában vagyunk
		self.room_id = room_id

		# értesítésekhez
		await add_user_to_current_users(user, room)
		await reset_notification_count(user, room)


		# a channel(felhasználó tulajdonképpen) hozzáadása a csoporthoz, így megkapja mindenki az adott üzenetet
		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name
			)


		await self.send_json({
				'join': str(room_id),
				'username': user.username,
			})

		if user.is_authenticated:
			await self.channel_layer.group_send(
				room.group_name,
				{
					'type': 'join.chat',
					'room_id': room_id,
					'user_id': user.id,
					'username': user.username,
				}
				)


	async def leave_room(self, room_id):
		"""
		Mikor valaki leave parancsot küld, meghívódik
		"""
		print('PrivateChatConsumer: leave_room')
		user = self.scope['user']

		try:
			room = await get_private_chat_room(room_id, user)
		except ClientError as exception:
			error = await handle_client_error(exception)
			await self.send_json(error)
			return


		# értesítéshez
		await remove_user_from_current_users(user, room)


		await self.channel_layer.group_send(
			room.group_name,
			{
				'type': 'leave.chat',
				'room_id': room_id,
				'user_id': user.id,
				'username': user.username,
			}
		)

		self.room_id = None


		# felhasználó törlése a csoportból
		await self.channel_layer.group_discard(
			room.group_name,
			self.channel_name
			)

		# klienset utasítjuk hogy véglegesítse a kilépést
		await self.send_json({
				'leave': str(room.id)
			})


	async def send_previous_messages_payload(self, messages, load_page_number):
		"""
		Elküldi a viewnak a következő adag betöltött üzeneteket
		Csak az adott kliensnek küldi el, nem az egész csoportnak
		"""

		print('PrivateChatConsumer: send_loaded_messages_payload')

		await self.send_json({
				'message_packet': 'message_packet', # itt a keyword a lényeg, az onmessage függvény a kliens oldalon így fogja tudni kezelni
				'messages': messages,
				'load_page_number': load_page_number,
			})	


	async def send_info_about_user_payload(self, user_information):
		"""
		Ezzel a függvénnyel küldünk vissza a viewhoz felhasználói információt
		"""
		print('PrivateChatConsumer: send_info_about_user_payload')

		await self.send_json({
				'user_information': user_information,
			})


	async def join_chat(self, event):

		if event['username']:
			await self.send_json({
					'message_type': MESSAGE_TYPE_JOIN,
					'room_id': event['room_id'],
					'user_id': event['user_id'],
					'username': event['username'],
				})


	async def leave_chat(self, event):

		if event['username']:
			await self.send_json({
					'message_type': MESSAGE_TYPE_LEAVE,
					'room_id': event['room_id'],
					'user_id': event['user_id'],
					'username': event['username'],
				})



@database_sync_to_async
def get_private_chat_room(room_id, user):
	"""
	Privát chatszoba lekérése a felhasználóknak (ha létezik)
	"""

	try:
		room = PrivateChatRoom.objects.get(id=room_id)
	except PrivateChatRoom.DoesNotExist:
		raise ClientError('EXIST_ERROR', 'PrivateChatRoom does not exist')

	if user != room.user1 and user != room.user2:
		raise ClientError('ROOM_ACCESS_DENIED', 'You are not allowed to be in this room')


	return room



@database_sync_to_async
def save_private_chat_room_message(user, room, message):
	"""
	Elküldött üzenet mentése az adatbázisba
	"""
	return PrivateChatRoomMessage.objects.create(user=user, room=room, content=message)


@database_sync_to_async
def get_user1_and_user2(room, user):
	print('VLAMI')
	user1 = room.user1
	user2 = room.user2
	if user1 == user:
		user2 = room.user2
		user1 = room.user1

	print(f'felhasznalok: {user1} és {user2}')
	return user1, user2


@database_sync_to_async
def get_users(room, user):
	"""
	A szobában lévő felhasználókról információ lekérdezése
	- megállapítja, hogy az adott user az user1 vagy user2
	- ez alapján serializálja a megfelelő user objectet majd tér vissza ezzel az értékkel

	Felhasználó információ beszerzése a másik felhasználóról
	Visszatérési értéke: a felhasználóról az info vagy None
	"""
	other_user = room.user1
	curr_user = room.user2
	if other_user == user:
		other_user = room.user2
		curr_user = room.user1

	print(f'felhasznalok: {other_user} és {curr_user}')

	info_packet = {}

	s = EncodeAccountObject() # listát ad vissza

	info_packet['user_information'] = s.serialize([other_user])[0]
	return json.dumps(info_packet)




@database_sync_to_async
def get_private_chat_room_messages(room, page_number):
	"""
	Privát chatszoba üzeneteinek lekérdezése, egyszerre egy megadott érték szerint
	"""
	try:	
		p = Paginator(PrivateChatRoomMessage.objects.get_chat_messages_by_room(room), PRIVATE_CHAT_ROOM_MESSAGE_PAGE_SIZE)

		message = {}

		load_page_number = int(page_number)

		# elértük e az utolsó oldalt
		if load_page_number <= p.num_pages:
			load_page_number = load_page_number + 1
			
			s = EncodePrivateChatRoomMessage()

			message['messages'] = s.serialize(p.page(page_number).object_list)
		else:
			message['messages'] = 'None'
		message['load_page_number'] = load_page_number

		# python szótár konvertálása JSON objektummá és visszatérés az értékkel
		return json.dumps(message)
	except Exception as exception:
		print('Error when getting private chat messages' + str(exception))

	return None



class EncodePrivateChatRoomMessage(Serializer):
	def get_dump_object(self, obj):
		"""
		PrivateChatRoomMessage object szerializálása, mikor payload-ként küldjük a view-hoz
		JSON formátumra alakítjuk
		Függvény egy override
		"""

		# ha valakinek nincs profilképe, az alapértelmezett profilképet kapja
		try:
			profile_image = str(obj.user.profile_image.url)
		except Exception as exception:
			profile_image = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET

		message_obj = {
			'message_id'	: 	str(obj.id),
			'message_type'	:	MESSAGE_TYPE_MESSAGE,
			'message'		:	str(obj.content),
			'user_id'		:	str(obj.user.id),
			'username'		:	str(obj.user.username),
			'profile_image'	:	profile_image,
			'sending_time'	:	create_sending_time(obj.sending_time),
		}

		return message_obj



@database_sync_to_async
def add_user_to_current_users(user, room):
	"""
	Meghívjuk a PrivateChatRoom modellben lévő ugyanilyen nevű függvényt
	"""
	account = Account.objects.get(id=user.id)
	return room.add_user_to_current_users(account)


@database_sync_to_async
def remove_user_from_current_users(user, room):
	"""
	Meghívjuk a PrivateChatRoom modellben lévő ugyanilyen nevű függvényt
	"""
	account = Account.objects.get(id=user.id)
	return room.remove_user_from_current_users(account)



# incrementing unread message count if they are not in the room and updatet message
@database_sync_to_async
def add_or_update_unread_message(user, room, current_users, current_message):
	"""
	Hogyha nincs csatlakozva a chathez a felhasználó, updateeljük a countert es a recent messaget
	"""
	print('ADDING')
	if not user in current_users:
		try:
			unread_messages = UnreadPrivateChatRoomMessages.objects.get(user=user, room=room)
			unread_messages.recent_message = current_message
			unread_messages.unread_messages_count += 1

			unread_messages.save() # activate pre_save receiver
		except UnreadPrivateChatRoomMessages.DoesNotExist:
			#elvileg nem kene ilyennek legyen
			UnreadPrivateChatRoomMessages(user=user, room=room, unread_messages_count=1).save()
			pass
	return 

# felhasznalo csatlakozik a szobahoz, reseteljuk a countert
@database_sync_to_async
def reset_notification_count(user, room):
	current_users = room.current_users.all()

	if user in current_users:
		print('IFEN BELUL')
		try:
			unread_messages = UnreadPrivateChatRoomMessages.objects.get(user=user, room=room)
			unread_messages.unread_messages_count = 0
			unread_messages.last_seen_time = timezone.now()
			unread_messages.save()
		#except UnreadPrivateChatRoomMessages.DoesNotExist:
		#	UnreadPrivateChatRoomMessages(user=user, room=room).save()
		#	pass
		except Exception as exception:
			UnreadPrivateChatRoomMessages(user=user, room=room).save()
			pass
	return 


