from django.contrib import admin
from .models import Arena

class ArenaConfig(admin.ModelAdmin):
	list_display = ['winner_of_fight', 'attacker', 'defender', 'date_of_fight', 'id']
	readonly_fields = ['attacker', 'defender', 'winner_of_fight']

	#ezek hogy ne dobjon hibat
	filter_horizontal = ()
	list_filter = () #itt meg lehetne adni username email stb es az alapjan filterel

	fieldsets = ()


admin.site.register(Arena, ArenaConfig)