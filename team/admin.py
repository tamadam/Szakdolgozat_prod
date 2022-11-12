from django.contrib import admin
from account.models import Account
from .models import Team, Membership, TeamMessage, UnreadTeamMessages, TeamJoinRequest
from django.core.paginator import Paginator
from django.core.cache import cache


class MembershipConfigInline(admin.TabularInline):
	model = Membership
	fields = ['user', 'date_joined']
	readonly_fields = fields
	extra = 0

	def has_add_permission(self, request, obj=None):
		return False
	
	def has_delete_permission(self, request, obj=None):
		return False



class TeamAdmin(admin.ModelAdmin):
	list_display = ['name', 'description', 'date_created']
	inlines = [MembershipConfigInline]
	readonly_fields = ['id']




class MembershipConfig(admin.ModelAdmin):
	list_display = ['user', 'team', 'date_joined']



admin.site.register(Team, TeamAdmin)
admin.site.register(Membership, MembershipConfig)




class CachingPaginator(Paginator):
	"""
	Sok üzenetnél az admin felületen lassú lehet a betöltése az üzeneteknek, ez megoldás rá
	Forrás: http://masnun.rocks/2017/03/20/django-admin-expensive-count-all-queries/
	"""
	def _get_count(self):

		if not hasattr(self, "_count"):
			self._count = None

		if self._count is None:
			try:
				key = "adm:{0}:count".format(hash(self.object_list.query.__str__()))
				self._count = cache.get(key, -1)
				if self._count == -1:
					self._count = super().count
					cache.set(key, self._count, 3600)

			except:
				self._count = len(self.object_list)
		return self._count


	count = property(_get_count)


class TeamMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'content', 'sending_time']
    list_filter = ['user', 'room', 'sending_time']
    search_fields = ['user__username', 'content'] # __ azt jelenti, hogy elérhetünk egy mezőt a modellben
    readonly_fields = ['id', 'user', 'room', 'sending_time']

    show_full_result_count = False
    paginator = CachingPaginator

    class Meta:
        model = TeamMessage


admin.site.register(TeamMessage, TeamMessageAdmin)




class UnreadTeamMessagesAdmin(admin.ModelAdmin):
	list_display = ['user', 'room', 'unread_messages_count']
	search_fields = []
	readonly_fields = ['id']

	class Meta:
		model = UnreadTeamMessages

admin.site.register(UnreadTeamMessages, UnreadTeamMessagesAdmin)


class TeamJoinRequestAdmin(admin.ModelAdmin):
	list_display = ['user', 'team', 'request_date']
	search_fields = []
	readonly_fields = ['id']
	
	class Meta:
		model = TeamJoinRequest

admin.site.register(TeamJoinRequest, TeamJoinRequestAdmin)

