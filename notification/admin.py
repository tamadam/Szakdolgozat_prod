from django.contrib import admin

from .models import Notification

class NotificationAdmin(admin.ModelAdmin):
	list_display = ['notified_user', 'content_type', 'sending_time']
	list_filter = ['content_type']
	search_fields = ['notified_user__username']

	class Meta:
		model = Notification


admin.site.register(Notification, NotificationAdmin)