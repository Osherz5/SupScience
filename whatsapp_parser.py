import re
from dateutil.parser import parse as dateutil_parse_date
import matplotlib.pyplot as plt
from datetime import datetime

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

SUPPORTED_HOURS_DELTA = [0.5, 1, 2]

MESSAGE_TYPE = {0 : "Message",
				1 : "Media",
				2 : "System"}

def read_data(file_name='w'):
	f = open(file_name, 'rb')
	a = f.read()
	f.close()
	return a

def parse_lines(data):
	date_pattern = "\d{1,2}/\d{1,2}/\d\d, \d\d\:\d\d"
	lines_raw = re.findall(u'(' + date_pattern + " - .*)\n", data)

	lines = []
	for i in lines_raw:
		date, rest = i.split(" - ", 1)
		if ':' in rest:
			user, message = rest.split(": ", 1)
			message_type = 1 if message == "<Media omitted>" else 0
		else:
			user = "system"
			message = rest
			message_type = 2

		temp_date = re.findall("^(\d{1,2}/\d{1,2}/\d\d), ", date)[0]
		temp_hour = date[date.find(',')+2:]
		lines.append((
						dateutil_parse_date(temp_date), # date
						int(temp_hour[:2]) * 60 + int(temp_hour[-2:]), # minutes
						user,
						message,
						message_type
					))
	return lines

def get_all_words(lines):
	words = []
	for i in lines:
		words += i[3].split()

	return words

def main():
	data = read_data()
	lines = parse_lines(data)
	users = list(set([i[2] for i in lines]))