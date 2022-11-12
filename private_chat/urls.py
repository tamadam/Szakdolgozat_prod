from django.urls import path

from .views import(
	private_chat_page_view,
	create_or_return_private_chat,
	refresh_page_part_view,
	)

app_name = 'private_chat'

urlpatterns = [
	path('', private_chat_page_view, name='private_chat_room'),
	path('create_or_return_private_chat/', create_or_return_private_chat, name='create_or_return_private_chat'),
	path('private_chat_page_view/', private_chat_page_view, name='private_chat_page_view'),
]