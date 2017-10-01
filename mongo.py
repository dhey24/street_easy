from pymongo import MongoClient
from secret import MONGO_USER, MONGO_PW
import pprint


def mongo_connect(user, pw)
	uri = "mongodb://" + user + ":" + pw + "@ds155684.mlab.com:55684/streeteasy"
	client = MongoClient(uri)
	db = client.streeteasy
	collection = db.listings

	return collection


def unique_names():
	coll = mongo_connect(MONGO_USER, MONGO_PW)
	names = coll.find().distinct("name")

	return names


def main():
	names = unique_names()
	pprint.pprint(names)

	#look for listings that are not in names

	#pull their data into pandas/csv/pkl

	#write back into mongoDB


if __name__ == '__main__':
	main()