from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import timezone
from datetime import datetime, date


def format_older_messages_sending_time(sending_time):
	months = {
		1 	: 'Január',
		2 	: 'Február',
		3 	: 'Március',
		4 	: 'Április',
		5 	: 'Május',
		6 	: 'Június',
		7 	: 'Július',
		8 	: 'Augusztus',
		9 	: 'Szeptember',
		10 	: 'Október',
		11 	: 'November',
		12 	: 'December',
	}

	current_day = timezone.now()
	#print('sendingtime' ,sending_time)


	year_month_day = str(sending_time).split()[0]
	#print('YMD:', year_month_day)
	year = year_month_day.split('-')[0]
	#print('year', year)
	month = int(year_month_day.split('-')[1].lstrip('0')) # 2022-07-07 19:17:47.314147 --> ['2022', '07', '07'] --> 7
	#print('month', month)
	day = year_month_day.split('-')[2]
	#print('day', day)

	#month_number = int(str(sending_time).split()[0].split('-')[1].lstrip('0')) 

	month_name = list({v for k,v in months.items() if k==month})[0]
	
	message_age_in_days = int(str(current_day-sending_time).split()[0])



	if message_age_in_days > 7:
		return f'{year}. {month_name}. {day}'
	elif message_age_in_days <= 7:
		return f'{message_age_in_days} napja'
	else:
		return 'ismeretlen küldési idő'



def format_today_messages_sending_time(sending_time):
	current_time = timezone.now()
	#sending_time = datetime.datetime(sending_time)
	#print(sending_time)
	elapsed_time = str((current_time-sending_time)).split(':')
	#print('ELAPSED TIME',elapsed_time)
	hour = int(elapsed_time[0])

	minute = elapsed_time[1]
	if minute != '00': # 00 -> int('')
		minute = int(minute.lstrip('0')) # 07 -> 7
	else:
		minute = 0

	second = elapsed_time[2].split('.')[0]
	if second != '00': # 00 -> int('')
		second = int(second.lstrip('0')) # 03.12345 --> 3
	else:
		second = 0

	#print(hour, minute, second)

	if hour == 0 and minute == 0 and second < 4:
		return 'éppen most'
	elif hour == 0 and minute == 0 and second >= 4:
		return f'{second} másodperce'
	elif hour == 0 and minute > 0:
		return f'{minute} perce'
	elif hour > 0:
		return f'{hour} órája'
	else:
		return 'ismeretlen küldési idő'



def create_sending_time(sending_time):
	"""
	Az üzenet küldési idejét számolja ki a következő módon:
		-> küldés adott napon: eltelt órák/percek/másodpercek száma
		-> küldés tegnap: küldési időpont
		-> küldés régebben: - küldés 7 napon belül: eltelt napok száma 
							- küldés 7 napnál régebben: dátum
	"""

	# example 3: https://www.programiz.com/python-programming/datetime/strftime


	if(naturalday(sending_time) == 'today'):
		message_time = format_today_messages_sending_time(sending_time)
	elif(naturalday(sending_time) == 'yesterday'):
		message_time = datetime.strftime(sending_time, '%H:%M')
		message_time = 'tegnap ' + str(message_time)
	else:
		message_time = format_older_messages_sending_time(sending_time)

	return message_time
