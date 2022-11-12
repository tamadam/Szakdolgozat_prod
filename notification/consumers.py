from django.conf import settings
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType

import json
from datetime import datetime

from core.constants import *

from private_chat.models import UnreadPrivateChatRoomMessages
from public_chat.models import UnreadPublicChatRoomMessages
from team.models import UnreadTeamMessages

from .models import Notification

class NotificationConsumer(AsyncJsonWebsocketConsumer):
	async def connect(self):
		"""
		Csatlakozáskor használjuk, a kezdeti fázisban mikor a szerver és a kliens websocket kapcsolatra vált
		"""
		print('NotificationConsumer: ' + str(self.scope['user']) + ' connected') 

		await self.accept()


	async def disconnect(self, code):
		"""
		Mikor bezáródik a websocket kapcsolat a szerver és kliens között
		"""
		print('NotificationConsumer: ' + str(self.scope['user']) + ' disconnected')



	async def receive_json(self, content, **kwargs):
		"""
		Dekódolt JSON üzenet, akkor hívódik meg, mikor valamilyen parancs érkezik a template-től
		Első argumentumban van benne
		"""
		command = content.get('command', None) 
		user = self.scope['user']
		print('NotificationConsumer: receive_json called with command: ' + str(command))

		try:
			if command == 'get_unread_private_chat_room_messages_count':
				try:
					info_packet = await get_unread_private_chat_room_messages_count(user)
					if info_packet != None:
						info_packet = json.loads(info_packet)
						await self.send_private_chat_notifications_count(info_packet['count'])
				except Exception as e:
					print('Exception at get_unread_private_chat_room_messages_count consumer: ' + str(e))
					pass
			elif command == 'get_unread_public_chat_room_messages_count':
				try:
					info_packet = await get_unread_public_chat_room_messages_count(user)
					if info_packet != None:
						info_packet = json.loads(info_packet)
						await self.send_public_chat_notifications_count(info_packet['count'])
				except Exception as e:
					print('Exception at get_unread_public_chat_room_messages_count consumer: ' + str(e))
					pass
			elif command == 'get_unread_team_messages_count':
				try:
					info_packet = await get_unread_team_messages_count(user)
					if info_packet != None:
						info_packet = json.loads(info_packet)
						await self.send_team_chat_notifications_count(info_packet['count'])
				except Exception as e:
					print('Exception at get_unread_team_messages_count consumer: ' + str(e))
					pass
		except:
			pass

	async def send_private_chat_notifications_count(self, count):
		"""

		"""
		await self.send_json(
			{
				"message_type": MESSAGE_TYPE_PRIVATE_NOTIFICATIONS_COUNT,
				"num": count,
			},
		)


	async def send_public_chat_notifications_count(self, count):
		"""

		"""
		await self.send_json(
			{
				"message_type": MESSAGE_TYPE_PUBLIC_NOTIFICATIONS_COUNT,
				"num": count,
			},
		)


	async def send_team_chat_notifications_count(self, count):
		"""

		"""
		await self.send_json(
			{
				"message_type": MESSAGE_TYPE_TEAM_NOTIFICATIONS_COUNT,
				"num": count,
			},
		)



@database_sync_to_async
def get_unread_team_messages_count(user):
    print('get_unread_team_messages_count')
    info_packet = {}
    if user.is_authenticated:
        chatmessage_ct = ContentType.objects.get_for_model(UnreadTeamMessages)
        notifications = Notification.objects.filter(notified_user=user, content_type__in=[chatmessage_ct])

        unread_count = 0
        if notifications:
            unread_count = len(notifications.all())
        info_packet['count'] = unread_count
        return json.dumps(info_packet)
    else:
        #raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
        pass
    return None



@database_sync_to_async
def get_unread_private_chat_room_messages_count(user):
    print('get_unread_private_chat_room_messages_count')
    info_packet = {}
    if user.is_authenticated:
        chatmessage_ct = ContentType.objects.get_for_model(UnreadPrivateChatRoomMessages)
        notifications = Notification.objects.filter(notified_user=user, content_type__in=[chatmessage_ct])

        unread_count = 0
        if notifications:
            unread_count = len(notifications.all())
        info_packet['count'] = unread_count
        return json.dumps(info_packet)
    else:
        #raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
        pass
    return None


@database_sync_to_async
def get_unread_public_chat_room_messages_count(user):
    print('get_unread_public_chat_room_messages_count')
    info_packet = {}
    if user.is_authenticated:
        chatmessage_ct = ContentType.objects.get_for_model(UnreadPublicChatRoomMessages)
        notifications = Notification.objects.filter(notified_user=user, content_type__in=[chatmessage_ct])

        unread_count = 0
        if notifications:
            unread_count = len(notifications.all())
        info_packet['count'] = unread_count
        return json.dumps(info_packet)
    else:
        #raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
        pass
    return None

