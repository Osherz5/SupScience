import re
import utils
import matplotlib.pyplot as plt

from collections import Counter

# http://unicode.org/emoji/charts/full-emoji-list.html

# hebrew[0] = \xd7\x90
# hebrew[0] = \u05d0
# hebrew[-1] = \xd7\xaa
# hebrew[-1] = \u05ea
WORDS_PATTERN = re.compile("[a-zA-Z\u05d0-\u05ea]+")

SUPPORTED_HOURS_DELTA = [0.5, 1, 2]

MESSAGE_TYPE = {0 : "Message",
				1 : "Media",
				2 : "System"}

# H = "\xd7\x97"
H = "\u05d7"
H_PATTERN = re.compile("(HH+)".replace('H', H))

def read_data(file_name='w'):
	f = open(file_name, 'rb')
	a = f.read()
	f.close()
	return a.decode("utf8")

# returns [date, time, user, message, message_type]
def parse_lines(data):
	"""
	parses the data and splits into messages
	message can be one of 3 types
		system message - "[date], [time] - [system_message_data]"
		user   message - "[date], [time] - [user]: [user_message_data]"
		user   media   - "[date], [time] - [user]: <Media omitted>"

	this data is being parsed into a 2D array
		1st dimension is the messages by order
		2nd dimension is a message tuple
			content name - [date    , time          , user, message, message_type       ]
			content type - [datetime, int of minutes, str , str    , int of MESSAGE_TYPE]

	* ':' in a system message will return unwanted results
		e.g. "[user] has changed the group name to \"abc:def\""
	"""

	# split messages by the date pattern
	# "[date], [time] - .*"
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
						utils.date.parse_date(temp_date), # date
						int(temp_hour[:2]) * 60 + int(temp_hour[-2:]), # minutes
						user,
						message,
						message_type
					))
	return lines

# get the usernames list
def get_users(lines, first_name_only=False, anonymize=False):
	users = list(
				set(
					[i[2] for i in lines]
				)
			)
	# set returns alphabetical order, list "shuffles" it
	# if anonymize: dont order
	# else: order

	users.remove("system")
	if anonymize:
		# get the length of the list, the count how many digits it has by
		# converting it into string and counting its length
		user_name_format = "user%%0%dd" % len(str(len(users)))
		return [user_name_format % i for i in range(len(users))]
	else:
		if first_name_only:
			users = [
				(i[1:-1] if i[0] == "\u202a" and i[-1] == "\u202c" else i.split()[0])
				for i in users
			]
			# users = [i.split()[0] for i in users]
		users.sort()
		return users

###############################################
############        MESSAGES       ############
###############################################

# calculate amount of messages and percentage out of total messages
def get_user_message_metadata(lines, users, media=False):
	amount_of_messages = [
		len([
			i for i in lines if i[2] == u and i[-1] == int(media)
		])
		for u in users
	]

	all_messages = sum(amount_of_messages)
	percent_of_messages = [float(i)/all_messages for i in amount_of_messages]

	return zip(users, amount_of_messages, percent_of_messages)
	# return [user, #messages, %messages]

# get all the messages that the user sent
def get_all_user_messages(lines, users):
	return [
		[i[3] for i in lines if i[2] == u and i[-1] == 0]
		for u in users
	]

###############################################
############         WORDS         ############
###############################################

# get Words Per Message
def get_user_wpm(lines, users, ignore_short_messages=0):
	all_user_messages = get_all_user_messages(lines, users)
	words_per_message = [
		# join all the user messages, and then split by whitespace
		float( # get accurate division
			sum( # combine all the messages
				filter( # filter out messages shorter than wanted
					(lambda x: x > ignore_short_messages)
					 if
					ignore_short_messages
					 else
					None,
					map( # run on all the messages
						# change from message to amount of words in the message
						lambda x: len(x.split()),
						all_user_messages[i]
					)
				)
			)
		)
		 /
		len(all_user_messages[i])
		for i in range(len(users))
	]
	return words_per_message

# TODO
def get_user_hpm(lines, users):
	# H Per Message

	all_user_content = get_all_user_messages(lines, users)

	all_user_h = map(H_PATTERN.findall, all_user_content)
	
	user_h_messages = map(len, all_user_h)
	user_h_amount = [len(''.join(h)) for h in all_user_h]
	user_h_amount = sum(
		map(
			len,
			all_user_h
		)
	)
	# H per message
	user_hpm = [
		float(user_h_amount[i])
		 /
		len([j for j in lines if j[2] == users[i] and j[-1] == 0])
		for i in range(len(users))
	]
	# H per data (the whole string)
	user_hpd = [
		float(user_h_amount[i])
		 /
		len(all_user_content[i].replace(' ', ''))
		for i in range(len(users))
	]
	return all_user_h, user_h_messages, user_h_amount, user_hpm, user_hpd

# create a list of all the words
def get_all_words(lines):
	return sum([ WORDS_PATTERN.findall(i[3]) for i in lines if i[-1] == 0 ], [])
	# return sum([i[3].split() for i in lines], [])

def get_most_common_words(words, amount=10, display=False):
	d = Counter(words)

	dzip = list(zip(d.keys(), d.values()))

	dzip.sort(key=lambda x: x[1])

	if amount:
		dzip = dzip[-amount:]

	if display:
		print('\n'.join(["%04d - %s" % (i[1], i[0][::-1]) for i in dzip]))
	else:
		return dzip

###############################################
############         PLOTS         ############
###############################################

# TODO
def plot_h(lines, users, users_names=None, hpm=True):
	if not users_names:
		users_names = users
	_, _, _, user_hpm, user_hpd = get_user_hpm(lines, users)
	data = user_hpm if hpm else user_hpd
	print("plotting " + ("hpm" if hpm else "hpd"))
	bar_plot(data, users_names, "H / message" if hpm else "H / data")
	plt.bar(range(len(user_hpd)), user_hpd, WIDTH, color="blue")
	plt.xticks(range(len(users)), users_names)
	plt.title("H / data")
	plt.show()

# TODO
def bar_plot(data, users_names=None, title=None):
	# Range Len Data
	rld = range(len(data))
	plt.bar(rld, data, WIDTH, color="blue")
	if users_names:
		plt.xticks(rld, users_names)
	if title:
		plt.title("H / data")
	plt.show()

# TODO
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

def plot_words(words, amount=15):
	utils.plot.hist(words, sort=lambda x: x[1], amount=amount, map=lambda x: [x[0].decode("utf8")[::-1], x[1]])

def main():
	data = read_data()
	lines = parse_lines(data)
	users = get_users(lines)
	

if __name__ == '__main__':
	main()
else:
	data = read_data()
	lines = parse_lines(data)
	users = get_users(lines)
	# users_names = ["Daniel Oren" if "972" in i else i for i in users]
	# users_names = [i.split()[0] for i in users_names]
