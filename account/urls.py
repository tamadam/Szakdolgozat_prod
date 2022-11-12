from django.urls import path

from account.views import (
	edit_profile_view,
	validate_username_realtime,
	validate_email_realtime,
	validate_password_realtime,
	increase_attribute_value,
	save_description,
	)

app_name = 'account'

urlpatterns = [
	path('szerkesztes/<user_id>', edit_profile_view, name='edit'),
	path('validate_username_realtime', validate_username_realtime, name='validate_username_realtime'),
	path('validate_email_realtime', validate_email_realtime, name='validate_email_realtime'),
	path('validate_password_realtime', validate_password_realtime, name='validate_password_realtime'),
	path('increase_attribute_value', increase_attribute_value, name='increase_attribute_value'),
	path('save_description', save_description, name='save_description'),
]