from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from public_chat.consumers import PublicChatRoomConsumer
from private_chat.consumers import PrivateChatRoomConsumer
from team.consumers import TeamConsumer
from notification.consumers import NotificationConsumer

"""
###   Django channels kapcsolódó dokumentáció: https://channels.readthedocs.io/en/latest/topics/routing.html#   ###

1. ProtocolTypeRouter : ennek segítségével definiálhatjuk milyen típusú ASGI appot készítünk [websocket típus]

2. AllowedHostsOriginValidator : domainek halmaza, amelyek használhatják ezt a websocketet [ALLOWED_HOSTS]

3. AuthMiddlewareStack :
		request.user-el elérjük az adott usert a viewsban --> ugyanezt meg tudjuk csinálni a websocketes kódban is
		--> self.scope['user'] : hozzáférést biztosít a user objecthez a sessionben a channel/websocket appon belül

4. URLRouter : 	a url-eket itt arra használjuk, hogy megmondjuk a django websocket toolnak,
				melyek azok a url-ek, amelyekhez websocketeket tudok csatlakoztatni
				(azoknak a url-eknek a listája, ahova a websocketet csatlakoztatjuk, amíg nincs consumer addig üres)

"""
# notification: bármelyik oldalon működhet ez a consumer, mivel nem adtunk meg külön path-t neki


"""
application = ProtocolTypeRouter({
	'websocket': AllowedHostsOriginValidator(
		AuthMiddlewareStack( 
			URLRouter([
				path('kozosseg/<room_id>/', PublicChatRoomConsumer), # public_chat_page.html-el van kapcsolatban, a ws-es rész (mar magyarra volt forditva mikor ez a ketto meg nem)
				path('uzenetek/<room_id>/', PrivateChatRoomConsumer), # private_chat_room.html-el van kapcsolatban -||-
				path('csapat/<room_id>/', TeamConsumer), #individual_team.html -||-
				path('', NotificationConsumer), 
				]) 
			)
		),
	})

"""
application = ProtocolTypeRouter({
	'websocket': AuthMiddlewareStack(
			URLRouter([
				path('kozosseg/<room_id>/', PublicChatRoomConsumer), # public_chat_page.html-el van kapcsolatban, a ws-es rész (mar magyarra volt forditva mikor ez a ketto meg nem)
				path('uzenetek/<room_id>/', PrivateChatRoomConsumer), # private_chat_room.html-el van kapcsolatban -||-
				path('csapat/<room_id>/', TeamConsumer), #individual_team.html -||-
				path('', NotificationConsumer), 
				]) 
		),
	})