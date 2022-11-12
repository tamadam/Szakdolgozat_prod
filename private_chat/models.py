from django.db import models
from django.conf import settings

# értesítésekhez
from notification.models import Notification
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save # trigger when notification generated
from django.utils import timezone




class PrivateChatRoom(models.Model):
	"""
	Privát chat szoba felépítése
	"""
	user1			= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user1')
	user2			= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user2')

	# users who are currently in the room
	current_users	= models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='current_users')


	#def __str__(self):
	#	return f'Private chat between {self.user1} and {self.user2}'


	@property
	def group_name(self):
		return f'PrivateChatRoom_{self.id}'


	# notificationhöz lehet nem is kell self.save nem kell?
	def add_user_to_current_users(self, user):
		"""
		Visszatérési értéke: igaz, hogyha a felhasználó hozzá lett adva a current_users-hez
		"""
		if not user in self.current_users.all():
			self.current_users.add(user)
			return True
		return False


	def remove_user_from_current_users(self, user):
		"""
		Visszatérési értéke: igaz, hogyha a felhasználó el lett távolítva a current_users-ből
		"""
		if user in self.current_users.all():
			self.current_users.remove(user)
			return True
		return False


class PrivateChatRoomMessageManager(models.Manager):
	def get_chat_messages_by_room(self, room):
		qs = PrivateChatRoomMessage.objects.filter(room=room).order_by('-sending_time')
		return qs


class PrivateChatRoomMessage(models.Model):
	"""
	Üzenet a PrivateChatRoomban
	"""
	user 			= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	room 			= models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
	sending_time	= models.DateTimeField(auto_now_add=True)
	content 		= models.TextField(unique=False, blank=False)


	objects = PrivateChatRoomMessageManager()


	def __str__(self):
		return self.content


	def get_sending_time(self):
		return self.sending_time



class UnreadPrivateChatRoomMessages(models.Model):
	"""
	Eltároljuk az olvasatlan üzeneteknek a számát adott felhasználónak az adott privát szobában
	Ahogy belépett a szobába a felhasználó, visszaállítjuk 0-ra a számlálót, 'olvasottra' állítjuk
	"""
	user 					= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	room 					= models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
	unread_messages_count	= models.IntegerField(default=0)
	recent_message 			= models.CharField(max_length=200, blank=True, null=True)
	last_seen_time 			= models.DateTimeField(null=True) # a legutóbbi idő mikor a user olvasta az uzeneteket

	notifications 			= GenericRelation(Notification)


	def __str__(self):
		return f'{self.user.username}\'s unread messages'



	# how do we trigger the notifciation associated with this(notifications a modellben)
	#ezzel

@receiver(post_save, sender=PrivateChatRoom)
def create_unread_private_chat_room_message(sender, instance, created, **kwargs):
	"""
	Amikor létrejön egy chatszoba mindkettő felhasználónak generálunk egy értesítést
	"""	
	if created:
		unread_message_user1 = UnreadPrivateChatRoomMessages(room=instance, user=instance.user1)
		unread_message_user2 = UnreadPrivateChatRoomMessages(room=instance, user=instance.user2)

		unread_message_user1.save()
		unread_message_user2.save()

@receiver(pre_save, sender=UnreadPrivateChatRoomMessages)
def unread_messages_count_inc(sender, instance, **kwargs):
	print('unread_messages_count_inc')
	if instance.id == None:
		pass # create_unread_private_chat_room_message fog lefutni(post_save)
	else:
		prev_notification = UnreadPrivateChatRoomMessages.objects.get(id=instance.id)
		if prev_notification.unread_messages_count < instance.unread_messages_count:
			content_type = ContentType.objects.get_for_model(instance)
			# meghatározzuk melyik user melyik
			if instance.user == instance.room.user1:
				other_user = instance.room.user2
			else:
				other_user = instance.room.user1

			try:
				notification = Notification.objects.get(notified_user=instance.user, content_type=content_type, object_id=instance.id)
				notification.notification_text = instance.recent_message
				#notification.last_seen_time = timezone.now()
				notification.save()
			except Notification.DoesNotExist:
				# elméletileg nem kellene ilyen hibának legyen, hiszen ezt az elején kezeljük, majd a post_save létrehozza
				instance.notifications.create(
					notified_user=instance.user,
					sender_user=other_user,
					notification_text=instance.recent_message,
					content_type=content_type
					)

@receiver(pre_save, sender=UnreadPrivateChatRoomMessages)
def unread_messages_count_reset(sender, instance, **kwargs):
	"""
	A táblában az értesítés sosem törlődik, a notification_text és a sending time updatelodik, de a sor nem torlodik
	Ha a counter csokken akkor törölje a notificatont(tablabvan marad)
	"""
	print('unread_messages_count_reset')
	if instance.id == None:
		pass
	else:
		prev_notification = UnreadPrivateChatRoomMessages.objects.get(id=instance.id)
		if prev_notification.unread_messages_count > instance.unread_messages_count:
			content_type = ContentType.objects.get_for_model(instance)
			try:
				notification = Notification.objects.get(notified_user=instance.user, content_type=content_type, object_id=instance.id)
				notification.delete()
			except Notification.DoesNotExist:
				pass
