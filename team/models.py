from django.db import models
from django.conf import settings


# Értesítéshez
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from notification.models import Notification



# https://docs.djangoproject.com/en/4.0/topics/db/models/#extra-fields-on-many-to-many-relationships

class TeamManager(models.Manager):
	def get_all_teams_in_ordered_list(self):
		teams = Team.objects.all()
		teams = sorted(teams, key=lambda team: team.honor, reverse=True)

		return teams


class Team(models.Model):
	name 			= models.CharField(max_length=60, unique=True, blank=False)
	description		= models.TextField(max_length=200, unique=False, blank=True, default="")
	date_created 	= models.DateTimeField(verbose_name = 'date created', auto_now_add = True, null=True)
	users 			= models.ManyToManyField(settings.AUTH_USER_MODEL, through='Membership')
	users_in_chat 	= models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='users_in_chat')
	rank			= models.DecimalField(verbose_name='rank', max_digits=19, decimal_places=0, blank = True, null = True) #helyezes
	honor			= models.DecimalField(verbose_name='team honor', max_digits=19, decimal_places=0, default = 1) #becsuletpont
	owner_of_team 	= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='owner_of_team')

	objects 		= TeamManager()

	def __str__(self):
		return self.name


	def add_user_to_current_users(self, user):
		"""
		Amikor egy felhasználó csatlakozik egy szobához, és ezáltal egy sockethez, ez a függvény fog meghívódni
		Visszatérési értéke: igaz, hogyha a felhasználó hozzá lett adva a users listához
		Megj.: users lista a chatszobában jelenleg csatlakozott felhasználók listája
		"""
		if not user in self.users_in_chat.all():
			self.users_in_chat.add(user)
			self.save()
			print(f'{user.username} ONLINE')


	def remove_user_from_current_users(self, user):
		"""
		Amikor egy felhasználó elhagyja a chatszobát, és ezáltal bezárja a socketet
		Visszatérési értéke: igaz, hogyha a felhasználó el lett távolítva a users listából
		"""
		if user in self.users_in_chat.all():
			self.users_in_chat.remove(user)
			self.save()
			print(f'{user.username} OFFLINE')



	@property
	def group_name(self):
		"""

		"""
		return f'TeamChatRoom-{self.id}'


class Membership(models.Model):
	user 			= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	team 			= models.ForeignKey(Team, on_delete=models.CASCADE)
	date_joined 	= models.DateTimeField(verbose_name = 'date joined', auto_now_add = True, null=True)


	class Meta:
		unique_together = [['user', 'team']] # pl magust ne lehessen 2x beletenni egy csapatba

	def __str__(self):
		return (f'{self.user.username} in {self.team.name}')


	def get_username(self):
		return self.user.username


class TeamMessageManager(models.Manager):
	def get_chat_messages_by_room(self, room):
		qs = TeamMessage.objects.filter(room=room).order_by('-sending_time')
		return qs


class TeamMessage(models.Model):
	"""
	Chat üzenet a Teamben
	"""
	user 			= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	room 			= models.ForeignKey(Team, on_delete=models.CASCADE)
	sending_time 	= models.DateTimeField(auto_now_add=True)
	content 		= models.TextField(unique=False, blank=False)


	objects 		= TeamMessageManager()


	def __str__(self):
		return self.content


class UnreadTeamMessages(models.Model):
	"""
	Eltároljuk az olvasatlan üzeneteknek a számát adott felhasználónak az adott privát szobában
	Ahogy belépett a szobába a felhasználó, visszaállítjuk 0-ra a számlálót, 'olvasottra' állítjuk
	"""
	user 					= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	room 					= models.ForeignKey(Team, on_delete=models.CASCADE)
	unread_messages_count	= models.IntegerField(default=0)
	recent_message 			= models.CharField(max_length=200, blank=True, null=True)
	last_seen_time 			= models.DateTimeField(null=True) # a legutóbbi idő mikor a user olvasta az uzeneteket

	notifications 			= GenericRelation(Notification)


	def __str__(self):
		return f'{self.user.username}\'s unread messages in team'



@receiver(pre_save, sender=UnreadTeamMessages)
def unread_messages_count_inc(sender, instance, **kwargs):
	print('unread_messages_count_inc')
	if instance.id == None:
		pass # create_unread_private_chat_room_message fog lefutni(post_save)
	else:
		prev_notification = UnreadTeamMessages.objects.get(id=instance.id)
		if prev_notification.unread_messages_count < instance.unread_messages_count:
			content_type = ContentType.objects.get_for_model(instance)
			received_message = instance.recent_message.split('+') # a sender usert az uzenetbe agyazzuk a consumernel
			print(received_message)

			#try:
				#sender_user = Membership.objects.filter(user__in=[int(received_message[0])]) # a sender user

				#print(sender_user)
			#except:
				#print('except')
				#sender_user = None
			sender_user = None
			message = received_message[1] # az uzenet maga

			
			try:
				notification = Notification.objects.get(notified_user=instance.user, content_type=content_type, object_id=instance.id)
				
				notification.notification_text = message
				#notification.last_seen_time = timezone.now() 
				notification.save()
			except Notification.DoesNotExist:
				# elméletileg nem kellene ilyen hibának legyen, hiszen ezt az elején kezeljük, majd a post_save létrehozza
				instance.notifications.create(
					notified_user=instance.user,
					sender_user=sender_user,
					notification_text=message,
					content_type=content_type
					)
			

@receiver(pre_save, sender=UnreadTeamMessages)
def unread_messages_count_reset(sender, instance, **kwargs):
	"""
	A táblában az értesítés sosem törlődik, a notification_text és a sending time updatelodik, de a sor nem torlodik
	Ha a counter csokken akkor törölje a notificatont(tablabvan marad)
	"""
	print('unread_messages_count_reset')
	if instance.id == None:
		pass
	else:
		prev_notification = UnreadTeamMessages.objects.get(id=instance.id)
		if prev_notification.unread_messages_count > instance.unread_messages_count:
			content_type = ContentType.objects.get_for_model(instance)
			try:
				notification = Notification.objects.get(notified_user=instance.user, content_type=content_type, object_id=instance.id)
				notification.delete()
			except Notification.DoesNotExist:
				pass


class TeamJoinRequestManager(models.Manager):
	def get_all_requests(self, team):
		qs = TeamJoinRequest.objects.filter(team=team).order_by('request_date')
		return qs


class TeamJoinRequest(models.Model):
	user 			= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	team			= models.ForeignKey(Team, on_delete=models.CASCADE)
	request_date 	= models.DateTimeField(verbose_name = 'request date', auto_now_add = True)


	def __str__(self):
		return f'Csatlakozási kérelem {self.team} csapathoz {self.user} felhasználótól'

	objects = TeamJoinRequestManager()