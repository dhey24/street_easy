import pandas as pd
import pymongo
from secret import MONGO_USER, MONGO_PW
from mongo import mongo_connect
import pprint

def main():
	coll = mongo_connect(MONGO_USER, MONGO_PW)
	#listings = coll.find({"no_fee": {"$regex": u"NO"}}).limit(10)
	listings = coll.find()
	df = pd.DataFrame(list(listings))
	#pprint.pprint(listings[0])
	print df.head()
	df.to_csv("./mongo_listings.csv")

if __name__ == '__main__':
	main()