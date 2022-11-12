"""Szakdolgozat URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from core.views import (
    home_page_view,
    users_search_view,
    )

from account.views import (
    register_page_view,
    login_page_view,
    logout_view,
    profile_view,
    )

from public_chat.views import (
    public_chat_page_view,
    )

from game.views import (
    easy_game_view,
    )



urlpatterns = [
    path('admin/', admin.site.urls),

    # core app urls
    path('', home_page_view, name='home_page'),


    # account app urls
    path('regisztracio/', register_page_view, name='register'),
    path('bejelentkezes/', login_page_view, name='login'),
    path('kilepes/', logout_view, name='logout'),
    path('kereses/', users_search_view, name='search'),
    path('profil/<user_id>/', profile_view, name='profile'),


    # other urls inside account app
    #path('account/', include('account.urls'))

    # private_chat app urls
    path('uzenetek/', include('private_chat.urls', namespace='private_chat')),

    path('kozosseg/', public_chat_page_view, name='public_chat'),

    # core app urls
    path('core/', include('core.urls', namespace='core')),

    # account app urls
    path('profil/', include('account.urls', namespace='account')),

    # team app urls
    path('csapat/', include('team.urls', namespace='team')),

    # game app urls
    path('jatek/', include('game.urls', namespace='game')),
]

# tell django where these staticfiles exists; urls host those resources
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

