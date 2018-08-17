# Flat tree
# Vitaly Chekryzhev, 2018

# Item structure:
# Tree = Item[]
# Item = [name, isCat, children[]]

class JFlatTree:
	def __init__(self, name):
		self.data = [[name, 1, []]]

	def get(self, item):
		return self.data[item]

	def size(self):
		return len(self.data)

	def dep(self, dst, add):
		self.data[dst][2].append(add)

	def __str__(self):
		size = self.size()
		plain = ''

		for item in self.data:
			plain += item[0] + ";" + str(item[1]) + ";" + ','.join(map(str, item[2])) + "\n"

		return plain

	def find(self, name, isCat):
		curIndex = 0
		pathChunk = ''

		path = name.split('/')

		while len(path) > 0:
			pathChunk = path.shift()
			for item in self.data[curIndex][2]:
				value = self.get(item)

				if value[0] == pathChunk:
					if (value[1] == isCat) and (len(path) == 0):
						return item

					# Dive into
					if value[1] == 1:
						curIndex = item
						break;

		return -1;

	def put(self, pIndex, name, isCat):
		newIndex = self.size()
		self.data[pIndex][2].append(newIndex)
		self.data.append([name, isCat, []])

		return newIndex

	def makeCat(self, path):
		curIndex = 0
		pathChunk = ''
		found = 0
		skip = 0

		while len(path) > 0:
			pathChunk = path.pop(0)
			found = 0

			if skip == 0:
				for item in self.data[curIndex][2]:
					value = self.get(item)
					if value[0] == pathChunk:
						if value[1] == 1:
							if len(path) == 0:
								return item

							found = 1

							# Dive into
							curIndex = item
							break

			if found == 0: # Not found sub category - create
				skip = 1
				curIndex = self.put(curIndex, pathChunk, 1)

		return curIndex
