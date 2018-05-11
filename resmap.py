#!/usr/bin/python3
# Vitaly Chekryzhev, 2018
# Find unused resources and build a map of usages
# v1.0
# 'attr/font' type is not taken in account

import re, sys, os, json
from os import listdir
from os.path import isfile, isdir, join
import xml.etree.ElementTree as ET
import argparse

proj_folder = './'
res_folder = proj_folder + 'res/'
smali_folder = proj_folder + 'smali/'

RESFOLDER_CACHE = {}

# Increase HEX by value
def hex_inc(n, value):
	return hex(int(n[2:], base=16) + value)

# Remove resource file
def rm_resource(tp, name):
	if not tp in RESFOLDER_CACHE:
		res_folders = [f for f in listdir(res_folder) if (isdir(join(res_folder, f)) and f.startswith(tp))]
		RESFOLDER_CACHE[tp] = res_folders
	else:
		res_folders = RESFOLDER_CACHE[tp]

	for folder in res_folders:
		for entry in listdir(res_folder + folder):
			if os.path.splitext(entry)[0] == name:
				if args.verbose: print('\t\t' + folder + '/' + entry)
				os.remove(res_folder + folder + '/' + entry)
				break

# Delete items of specified type from specific xml
def cleanup(tree_root, folders, tp, a):
	if tp in ['array', 'bool', 'color', 'dimen', 'drawable', 'id', 'integer', 'string', 'style']:
		for folder in folders:
			filename = res_folder + folder + '/' + tp + 's.xml'
			if not os.path.isfile(filename): continue

			if args.verbose: print('\t\tClean ' + filename)
			tree_sub = ET.parse(filename)
			modified = False
			root = tree_sub.getroot()
			for el in a:
				child = root.find('*[@name="' + str(el) + '"]')
				if not child is None:
					modified = True
					root.remove(child)

			if args.replace:
				if args.backup:
					os.rename(filename, filename + '.bak')
			else:
				filename = filename + '.new'

			if modified:
				tree_sub.write(filename, xml_declaration=True, encoding='utf-8')

	if tp in ['anim', 'color', 'drawable', 'menu', 'mipmap', 'layout', 'xml', 'raw']:
		for el in a:
			rm_resource(tp, el)

	# Filter public
	children = tree_root.findall('./public[@type="' + tp + '"]')

	for child in children:
		for el in a:
			if child.attrib['name'] == el:
				tree_root.remove(child)
				break

# Check for correct environment
if not os.path.isfile(res_folder + 'values/public.xml'):
	print('Wrong directory')
	sys.exit(1)

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--cleanup', help='clean definition XML/SMALI', action='store_true')
parser.add_argument('-r', '--replace', help='replace original files', action='store_true')
parser.add_argument('-b', '--backup', help='create backup on replace', action='store_true')
parser.add_argument('-x', '--cache', help='store cache of usage data', action='store_true')
parser.add_argument('-v', '--verbose', help='verbose log', action='store_true')

args = parser.parse_args()

re_type = re.compile('@(\w+)/([\w\d_\-\.]+)')
re_style = re.compile('@style/([\w\d_\-\.]+)')
re_hexid = re.compile(', (0x7f0[a-f\d]{5})')
re_strjumbo = re.compile('const-string/jumbo v\d, "([\w\d_]+)"')
re_class = re.compile('sget v\d, L[\/\w]+\/R\$(\w+);->([\w\d]+):')
re_switch_id = re.compile('(0x7f0[a-f\d]{5}) -> :sswitch_\d')
re_switch2_id = re.compile('.packed-switch (0x7f0[a-f\d]{5})')
re_type_attr = re.compile('="@(\w+)/([^"]+)"')
re_type_val = re.compile('>@(\w+)/([^<]+)<')

SMALI = {}
UNUSED = {}
USED = {}
XMLs = {}
ARRAYs = {}

SUPPORT_TYPES = [
	'anim', 'animator', 'array', 'bool',
	'color', 'dimen', 'drawable', 'id',
	'integer', 'layout', 'menu', 'mipmap',
	'string', 'style', 'xml', 'raw',
	'styleable']

for t in SUPPORT_TYPES:
	UNUSED[t] = []
	USED[t] = {}
	XMLs[t] = {}
	ARRAYs[t] = {}

value_folders = [f for f in listdir(res_folder) if (isdir(join(res_folder, f)) and f.startswith('values'))]

if os.path.isfile('cache.txt') and args.cache:
	print('Read cache')
	fCACHE = open('cache.txt')
	s = fCACHE.readline()

	USED = json.loads(s)

	fCACHE.close()
else:
	print('Load XML from values')
	for folder in value_folders:
		print('\t' + folder)
		for entry in listdir(res_folder + folder):
			if entry in [
				'bools.xml', 'integers.xml', 'ids.xml',
				'integers.xml', 'public.xml', 'strings.xml']:
				continue

			if entry == 'arrays.xml':
				# Search for links in array definitions
				if args.verbose: print('\t\tarrays')
				tree = ET.parse(res_folder + folder + '/' + entry)
				root = tree.getroot()

				for child in root:
					nName = '@array/' + child.attrib['name']
					for child_item in child:
						res = re_type.search(child_item.text)
						if res:
							resType = res.group(1)

							if nName in ARRAYs[resType]:
								ARRAYs[resType][nName].add(res.group(2))
							else:
								ARRAYs[resType][nName] = set([res.group(2)])
				continue

			if entry == 'attrs.xml':
				if args.verbose: print('\t\tattrs')
				tree = ET.parse(res_folder + folder + '/' + entry)
				root = tree.getroot()
				resType = 'id'
				for child in root:
					nName = '@attr/' + child.attrib['name']
					for child_item in child:
						if nName in ARRAYs[resType]:
							ARRAYs[resType][nName].add(child_item.attrib['name'])
						else:
							ARRAYs[resType][nName] = set([child_item.attrib['name']])
				continue

			if entry == 'colors.xml':
				if args.verbose: print('\t\tcolors')
				tree = ET.parse(res_folder + folder + '/' + entry)
				root = tree.getroot()

				for child in root:
					nName = '@color/' + child.attrib['name']
					res = re_type.search(child.text)
					if res:
						resType = res.group(1)

						if nName in ARRAYs[resType]:
							ARRAYs[resType][nName].add(res.group(2))
						else:
							ARRAYs[resType][nName] = set([res.group(2)])
				continue

			if entry == 'dimens.xml':
				if args.verbose: print('\t\tdimens')
				tree = ET.parse(res_folder + folder + '/' + entry)
				root = tree.getroot()

				items = root.findall('./item')
				for child in items:
					nName = '@dimen/' + child.attrib['name']
					res = re_type.search(child.text)
					if res:
						resType = res.group(1)

						if nName in ARRAYs[resType]:
							ARRAYs[resType][nName].add(res.group(2))
						else:
							ARRAYs[resType][nName] = set([res.group(2)])
				continue

			if entry == 'styles.xml':
				if args.verbose: print('\t\tstyles')
				tree = ET.parse(res_folder + folder + '/' + entry)
				root = tree.getroot()

				for child in root:
					nName = '@style/' + child.attrib['name']

					if 'parent' in child.attrib:
						res = re_style.search(child.attrib['parent'])
						if res:
							if nName in ARRAYs['style']:
								ARRAYs['style'][nName].add(res.group(1))
							else:
								ARRAYs['style'][nName] = set([res.group(1)])

					# Iterate subitems
					for child_item in child:
						res = re_type.search(child_item.text)
						if res:
							resType = res.group(1)
							if nName in ARRAYs[resType]:
								ARRAYs[resType][nName].add(res.group(2))
							else:
								ARRAYs[resType][nName] = set([res.group(2)])
				continue

	print('Retrieve folder tree')
	res_folders = [f for f in listdir(res_folder) if (isdir(join(res_folder, f)) and (
		f.startswith(('drawable', 'menu', 'layout', 'color', 'anim'))))]
	res_folders.sort()

	# Get file list of XML
	print('Get resource XML list')
	xml_files = [('..', 'AndroidManifest.xml')]
	for d in res_folders:
		xml_files.extend([(d, f) for f in listdir(res_folder + d) if (isfile(join(res_folder + d, f)) and f.endswith('.xml'))])

	# Read and cache usage info from XML
	print('Find resource links in XMLs')
	for f in xml_files:
		# Check file
		filepath = res_folder + f[0] + '/' + f[1]
		if not os.path.isfile(filepath): continue

		with open(filepath) as src:
			# Check if folder is resource-container
			if f[0] == '..':
				typename = f[1]
			else:
				typename = '@' + f[0].rsplit('-', 1)[0] + '/' + f[1][:-4]

			for line in src:
				line = line.strip()
				res = re_type_attr.findall(line)
				if not res:
					res = re_type_val.findall(line)

				if res:
					for r in res:
						resType = r[0]
						if resType == 'attr': continue

						if typename in XMLs[resType]:
							XMLs[resType][typename].add(r[1])
						else:
							XMLs[resType][typename] = set([r[1]])

	# Read and cache info from SMALI
	print('Walk code and find IDs')
	for dirName, subdirList, fileList in os.walk(smali_folder):
		if args.verbose: print('\t' + dirName)

		for fname in fileList:
			if not (fname.startswith('R$') or fname.startswith('R.')):
				idlist = []
				filename = dirName + '/' + fname
				classname = filename[8:-6]
				classname = classname.replace('/', '.')

				packed = 0
				switch_len = 0
				orig_id = ''

				with open(filename) as file:
					for line in file:
						line = line.strip()

						if packed == 1:
							if line == '.end packed-switch':
								packed = 0
								orig_id = ''
								continue

							idlist.append(hex_inc(orig_id, switch_len))
							switch_len += 1

						res = re_hexid.search(line)
						if res:
							idlist.append(res.group(1))
							continue

						res = re_class.search(line)
						if res:
							resType = res.group(1)
							if resType == 'attr': continue

							if classname in XMLs[resType]:
								XMLs[resType][classname].add(res.group(2))
							else:
								XMLs[resType][classname] = set([res.group(2)])

						res = re_switch_id.search(line)
						if res:
							idlist.append(res.group(1))
							continue

						res = re_switch2_id.search(line)
						if res:
							packed = 1
							switch_len = 0
							orig_id = res.group(1)
							continue

						res = re_strjumbo.search(line)
						if res:
							idlist.append(res.group(1))
							continue

				SMALI[classname] = idlist

	print('Open public ID list')
	tree = ET.parse(res_folder + 'values/public.xml')
	root = tree.getroot()

	# Iterate resource list
	print('Find usages')

	lastType = ''
	for child in root:
		nID = child.attrib['id']
		nName = child.attrib['name']
		nType = child.attrib['type']

		if nType == 'attr': continue

		if nType != lastType:
			if args.verbose: print('\t' + nType)
			lastType = nType

		ulist = []

		for k in ARRAYs[nType]:
			if nName in ARRAYs[nType][k]:
				ulist.append(k)

		for k in XMLs[nType]:
			if nName in XMLs[nType][k]:
				ulist.append(k)

		for k in SMALI:
			if (nID in SMALI[k]) or (nName in SMALI[k]):
				ulist.append(k)

		USED[nType][nName] = ulist

	if args.cache:
		fCACHE = open('cache.txt', 'w')
		fCACHE.write(json.dumps(USED))
		fCACHE.close()

loop = 1
print('Wash out usage data')
while True:
	print('\titer #' + str(loop))
	found_unused = 0

	UNUSED_tmp = []

	for rtype in USED:
		for item in list(USED[rtype]):
			if len(USED[rtype][item]) == 0:
				UNUSED_tmp.append('@' + rtype + '/' + item)
				UNUSED[rtype].append(item)
				del USED[rtype][item]
				found_unused += 1

	if found_unused == 0: break

	# Wash out
	for rtype in USED:
		for item in USED[rtype]:
			USED[rtype][item][:] = [x for x in USED[rtype][item] if not x in UNUSED_tmp]

	loop += 1

# Dump array contents

fUNUSED = open('unused.txt', 'w')
fUSAGE = open('usage.txt', 'w')

for rtype in USED:
	for item in USED[rtype]:
		fUSAGE.write('@' + rtype + '/' + item + '\n')
		for k in USED[rtype][item]:
			fUSAGE.write('\t' + k + '\n')

		fUSAGE.write('\n')

for rtype in UNUSED:
	for item in UNUSED[rtype]:
		fUNUSED.write('@' + rtype + '/' + item + '\n')

fUNUSED.close()
fUSAGE.close()

if args.cleanup:
	print('Cleanup')
	filename = res_folder + 'values/public.xml'
	tree = ET.parse(filename)
	root = tree.getroot()

	for nType in UNUSED:
		print('\t' + nType)
		if len(UNUSED[nType]) == 0: continue
		cleanup(root, value_folders, nType, UNUSED[nType])

	if args.replace:
		if args.backup:
			os.rename(filename, filename + '.bak')
	else:
		filename = filename + '.new'

	tree.write(filename, xml_declaration=True, encoding='utf-8')

	print('Walk code and find resource definitions')
	for dirName, subdirList, fileList in os.walk(smali_folder):
		if args.verbose: print('\t' + dirName)

		for fname in fileList:
			if (fname.startswith('R$') and fname.endswith('.smali')):
				fType = fname[2:].rsplit('.', 1)[0]
				if (fType == 'attr' or fType == 'styleable'): continue

				filename = dirName + '/' + fname
				f_src = open(filename)
				f_res = open(filename + '.new', 'w')

				skip = False
				for line in f_src:
					if skip:
						skip = False
						continue

					if line.startswith('.field public static final'):
						varName = line[27:].rsplit(':', 1)[0]
						stop = False
						for el in UNUSED[fType]:
							if el == varName:
								stop = True
								break

						if stop:
							skip = True
							continue
						else:
							skip = False

					f_res.write(line)

				f_src.close()
				f_res.close()

				if args.replace:
					if args.backup:
						os.rename(filename, filename + '.bak')
					os.rename(filename + '.new', filename)

print('Done')
