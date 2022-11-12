from django.http import HttpResponse
from django.shortcuts import redirect


#if a user is authenticated, cant open the register or login page
def anonymous_user(view_func):
	def wrapper_func(request, *args, **kwargs):
		user = request.user
		if user.is_authenticated:
			return redirect('home_page')
		else:
			return view_func(request, *args, **kwargs)
	
	return wrapper_func