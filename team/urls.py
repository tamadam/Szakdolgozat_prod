from django.urls import path

from team.views import (
	user_team_view,
	leave_team,
	accept_user_join,
	individual_team_view,
	save_team_description,
	send_join_request,
	decline_user_join,
	fire_team_mate,
	)

app_name = 'team'

urlpatterns = [
	path('', user_team_view, name='user_team_view'),
	path('leave_team/', leave_team, name='leave_team'),

	path('accept_user_join', accept_user_join, name='accept_user_join'),
	path('decline_user_join', decline_user_join, name='decline_user_join'),
	path('send_join_request', send_join_request, name='send_join_request'),
	path('fire_team_mate', fire_team_mate, name='fire_team_mate'),

	path('<team_id>/', individual_team_view, name='individual_team_view'),
	path('save_team_description', save_team_description, name='save_team_description'),
]