from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

import json

# Az exception kezelő osztály és függvény
from .exceptions import ClientError, handle_client_error

# Gyakran használt konstansok
from core.constants import *

# Modellek
from .models import PublicChatRoom, PublicChatRoomMessage, UnreadPublicChatRoomMessages

# Küldési idő kalkulálása
from .utils import *
from django.utils import timezone


# Chat üzenetek betöltése (pagination)
from django.core.serializers.python import Serializer
from django.core.paginator import Paginator
from django.core.serializers import serialize

# Értesítéshez
from account.models import Account


"""
Documentation used:
 	https://github.com/django/channels/blob/main/channels/generic/websocket.py
	https://channels.readthedocs.io/en/stable/topics/consumers.html    	
"""	

class PublicChatRoomConsumer(AsyncJsonWebsocketConsumer):
	async def connect(self):
		"""
		Csatlakozáskor használjuk, a kezdeti fázisban mikor a szerver és a kliens websocket kapcsolatra vált
		Mindenkit hagyunk csatlakozni a websockethez, a jogot a chateléshez egy későbbi szakaszban ellenőrizzük
		"""

		print('PublicChatConsumer: ' + str(self.scope['user']) + ' connected') 

		# csatlakozás elfogadása
		await self.accept()

		# definiáljuk a room_id változót, a későbiekkben ebben lesz eltárolva melyik szobában vagyunk
		self.room_id = None


	async def disconnect(self, code):
		"""
		Mikor bezáródik a websocket kapcsolat a szerver és kliens között
		"""

		print('PublicChatConsumer: ' + str(self.scope['user']) + ' disconnected') 
		
		# ellenőrizzük, hogy a room_id vissza lett-e állítva, és ha nem meghívjuk a megfelelő függvényt
		try:
			if self.room_id != None:
				await self.leave_room(self.room_id)
		except Exception as exception:
			print('Exception during disconnect in PublicChatConsumer' + str(exception))
			pass



	async def receive_json(self, content, **kwargs):
		"""
		Dekódolt JSON üzenet, akkor hívódik meg, mikor valamilyen parancs érkezik a template-től
		"""

		# https://www.w3schools.com/python/ref_dictionary_get.asp
		command = content.get('command', None)
		room_id = content['room_id']

		print('PublicChatConsumer: receive_json called with command: ' + str(command))


		#message = content['message'] csak akkor lesz message ha send van

		try:
			if command == 'send':
				message = content['message']
				if len(message.lstrip()) != 0:
					await self.send_chat_message_to_room(room_id, message)
				else:
					raise ClientError('EMPTY MESSAGE', 'Üres üzenet küldése nem lehetséges!')
			elif command == 'join':
				await self.join_room(room_id)
			elif command == 'leave':
				await self.leave_room(room_id)
			elif command == 'get_public_chat_room_messages':
				page_number = content['page_number']
				info_packet = await get_public_chat_room_messages(room_id, page_number) 

				if info_packet != None:
					# JSON formátum átalakítása python szótárrá
					info_packet = json.loads(info_packet)

					await self.send_previous_messages_payload(info_packet['messages'], info_packet['load_page_number'])
				else:
					raise ClientError('NO_MESSAGES', 'Something went wrong when getting PublicChatRoom messages')
		except ClientError as exception:
			error = await handle_client_error(exception)
			await self.send_json(error)
			return



	async def send_chat_message_to_room(self, room_id, message):
		"""
		receive_json függvény hívja meg, mikor valaki üzenetet küld a chatszobába
		Ez a függvény kezdi meg azt a folyamatot, amely az üzenetet az egész csoportnak elküldi
		"""
		user = self.scope['user']
		print('PublicChatConsumer: send_chat_message_to_room from user: ' + user.username)

		# ellenőrizzük, hogy a szobában van-e az adott felhasználó
		if self.room_id != None:
			if str(room_id) != str(self.room_id):
				raise ClientError('ROOM_ACCESS_DENIED', 'You are not allowed to be in this room')
			if not user.is_authenticated:
				raise ClientError('ROOM_ACCESS_DENIED', 'You are not allowed to be in this room')
		else:
			raise ClientError('Room access denied', 'Room access denied')


		room = await get_public_chat_room(room_id)

		current_users = room.users.all()

		all_registered_users = Account.objects.all() 
		# ezeknek a usereknek kuldjuk ki az ertesitest akik nincsenek a chatszobaban benne
		# az uzenetkuldo user is benne van ebben a listaban de mivel neki feltetlen a chatszobaban kell legyen
		# uzenetkuldeskor így nem gond


		await add_or_update_unread_message(user, all_registered_users, room, current_users, message)



		# üzenet mentése az adatbázisba
		await save_public_chat_room_message(user, room, message)

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
				'profile_image'	: profile_image,
				'message': message
			}
		)


	async def chat_message(self, event):
		"""
		Akkor fut le, mikor valaki üzenetet küld a chatbe
		Itt történik a tényleges üzenet elküldés a templatehez(a kliensnek) 
		"""

		print('PublicChatConsumer: chat_message from user: ' + str(event['username']))


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
		print('PublicChatConsumer: join_room')
		user = self.scope['user']

		try:
			room = await get_public_chat_room(room_id)
		except ClientError as exception:
			error = await handle_client_error(exception)
			await self.send_json(error)
			return


		# tároljuk hogy a szobában vagyunk
		self.room_id = room.id

		# hozzáadjuk az adott felhasználót a jelenleg chatben lévő felhasználók közé
		if user.is_authenticated:
			print(f'PublicChatConsumer: add user {user.username} to online users in group {room.group_name} ') 
			await add_user(room, user)
			await reset_notification_count(user, room)

		# a channel(felhasználó tulajdonképpen) hozzáadása a csoporthoz, így megkapja mindenki az adott üzenetet
		await self.channel_layer.group_add(
			room.group_name,
			self.channel_name
			)	

		# payloadot küldünk hogy csatlakoztunk a szobaba (js.ben: data.join)
		await self.send_json({
			'join': str(room.id),
			'username': user.username,
			})


		# online lévő felhasználók neve és száma 
		online_users_count = await get_number_of_users_in_room(room_id)
		online_users_name = await get_name_of_the_users_in_room(room_id)


		# elküldjük az új online lévő felhasználók számát és nevét
		await self.channel_layer.group_send(
				room.group_name,
				{
					'type': 'online.users',
					'online_users_count': online_users_count,
					'online_users_name': online_users_name,
				}
			)


	async def leave_room(self, room_id):
		"""
		Mikor valaki leave parancsot küld, meghívódik
		"""
		print('PublicChatConsumer: leave_room')
		user = self.scope['user']

		try:
			room = await get_public_chat_room(room_id)
		except ClientError as exception:
			error = await handle_client_error(exception)
			await self.send_json(error)
			return


		self.room_id = None

		# felhasználó törlése a jelenleg online lévő felhasználók közül
		if user.is_authenticated:
			print(f'PublicChatConsumer: remove user {user.username} from online users in group {room.group_name} ')
			await remove_user(room, user)


		# felhasználó törlése a csoportból
		await self.channel_layer.group_discard(
				room.group_name,
				self.channel_name
			)

		# online lévő felhasználók neve és száma 
		online_users_count = await get_number_of_users_in_room(room_id)
		online_users_name = await get_name_of_the_users_in_room(room_id)

		# elküldjük a frissített online felhasználók számát és nevét
		await self.channel_layer.group_send(
				room.group_name,
				{
					'type': 'online.users',
					'online_users_count': online_users_count,
					'online_users_name': online_users_name,					
				}
			)


	async def send_previous_messages_payload(self, messages, load_page_number):
		"""
		Elküldi a viewnak a következő adag betöltött üzeneteket
		Csak az adott kliensnek küldi el, nem az egész csoportnak
		"""

		print('PublicChatConsumer: send_previous_messages_payload')
		await self.send_json({
				'message_packet': 'message_packet', # itt a keyword a lényeg, az onmessage függvény a kliens oldalon így fogja tudni kezelni
				'messages': messages,
				'load_page_number': load_page_number,
			})


	async def online_users(self, event):
		"""
		Elküldi a szobához jelenleg csatlakozott felhasználók számát	
		"""
		#print('number_of_online_users')
		await self.send_json({
				'message_type': MESSAGE_TYPE_ONLINE_USERS,
				'num_of_online_users': event['online_users_count'],
				'online_users_name': event['online_users_name'],
			})



@database_sync_to_async
def get_public_chat_room(room_id):
	"""
	Publikus chatszoba lekérése a felhasználónak (ha létezik)
	"""
	try:
		room = PublicChatRoom.objects.get(pk=room_id)
	except PublicChatRoom.DoesNotExist:
		raise ClientError('EXIST_ERROR', 'PublicChatRoom does not exist')

	return room



@database_sync_to_async
def get_number_of_users_in_room(room_id):
	"""
	Jelenleg online felhasználók számának lekérdezése
	"""
	users = PublicChatRoom.objects.get(id=room_id).users
	if users:
		return len(users.all())
	return 0


@database_sync_to_async
def get_name_of_the_users_in_room(room_id):
	"""
	Jelenleg online felhasználók nevének lekérdezése
	"""
	online_users_name = []
	users = PublicChatRoom.objects.get(id=room_id).users
	if users:
		for user in users.all():
			online_users_name.append(user.username)
		return online_users_name
	return online_users_name





@database_sync_to_async
def save_public_chat_room_message(user, room, message):
	"""
	Elküldött üzenet mentése az adatbázisba
	"""
	return PublicChatRoomMessage.objects.create(user=user, room=room, content=message)


@database_sync_to_async
def get_public_chat_room_messages(room, page_number):
	"""
	Publikus chatszoba üzeneteinek lekérdezése, egyszerre egy megadott érték szerint
	"""
	try:
		p = Paginator(PublicChatRoomMessage.objects.get_chat_messages_by_room(room), PUBLIC_CHAT_ROOM_MESSAGE_PAGE_SIZE)

		message = {}

		load_page_number = int(page_number)

		# elértük e az utolsó oldalt
		if load_page_number <= p.num_pages:
			load_page_number = load_page_number + 1

			s = EncodePublicChatRoomMessage()

			message['messages'] = s.serialize(p.page(page_number).object_list)
		else:
			message['messages'] = 'None'
		message['load_page_number'] = load_page_number

		# python szótár konvertálása JSON objektummá és visszatérés az értékkel
		return json.dumps(message)

	except Exception as exception:
		print('Error when getting public chat messages' + str(exception))
	
	return None


class EncodePublicChatRoomMessage(Serializer):
	def get_dump_object(self, obj):
		"""
		PublicChatRoomMessage object szerializálása, mikor payload-ként küldjük a view-hoz
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
def add_user(room, user):
	"""
	Meghívja a modellben lévő add_user_to_current_users függvényt
	Ezzel hozzáférünk az adatbázis táblához:
		- mivel a hozzáférés szinkron művelet ezért át kell alakítani aszinkronná
	"""
	return room.add_user_to_current_users(user)


@database_sync_to_async
def remove_user(room, user):
	"""
	Meghívja a modellben lévő remove_user_from_current_users függvényt
	Ezzel hozzáférünk az adatbázis táblához:
		- mivel a hozzáférés szinkron művelet ezért át kell alakítani aszinkronná
	"""

	return room.remove_user_from_current_users(user)



# incrementing unread message count if they are not in the room and updatet message
@database_sync_to_async
def add_or_update_unread_message(sender_user, all_registered_users, room, current_users, current_message):
	"""
	Hogyha nincs csatlakozva a chathez a felhasználó, updateeljük a countert es a recent messaget
	"""
	print('ADDING')
	for user in all_registered_users:
		if not user in current_users:
			try:
				unread_messages = UnreadPublicChatRoomMessages.objects.get(user=user, room=room)
				unread_messages.recent_message = f'{sender_user}+{current_message}'
				unread_messages.unread_messages_count += 1

				unread_messages.save() # activate pre_save receiver
			except UnreadPublicChatRoomMessages.DoesNotExist:
				#elvileg nem kene ilyennek legyen
				UnreadPublicChatRoomMessages(user=user, room=room, unread_messages_count=1).save()
				pass
	return 

# felhasznalo csatlakozik a szobahoz, reseteljuk a countert
@database_sync_to_async
def reset_notification_count(user, room):
	current_users = room.users.all()

	if user in current_users:
		print('IFEN BELUL')
		try:
			unread_messages = UnreadPublicChatRoomMessages.objects.get(user=user, room=room)
			unread_messages.unread_messages_count = 0
			unread_messages.last_seen_time = timezone.now()
			unread_messages.save()
		except UnreadPublicChatRoomMessages.DoesNotExist:
			UnreadPublicChatRoomMessages(user=user, room=room, last_seen_time=timezone.now()).save()
			pass
	return 


