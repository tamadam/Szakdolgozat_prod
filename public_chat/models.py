from django.db import models
from django.conf import settings

# Értesítéshez
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from notification.models import Notification
from account.models import Account


class PublicChatRoom(models.Model):
	"""
	A publikus chat szoba felépítése
	"""
	name 		= models.CharField(max_length=60, unique=True, blank=False) #name must be set

	users 		= models.ManyToManyField(settings.AUTH_USER_MODEL, blank = True) # users who are connected to the chat


	def __str__(self):
		return self.name


	def add_user_to_current_users(self, user):
		"""
		Amikor egy felhasználó csatlakozik egy szobához, és ezáltal egy sockethez, ez a függvény fog meghívódni
		Visszatérési értéke: igaz, hogyha a felhasználó hozzá lett adva a users listához
		Megj.: users lista a chatszobában jelenleg csatlakozott felhasználók listája
		"""
		if not user in self.users.all():
			self.users.add(user)
			self.save()
			print(f'{user.username} ONLINE')


	def remove_user_from_current_users(self, user):
		"""
		Amikor egy felhasználó elhagyja a chatszobát, és ezáltal bezárja a socketet
		Visszatérési értéke: igaz, hogyha a felhasználó el lett távolítva a users listából
		"""
		if user in self.users.all():
			self.users.remove(user)
			self.save()
			print(f'{user.username} OFFLINE')



	@property
	def group_name(self):
		"""
		Group: channeleknek a kollekciója; channelek: maguk a userek 
		Visszatérési értéke egy név, amelyre tudnak csatlakozni, ezáltal megkapják az elküldött üzeneteket
		"""
		return f'MainRoom_ID_{self.id}'



class PublicChatRoomMessageManager(models.Manager):
	def get_chat_messages_by_room(self, room):
		"""
		Adott szobában lévő összes chat üzenet lekérdezése
		"""
		qs = PublicChatRoomMessage.objects.filter(room=room).order_by("-sending_time")

		return qs
	

class PublicChatRoomMessage(models.Model):
	"""
	Üzenet a PublicChatRoomban
	"""
	user 			= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # ha egy user torlodik a chat uzenetei is
	room 			= models.ForeignKey(PublicChatRoom, on_delete=models.CASCADE) # ha a chatszoba törlődik az összes ebben lévő üzenet is
	sending_time 	= models.DateTimeField(auto_now_add=True)
	content 		= models.TextField(unique=False, blank=False)

	objects = PublicChatRoomMessageManager()


	def __str__(self):
		return self.content




class UnreadPublicChatRoomMessages(models.Model):
	"""
	Eltároljuk az olvasatlan üzeneteknek a számát adott felhasználónak az adott privát szobában
	Ahogy belépett a szobába a felhasználó, visszaállítjuk 0-ra a számlálót, 'olvasottra' állítjuk
	"""
	user 					= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	room 					= models.ForeignKey(PublicChatRoom, on_delete=models.CASCADE)
	unread_messages_count	= models.IntegerField(default=0)
	recent_message 			= models.CharField(max_length=200, blank=True, null=True)
	last_seen_time 			= models.DateTimeField(null=True) # a legutóbbi idő mikor a user olvasta az uzeneteket

	notifications 			= GenericRelation(Notification)


	def __str__(self):
		return f'{self.user.username}\'s unread messages in public chatroom'



@receiver(pre_save, sender=UnreadPublicChatRoomMessages)
def unread_messages_count_inc(sender, instance, **kwargs):
	print('unread_messages_count_inc')
	if instance.id == None:
		pass 
	else:
		prev_notification = UnreadPublicChatRoomMessages.objects.get(id=instance.id)
		if prev_notification.unread_messages_count < instance.unread_messages_count:
			content_type = ContentType.objects.get_for_model(instance)
			received_message = instance.recent_message.split('+') # a sender usert az uzenetbe agyazzuk a consumernel
			try:
				sender_user = Account.objects.get(username=received_message[0]) # a sender user
			except:
				sender_user = None
			message = received_message[1] # az uzenet maga

			
			try:
				notification = Notification.objects.get(notified_user=instance.user, content_type=content_type, object_id=instance.id)
				
				notification.notification_text = message
				#notification.last_seen_time = timezone.now() #torolheto priv chatnel is
				notification.save()
			except Notification.DoesNotExist:
				# elméletileg nem kellene ilyen hibának legyen, hiszen ezt az elején kezeljük, majd a post_save létrehozza
				instance.notifications.create(
					notified_user=instance.user,
					sender_user=sender_user,
					notification_text=message,
					content_type=content_type
					)
			

@receiver(pre_save, sender=UnreadPublicChatRoomMessages)
def unread_messages_count_reset(sender, instance, **kwargs):
	"""
	A táblában az értesítés sosem törlődik, a notification_text és a sending time updatelodik, de a sor nem torlodik
	Ha a counter csokken akkor törölje a notificatont(tablabvan marad)
	"""
	print('unread_messages_count_reset')
	if instance.id == None:
		pass
	else:
		prev_notification = UnreadPublicChatRoomMessages.objects.get(id=instance.id)
		if prev_notification.unread_messages_count > instance.unread_messages_count:
			content_type = ContentType.objects.get_for_model(instance)
			try:
				notification = Notification.objects.get(notified_user=instance.user, content_type=content_type, object_id=instance.id)
				notification.delete()
			except Notification.DoesNotExist:
				pass
