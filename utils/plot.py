import matplotlib.pyplot as plt

from collections import Counter

WIDTH = 1/1.5

def _rl(a):
	return range(len(a))

def hist(data, **kwargs):
	# data should be a list
	# create a dict of how many times each object appears
	c = Counter(data)
	czip = zip(c.keys(), c.values())

	if "sort" in kwargs:
		czip.sort(key=kwargs["sort"])
		kwargs.pop("sort")

	if "amount" in kwargs:
		czip = czip[-kwargs["amount"]:]
		kwargs.pop("amount")

	if "map" in kwargs:
		czip = map(kwargs["map"], czip)
		kwargs.pop("map")

	bar([i[1] for i in czip], names=[i[0] for i in czip], **kwargs)

def pie():
	pass

def bar(data, names=None, color="blue", title=None):
	# create a bar 
	plt.bar(_rl(data), data, WIDTH, color=color)

	if names:
		# plt.xticks(_rl(data) + WIDTH*0.5, names)
		plt.xticks(_rl(data), names)

	if title:
		plt.title(title)

	plt.show()

