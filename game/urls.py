from django.urls import path

from game.views import (
	game_choice_view,
	easy_game_view,
	medium_game_view,
	hard_game_view,
	finished_game,
	arena_view,
	arena_fight,
	set_team_arena_sessions,
	team_arena_view,
	)

app_name = 'game'

urlpatterns = [
	path('', game_choice_view, name='game_choice'),
	path('memoria/', easy_game_view, name='easy_game'),
	path('puzzle/', medium_game_view, name='medium_game'),
	path('aknakereso/', hard_game_view, name='hard_game'),
	path('finished_game',finished_game, name='finished_game'),
	path('arena/', arena_view, name='arena'),
	path('arena_fight', arena_fight, name='arena_fight'),
	path('set_team_arena_sessions', set_team_arena_sessions, name='set_team_arena_sessions'),
	path('csapat-arena/', team_arena_view, name='team_arena'),
]