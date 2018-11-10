from models import *
from toggles import *

import csv
import sys

# files in the folder pointed to by DATA_PATH should have form
# <ITEM_TYPE>_suffix.csv to be read properly
DATA_PATH = 'dynamicfilterapp/simulation_files/hotels/'

def load_database():
	"""
	Loads in the real data from files into database. Use for actual database, not for test cases
	"""
	# read in the questions
	ID = 0
	f = open(DATA_PATH + ITEM_TYPE + '_questions.csv', 'r')
	for line in f:
		line = line.rstrip('\n') 
		q = Question.objects.create(question_ID=ID, question_text=line)
		pred = Predicate(predicate_ID=ID, question=q)
		try:
			pred.save()
		except:
			print "there was a problem saving question", ID
		ID += 1
	f.close()

	# read in the items
	ID = 0
	with open(DATA_PATH + ITEM_TYPE + '_items.csv', 'r') as f:
		itemData = f.read()
	items = itemData.split("\n")

	with open(DATA_PATH + ITEM_TYPE + '_addresses.csv', 'r') as f1:
		addressData = f1.read()
	addresses = addressData.split("\n")

	for i in range(len(items)):
		i = Item(item_ID=ID, name=items[i], address=addresses[i], item_type=ITEM_TYPE)
		try:
			i.save()
		except:
			print "there was a problem saving item", ID
		ID += 1

	predicates = Predicate.objects.all()
	itemList = Item.objects.all()
	for p in predicates:
		for i in itemList:
			ip_pair = IP_Pair(item=i, predicate=p)
			try:
				ip_pair.save()
			except:
				"ip pair was not saved"


def make_task_file():
	"""
	Creates a csv file for AMT batch
	"""
	f = open(DATA_PATH + ITEM_TYPE + '_task_file.csv', 'w')

	# write the header
	f.write('Hotel,Address,Question\n')

	for ip in IP_Pair.objects.all():
		f.write(ip.item.name + ',"' + ip.item.address + '",' + ip.predicate.question.question_text + '\n')
	f.close()
