from django import forms
from .models import Team
from django.core.exceptions import ValidationError

class TeamCreationForm(forms.ModelForm):
	class Meta:
		model = Team
		fields = ['name', 'description']


	def clean_name(self):
		name = self.cleaned_data['name']
		if Team.objects.filter(name__icontains=name).exists():
			raise ValidationError(f'"{name}" csapatnév már használatban van!')

		return name
