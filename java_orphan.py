#!/usr/bin/python3
# Look for orphaned classes
# Vitaly Chekryzhev, 2018

# Features
#	* Create report
#	* Full cleanup
#	* Use cache

from os import listdir, chmod
import io, sys, re, json
from os.path import isfile, isdir, join, basename, dirname
import argparse
import treelib

# Exclude core classes
exclusions = [
	'java/',
	'dalvik/',
	'android/[^s]'
	]

# Exclude internal classes
int_classes = ['R', 'BuildConfig', 'package-info']

fCachefile = './cache.txt'
fCachefile2 = './cache_u.txt'
fCachefile3 = './cache_l.txt'
fJS = 'usemap.txt'
fOrphans = 'orphans'
fUsed = 'used.txt'

# Retrieve main class name
found = 0
hasMainAction = 0
class_line = []

try:
	F = open('../AndroidManifest.xml', 'r')
except IOError:
	print("Unable to open manifest")
	sys.exit(1)

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--cleanup', help='remove SMALI', action='store_true')
parser.add_argument('-x', '--cache', help='store cache of usage data', action='store_true')
parser.add_argument('-v', '--verbose', help='verbose log', action='store_true')

args = parser.parse_args()

re_service = re.compile('^\s*<service')
re_name = re.compile('name="([^\"]+?)"')
re_javaname = re.compile('"([^\"]+?).java"')
re_fileclass = re.compile('\.\/([\/\-\w\d]+)(\$.+)?\.smali')
re_resclass = re.compile('^\s*<(\w+\.[\w\.]+)\s')
re_class = re.compile('[ \)]L([^:\(]+?);')
re_classsub = re.compile('([\/\-\w\d]+)(\$.+)?')

for line in F:
	if found and not hasMainAction:
		if line.find('<action android:name="android.intent.action.MAIN"') > -1:
			hasMainAction = 1

			mainClassName = mainClassName.replace('.', '/')
			class_line.append(mainClassName)

	if re.match(r'^\s*<activity', line) and not hasMainAction:
		hasMainAction = 0
		found = 1

		res = re_name.search(line)
		mainClassName = res.group(1)

	if re_service.match(line):
		res = re_name.search(line)
		mainClassName = res.group(1)

		mainClassName = mainClassName.replace('.', '/')
		class_line.append(mainClassName)

F.close()

if not hasMainAction:
	print("Manifest has no main action!")
	sys.exit(2)

CLASS = {}
REPLACES = {}
classes = []
classDir = ['.']

if isfile(fCachefile) and args.cache:
	print("Read from cache")
	C = open(fCachefile, 'r')
	CLASS = json.loads(C.readline())
	REPLACES = json.loads(C.readline())
	C.close()
	print("\t* done")
else:
	print("Traverse dir tree")

	# Find classes
	while len(classDir) > 0:
		directory = classDir.pop()

		for entry in listdir(directory):
			if entry.startswith('.'):
				continue

			if entry.endswith('.smali'):
				classes.append(directory + '/' + entry)

			if isdir(directory + '/' + entry):
				classDir.append(directory + '/' + entry)

	print("\t* done\n")

	print("Cache class list")

	# Cache classes
	for filename in classes:
		data = []

		F = open(filename, 'r')

		# Get class name from obfuscator replacements
		F.readline()
		F.readline()
		s = F.readline()
		srcName = ''
		res = re_javaname.search(s)
		if res:
			srcName = res.group(1)
			srcName = srcName.rstrip()

		res = re_fileclass.search(filename)
		className = res.group(1)
		part = res.group(2)
		if not part: part = ''

		classNameFull = className + part

		# TODO: Check forming!
		if ((srcName != '') and (srcName != basename(className))):
			REPLACES[classNameFull] = dirname(className) + '/' + srcName + part

		for line in F:
			res = re_class.search(line)
			if res:
				className = res.group(1)

				found = 0

				# Check for exclusions
				for exc in exclusions:
					if re.match('^' + exc, className):
						found = 1
						break

				if (not found and (classNameFull != className)):
					data.append(className)

		# Get unique list
		myset = set(data)
		data = list(myset)
		data.sort()

		CLASS[classNameFull] = data
		F.close()

	print("\t* done\n")

	# Dump cache
	print("Dump cache")
	C = open(fCachefile, 'w')
	C.write(json.dumps(CLASS))
	C.write("\n")
	C.write(json.dumps(REPLACES))
	C.close()
	print("\t* done")

print("Cached classes:", len(CLASS))
# TODO: Sort here

USAGE = {}
USAGE_LAYOUT = {}

if isfile(fCachefile2) and args.cache:
	print("Read from usage cache")
	C = open(fCachefile2, 'r')
	USAGE = json.loads(C.readline())
	C.close()
	print("\t* done")
else:
	print("Calculate usage")

	# Look for usages of class
	classlist = list(CLASS.keys())

	for k in classlist:
		USAGE[k] = []

		for k2 in classlist:
			if k in CLASS[k2]:
				USAGE[k].append(k2)
				continue

	# Dump cache
	print("Dump usage cache")
	C = open(fCachefile2, 'w')
	C.write(json.dumps(USAGE))
	C.close()
	print("\t* done")


if isfile(fCachefile3) and args.cache:
	print("Read from cache layout")
	C = open(fCachefile3, 'r')
	USAGE_LAYOUT = json.loads(C.readline())
	C.close()
	print("\t* done")
else:
	# Search visual components
	print("Read layouts")
	RESDIR = '../res/'
	layout_dirs = []

	layout_dirs = [f for f in listdir(RESDIR) if (isdir(join(RESDIR, f)) and f.startswith('layout'))]

	for k in layout_dirs:
		directory = RESDIR + k

		for entry in listdir(directory):
			if isfile(directory + '/' + entry) and entry.endswith('.xml'):
				F = open(directory + '/' + entry, 'r')

				for line in F:
					res = re_resclass.search(line)
					if res:
						cl = res.group(1)
						cl = cl.replace('.', '/')

						if not cl in USAGE_LAYOUT:
							USAGE_LAYOUT[cl] = []

						USAGE_LAYOUT[cl].append(k + '/' + entry)

				F.close()

	print("\t* done")

	# Dump layout cache
	print("Dump layout cache")
	C = open(fCachefile3, 'w')
	C.write(json.dumps(USAGE_LAYOUT))
	C.close()
	print("\t* done")


# Loop package classes and mark lines
print("Mark main classes")
MARKED = {}

absent = []

for k in USAGE_LAYOUT:
	class_line.append(k)

while len(class_line) > 0:
	cl = class_line.pop()

	# Iterate its connections
	if not cl in MARKED:
		if cl in CLASS:
			for c in CLASS[cl]:
				class_line.append(c)
		else:
			if not cl in absent:
				absent.append(cl)
			continue

	MARKED[cl] = 1

if args.verbose:
	absent.sort()
	print("ERROR! missing classes:\n" + "\n".join(absent))

del absent
print("\t* done")

print("Dump orphans")
ORP = open(fOrphans + '.txt', 'w')
ORPS = open(fOrphans + '.sh', 'w')
USED = open(fUsed, 'w')
USED2 = open(fUsed + '.clean', 'w')

ORPS.write("#!/bin/sh\n")

classlist = list(USAGE.keys())
classlist.sort()

print("Wash out usage data")

UNUSED_tmp = {}

for k in classlist:
	if k in MARKED:
		# Protect classes in main line
		continue

	if args.verbose:
		print("\t\tRemove: " + k)

	UNUSED_tmp[k] = 1
	del USAGE[k]

	# Check for exclusions
	class_path = k.split('/') # TODO: check Replacements!
	className = class_path[-1]
	if className in int_classes:
		continue

	ORPS.write("rm '" + k + ".smali'\n")
	ORP.write(k)
	if k in REPLACES:
		ORP.write(' -> ' + REPLACES[k])
	ORP.write("\n")

classlist = list(USAGE.keys())
classlist.sort()

for k in classlist:
	# Remove from USED unused classes
	uplist = []

	for l in USAGE[k]:
		if not l in UNUSED_tmp:
			uplist.append(l)

	USAGE[k] = uplist

i = 1
NUM = {}
cleaned = []

for k in classlist:
	USED.write(k + "\n")

	res = re_classsub.search(k)
	className = res.group(1)
	part = res.group(2)
	if not part: part = ''

	cleaned = []
	for k2 in USAGE[k]:
		USED.write("\t" + k2 + "\n")

		res = re_classsub.search(k2)
		class_sub = res.group(1)
		part_sub = res.group(2)
		if not part_sub: part_sub = ''

		if className != class_sub:
			cleaned.append(k2)

	if k in USAGE_LAYOUT:
		for k2 in USAGE_LAYOUT[k]:
			USED.write("\t@" + k2 + "\n")
			cleaned.append('@' + k2)

	USED.write("\n")

	if len(cleaned) > 0:
		USED2.write(k + "\n")
		for c in cleaned:
			USED2.write("\t" + c + "\n")

		USED2.write("\n")

	NUM[k] = i
	i += 1

ORP.close()
ORPS.close()
USED.close()
USED2.close()

chmod("orphans.sh", 0o755)

print("Build class tree")
JL = treelib.JFlatTree('Root')

prevPath = ''
curPath = ''
pathIndex = 0
aCPath = []
CLIND = {}

for k in classlist:
	aCPath = k.split('/')
	name = aCPath.pop()
	curPath = '/'.join(aCPath)

	if prevPath != curPath:
		pathIndex = JL.makeCat(aCPath)
		prevPath = curPath

	CLIND[k] = JL.put(pathIndex, name, 0)

print("\t* done")

print("Fill dependency tree")
for k in classlist:
	for k2 in USAGE[k]:
		JL.dep(CLIND[k], CLIND[k2])
print("\t* done")

print("Dump class map")
USED = open(fJS, 'w')
USED.write(str(JL))
USED.close()
print("\t* done")
