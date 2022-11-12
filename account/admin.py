from django.contrib import admin
from .models import Account, Character, CharacterHistory
from django.contrib.auth.admin import UserAdmin
from team.models import Team, Membership


class TeamMembershipInLine(admin.TabularInline):
	model = Membership
	fields = ['team', 'date_joined']
	readonly_fields = fields
	extra = 0
	max_num=0 # account modellből ne lehessen csapatot hozzáadni

	# https://books.agiliq.com/projects/django-admin-cookbook/en/latest/remove_add_delete.html

	def has_delete_permission(self, request, obj=None): # ne lehessen csapatot törölni account modellből
		# Disable delete
		return False


# config how the admin panel should look like
class AccountAdminConfig(UserAdmin):
	inlines = [TeamMembershipInLine]
	list_display = ('username', 'email', 'date_joined', 'is_admin')  #, 'is_warrior', 'is_mage', 'is_scout', 'is_admin') #kilistazza mi latszodjon
	ordering = ('-date_joined', ) # ordering ascending/descending
	search_fields = ('username', 'email') # ezek alapjan lehet keresni az adminban
	readonly_fields = ('id', 'date_joined', 'last_login')


	
	
	#ezek hogy ne dobjon hibat
	filter_horizontal = ()
	list_filter = () #itt meg lehetne adni username email stb es az alapjan filterel
	"""
	fieldsets = (
		(None, {'fields': ('username', 'email',)}),
		('Permissions', {'fields': ('is_warrior', 'is_mage', 'is_scout', 'is_admin',)}),
		)
	"""
	fieldsets = ()

	# add user at the admin panel config
	"""
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('email', 'username', 'password1', 'password2', 'is_warrior', 'is_mage', 'is_scout', 'is_admin', 'is_staff')}
			),
		)
	"""
	
admin.site.register(Account, AccountAdminConfig)

class CharacterConfig(admin.ModelAdmin):
	list_display = ('account', 'character_type', 'level', 'honor', 'rank')  
	readonly_fields = ['character_type', 'account']
	#ezek hogy ne dobjon hibat
	filter_horizontal = ()
	list_filter = () #itt meg lehetne adni username email stb es az alapjan filterel

	fieldsets = ()


admin.site.register(Character, CharacterConfig)


class CharacterHistoryConfig(admin.ModelAdmin):
	readonly_fields = ['account']

admin.site.register(CharacterHistory, CharacterHistoryConfig)


