from django import template
from core.constants import STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET

from account.models import Character, Account

register = template.Library()

@register.simple_tag
def get_user_profile_picture(current_user):
	"""
	Django template tag - sidebarhoz nem tartozik külön view
	Arra használjuk, hogy az adott felhasználónak betöltse a profilképét
	"""

	account = Account.objects.get(id=current_user.id)
	if account.profile_image:
		img_path = account.profile_image.url
	else:
		img_path = STATIC_IMAGE_PATH_IF_DEFAULT_PIC_SET
		

	return img_path


@register.simple_tag
def get_user_gold_count(current_user):
	"""
	Arra használjuk, hogy az adott felhasználónak betöltse az aranyainak a számát
	"""

	return Character.objects.get(account=Account.objects.get(id=current_user.id)).gold
