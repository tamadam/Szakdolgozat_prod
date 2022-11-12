from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required

from core.constants import *
from account.models import Account


@login_required(login_url='login')
def public_chat_page_view(request):

	try:
		account = Account.objects.get(id=request.user.id)
	except:
		account = None
		pass

	context = {
		'debug_mode': settings.DEBUG,
		'room_id': PUBLIC_CHAT_ROOM_ID, 
		'account': account,
	}

	return render(request, 'public_chat/public_chat_page.html', context)