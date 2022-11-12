from .models import *


def create_or_get_private_chat(user1, user2):
	try:
		print(user1.username)
		print(user2.username)
		private_chat = PrivateChatRoom.objects.get(user1=user1, user2=user2)
	except PrivateChatRoom.DoesNotExist:
		try:
			private_chat = PrivateChatRoom.objects.get(user1=user2, user2=user1)
		except PrivateChatRoom.DoesNotExist:
			private_chat = PrivateChatRoom(user1=user1, user2=user2)
			private_chat.save()

	return private_chat
