from channels.db import database_sync_to_async


# Forrás
# https://gearheart.io/articles/creating-a-chat-with-django-channels/



class ClientError(Exception):
	"""
	Egyedi osztály, bármilyen hiba lép fel, visszaküldi az adott kliensnek a hibaüzenetet
	"""

	def __init__(self, code, message):
		super().__init__(code)
		self.code = code

		if message:
			self.message = message



@database_sync_to_async
def handle_client_error(exception):
	"""
	ClientError kezelése
	"""
	
	error = {
		'error': exception.code,
		'message': 'Something went wrong',
	}

	if exception.message:
		error['message'] = exception.message


	return error