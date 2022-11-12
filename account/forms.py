from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Account, Character


#customize usercreation form, ez ellenorzi alapbol hogy letezik e a user es jo e a jelszo
class AccountRegistrationForm(UserCreationForm):
	character_type = forms.ChoiceField(choices=Character.ROLES)
	email = forms.EmailField(max_length=128,  error_messages = {'invalid': 'Helytelen email cím'}) # felülírjuk az alapértelmezett django hibaüzenetet arra, amikor az email formai helyességét vizsgálja

	class Meta:
		model = Account
		fields = ['username', 'email', 'password1', 'password2']

	# dokumentacio szerint a clean_<mezonev> szintaktikat kell kovetni es így mukodik
	def clean_username(self):
		username = self.cleaned_data['username'].lower()
		try:
			account = Account.objects.exclude(id=self.instance.id).get(username=username)
		except Account.DoesNotExist:
			return username
		raise forms.ValidationError(f'{username} nevű felhasználónk már van! Válassz egy másikat')
		

	def clean_email(self):
		email = self.cleaned_data['email'].lower() # ##email az a htmlben az input neve##
		try:
			account = Account.objects.exclude(id=self.instance.id).get(email=email)
		except Account.DoesNotExist:
			return email
		raise forms.ValidationError(f'{email} : ezt az emailt már valaki más használja')





	#  6 karakter hosszu, 1 szám 1 nagy és kisbetut tartalmaznia kell minimum 
	# felülírjuk a beepitett django fgv-t
	# https://github.com/loggly/django/blob/master/django/contrib/auth/forms.py 33.sor
	
	def clean_password2(self):
		password1 = self.cleaned_data.get('password1')
		password2 = self.cleaned_data.get('password2')
		if len(password1) < 6:
			raise forms.ValidationError('A jelszónak legalább 6 karakternek kell legyen')
		if sum(character.isdigit() for character in password1) < 1:
			raise forms.ValidationError('A jelszónak tartalmaznia kell legalább 1 számot')
		if not any (character.islower() for character in password1):
			raise forms.ValidationError('A jelszónak tartalmaznia kell legalább 1 kisbetűt')
		if not any (character.isupper() for character in password1):
			raise forms.ValidationError('A jelszónak tartalmaznia kell legalább 1 nagybetűt')

		if password1 != password2:
			raise forms.ValidationError('A két jelszó nem egyezik')

		return super(AccountRegistrationForm, self).clean_password2()
	
class AccountEditForm(forms.ModelForm):

	class Meta:
		model = Account
		fields = ['username', 'email', 'profile_image']

	# dokumentacio szerint a clean_<mezonev> szintaktikat kell kovetni es így mukodik
	def clean_username(self):
		username = self.cleaned_data['username'].lower()
		try:
			account = Account.objects.exclude(id=self.instance.id).get(username=username)
		except Account.DoesNotExist:
			return username
		raise forms.ValidationError(f'{username} nevű felhasználónk már van! Válassz egy másikat')
		

	def clean_email(self):
		email = self.cleaned_data['email'].lower() # ##email az a htmlben az input neve##
		try:
			account = Account.objects.exclude(id=self.instance.id).get(email=email)
		except Account.DoesNotExist:
			return email
		raise forms.ValidationError(f'{email} : ezt az emailt már valaki más használja')


