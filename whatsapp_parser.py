import re
import utils
import matplotlib.pyplot as plt

from collections import Counter

# http://unicode.org/emoji/charts/full-emoji-list.html


SUPPORTED_HOURS_DELTA = [0.5, 1, 2]

MESSAGE_TYPE = {0 : "Message",
				1 : "Media",
				2 : "System"}


class Text(object):
	# hebrew[0] = \xd7\x90
	# hebrew[0] = \u05d0
	# hebrew[-1] = \xd7\xaa
	# hebrew[-1] = \u05ea
	WORDS_PATTERN = re.compile("[a-zA-Z\u05d0-\u05ea]+")
		
	# H = "\xd7\x97"
	H = "\u05d7"
	H_PATTERN = re.compile("(HH+)".replace('H', H))

	# split messages by the date pattern
	# "[date], [time] - .*"
	DATE_AND_TIME = "\d{1,2}/\d{1,2}/\d\d, \d\d\:\d\d"
	DATE_PATTERN = re.compile(u'(' + DATE_AND_TIME + " - .*)\n")


class Data(object):

	###############################################
	############          INIT         ############
	###############################################
	
	def init(self):
		self.read_data()
		self.parse_lines()
		self.get_users()
		self.get_all_words()

	def init_all(self):
		self.init()
		self.get_user_message_metadata()
		self.get_user_message_metadata(True)
		self.get_all_user_messages()
		self.get_user_wpm()
		self.get_user_hpm()
		self.get_most_common_words()

	def read_data(self, file_name='w'):
		f = open(file_name, 'rb')
		a = f.read()
		f.close()
		self.data = a.decode("utf8")
		return self.data

	# returns [date, time, user, message, message_type]
	def parse_lines(self):
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

		self.lines_raw = Text.DATE_PATTERN.findall(self.data)

		self.lines = []
		for i in self.lines_raw:
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
			self.lines.append((
							utils.date.parse_date(temp_date), # date
							int(temp_hour[:2]) * 60 + int(temp_hour[-2:]), # minutes
							user,
							message,
							message_type
						))
		return self.lines

	# get the usernames list
	def get_users(self, first_name_only=False, anonymize=False):
		"""
		gets a unique list of all the users
		This functions' flags change the value of self.users and the return value
		However, these variables will exist anyway
			self._users_anonymized
			self._users
			self._users_first_name
		while self.users will be a copy of the list requested by the flags
		"""
		self.users = list(
					set(
						[i[2] for i in self.lines]
					)
				)

		# set returns alphabetical order, list "shuffles" it
		# if anonymize: dont order
		# else: order
		if "system" in self.users:
			self.users.remove("system")

		### Anonymize ###
		# get the length of the list, the count how many digits it has by
		# converting it into string and counting its length
		self._user_name_format = "user%%0%dd" % len(str(len(self.users)))
		self._users_anonymized = [self._user_name_format % i for i in range(len(self.users))]
		
		self.users.sort()
		self._users = self.users[:]
		self._users_first_name = [
			(
				i[1:-1]
				 if
				i[0] == "\u202a"
				 and
				i[-1] == "\u202c"
				 else
				i.split()[0]
			)
			for i in self.users
		]

		if anonymize:
			self.users = self._users_anonymized[:] 
		else:
			if first_name_only:
				self.users = self._users_first_name[:]
		
		return self.users

	###############################################
	############        MESSAGES       ############
	###############################################

	# calculate amount of messages and percentage out of total messages
	def get_user_message_metadata(self, media=False):
		amount_of_user_messages = [
			len([
				i for i in self.lines if i[2] == u and i[-1] == int(media)
			])
			for u in self.users
		]

		messages_amount = sum(amount_of_user_messages)
		percent_of_messages = [float(i)/messages_amount for i in amount_of_user_messages]

		if media:
			self.user_media_amount = amount_of_user_messages
			self.user_media_percentage = percent_of_messages
		else:
			self.user_message_amount = amount_of_user_messages
			self.user_message_percentage = percent_of_messages

		return zip(self.users, amount_of_user_messages, percent_of_messages)
		# return [user, #messages, %messages]

	# get all the messages that the user sent
	def get_all_user_messages(self):
		self.messages_by_user = [
			[i[3] for i in self.lines if i[2] == u and i[-1] == 0]
			for u in self.users
		]
		self.messages_by_user_combined = list(
			map(
				lambda x: '\n'.join(x),
				self.messages_by_user
			)
		)
		return self.messages_by_user

	###############################################
	############         WORDS         ############
	###############################################

	# get Words Per Message
	def get_user_wpm(self, ignore_short_messages=0):
		if not self.__dict__.get("messages_by_user"):
			get_all_user_messages(self.lines, self.users)
		self.user_wpm = [
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
							self.messages_by_user[i]
						)
					)
				)
			)
			 /
			len(self.messages_by_user[i])
			for i in range(len(self.users))
		]
		return self.user_wpm

	# get H Per Message
	def get_user_hpm(self):
		if not self.__dict__.get("messages_by_user_combined"):
			get_all_user_messages()
				# H Per Message

		all_user_h = list(map(Text.H_PATTERN.findall, self.messages_by_user_combined))
		
		user_h_messages = list(map(len, all_user_h))
		self.user_h_amount = [len(''.join(h)) for h in all_user_h]

		# H per message
		self.user_hpm = list( # convert map to list
			map( # divide h_amount by user_message_amount
				lambda x: float(x[0]) / x[1],
				zip(
					self.user_h_amount,
					self.user_message_amount
				)
			)
		)

		# H per data (the whole string)
		self.user_hpd = [
			float(self.user_h_amount[i])
			 /
			len(self.messages_by_user_combined[i].replace(' ', ''))
			for i in range(len(self.users))
		]
		return all_user_h, user_h_messages, self.user_h_amount, self.user_hpm, self.user_hpd

	# create a list of all the words
	def get_all_words(self):
		self.words = sum([ Text.WORDS_PATTERN.findall(i[3]) for i in self.lines if i[-1] == 0 ], [])
		return self.words

	def get_most_common_words(self, amount=10, display=False):
		self.words_histogram = Counter(self.words)

		words = list(zip(self.words_histogram.keys(), self.words_histogram.values()))

		words.sort(key=lambda x: x[1])

		if amount:
			words = words[-amount:]

		if display:
			print('\n'.join(["%04d - %s" % (i[1], i[0][::-1]) for i in words]))
		else:
			return words

###############################################
############        EXAMPLES       ############
###############################################

def plot_h(data, users_names=None, hpm=True):
	if not users_names:
		users_names = data.users
	utils.plot.bar(
		user_hpm if hpm else user_hpd, # data
		names=users_names,
		title="H / message" if hpm else "H / data"
	)

def plot_messages(data, pie=True, media=False):
	# fd = filtered data
	fd = self.user_media_amount if media else self.user_media_amount

	if pie:
		utils.plot.pie(fd, labels=data.users, legend_title="users")
	else:
		utils.plot.bar(fd, names=data.users)

def plot_words(words, amount=15):
	utils.plot.hist(words, sort=lambda x: x[1], amount=amount, map=lambda x: [x[0].decode("utf8")[::-1], x[1]])

if __name__ == '__main__':
	pass
else:
	d = Data()
	d.init_all()
	# data = read_data()
	# lines = parse_lines(data)
	# users = get_users(lines)
	# users_names = ["Daniel Oren" if "972" in i else i for i in users]
	# users_names = [i.split()[0] for i in users_names]
