import pandas as pd
import pymongo
from secret import MONGO_USER, MONGO_PW
from mongo import mongo_connect
import pprint
from places import *

def main():
	"""pull all data from mongo into a csv
	"""
	coll = mongo_connect(MONGO_USER, MONGO_PW)
	#listings = coll.find({"no_fee": {"$regex": u"NO"}}).limit(10)
	listings = coll.find()
	df = pd.DataFrame(list(listings))
	#pprint.pprint(listings[0])
	print df.head()
	df.to_csv("./mongo_listings.csv", encoding='utf-8')


def update_places():
	"""one time batch run for adding places info to existing data
	"""
	coll = mongo_connect(MONGO_USER, MONGO_PW)
	#listings = coll.find({"no_fee": {"$regex": u"NO"}}).limit(10)
	ids = coll.find({"coffee_count": {"$exists": False}}, 
					{'_id': 1, 'latlong': 1})
	for m_id in ids:
		place_fields = place_agg(m_id['latlong'])
		coll.update_one({"_id": m_id['_id']},
					    {"$set": place_fields})


if __name__ == '__main__':
	update_places()
	main()