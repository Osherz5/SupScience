import re
from dateutil.parser import parse as dateutil_parse_date
import matplotlib.pyplot as plt
from datetime import datetime

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

SUPPORTED_HOURS_DELTA = [0.5, 1, 2]
WIDTH = 1/1.5

MESSAGE_TYPE = {0 : "Message",
				1 : "Media",
				2 : "System"}

H = "\xd7\x97"

def read_data(file_name='w'):
	f = open(file_name, 'rb')
	a = f.read()
	f.close()
	return a

# returns [date, time, user, message, message_type]
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

def get_users(lines, first_name_only=False, anonymize=False):
	temp = list(
				set(
					[i[2] for i in lines]
					)
				)
	temp.remove("system")
	if anonymize:
		# get the length of the list, the count how many digits it has by
		# converting it into string and counting its length
		user_name_format = "user%%0%dd" % len(str(len(temp)))
		return [user_name_format % i for i in range(len(temp))]
	else:
		users = [
				(i[3:-3] if i[:3] == "\xe2\x80\xaa" and i[-3:] == "\xe2\x80\xac" else i)
				for i in temp]
		return [i.split()[0] if first_name_only else i for i in users]

def get_user_message_metadata(lines, users, media=False):
	amount_of_messages = [
		len([
			i for i in lines if i[2] == u and i[-1] == int(media)
		])
		for u in users
	]
	percent_of_messages = [float(i)/sum(amount_of_messages) for i in amount_of_messages]
	return zip(users, amount_of_messages, percent_of_messages)
	# return [user, #messages, %messages]

def get_user_wpm(lines, users, media=False):
	# Words Per Message
	if media:
		words_per_message = [1]*len(users)
	else:
		all_user_content = [
			'\n'.join([i[3] for i in lines if i[2] == u and i[-1] == 0])
			for u in users
		]
		words_per_message = [
			float(len(all_user_content[i].split()))
			 /
			amount_of_messages[i]
			for i in range(len(users))
		]
	return words_per_message

def get_user_hpm(lines, users, media=False):
	# H Per Message
	if media:
		h_per_message = [0]*len(users)
	else:
		all_user_content = [
			'\n'.join([i[3] for i in lines if i[2] == u and i[-1] == 0])
			for u in users
		]

def plot_messages(lines, pie=True, media=False):
	users = get_users(lines)
	# fd = filtered data
	fd = [
		len([
			i for i in lines if i[2] == u and i[-1] == int(media)
		])
		for u in users
	]

	if pie:
		plt.pie(fd, labels=users)
		plt.legend(title="users")
		plt.axis("equal")
	else:
		plt.bar(range(len(fd)), fd, WIDTH, color="blue")
		plt.xticks(range(len(fd)), users)

	plt.show()

def main():
	data = read_data()
	lines = parse_lines(data)
	users = get_users(lines)