# Method description
# Vitaly Chekryzhev, 2018

class JMethod:
	def __init__(self, classname, desc):
		self.module = classname
		self.source = classname[1:-1].replace('/', '.')
		a = desc.split('(')
		self.name = a[0]
		self.desc = desc
		self.start = 0
		self.end = 0
		self.used = 0
		self.exclude = 0
		self.mods = []
		self.uselist = []

	def __str__(self):
		return ("%s: %s, #%d, len: %d") % (self.source, self.desc, self.start, len(self))

	def __len__(self):
		return self.end - self.start

	def use(self, filename):
		self.uselist.append(filename)
		self.used = 1
