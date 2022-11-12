from django.contrib import admin
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import models

from .models import PublicChatRoom, PublicChatRoomMessage, UnreadPublicChatRoomMessages


class PublicChatRoomAdmin(admin.ModelAdmin):
	list_display = ['id', 'name']
	search_fields = ['id', 'name']

	class Meta:
		model = PublicChatRoom


admin.site.register(PublicChatRoom, PublicChatRoomAdmin)


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


class PublicChatRoomMessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'content', 'sending_time']
    list_filter = ['room', 'user', 'sending_time']
    search_fields = ['room__name', 'user__username', 'content'] # __ azt jelenti, hogy elérhetünk egy mezőt a modellben
    readonly_fields = ['id', 'user', 'room', 'sending_time']

    show_full_result_count = False
    paginator = CachingPaginator

    class Meta:
        model = PublicChatRoomMessage


admin.site.register(PublicChatRoomMessage, PublicChatRoomMessageAdmin)


class UnreadPublicChatRoomMessagesAdmin(admin.ModelAdmin):
	list_display = ['user', 'room', 'unread_messages_count']
	search_fields = []
	readonly_fields = ['id']

	class Meta:
		model = UnreadPublicChatRoomMessages

admin.site.register(UnreadPublicChatRoomMessages, UnreadPublicChatRoomMessagesAdmin)