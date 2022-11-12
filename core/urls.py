from django.urls import path

from core.views import (
	load_users_pagination,
	load_teams_pagination,
	get_search_results,
	)

app_name = 'core'

urlpatterns = [
	#path('list_accounts', list_accounts, name='list_accounts'),
	path('load_users_pagination', load_users_pagination, name='load_users_pagination'),
	path('load_teams_pagination', load_teams_pagination, name='load_teams_pagination'),
	path('get_search_results', get_search_results, name='get_search_results'),
]