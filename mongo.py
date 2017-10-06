from pymongo import MongoClient
from street_easy_scraping2 import scrape_listings
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
	url = "https://streeteasy.com/for-rent/nyc/area:100,300%7Cbeds:1"
	num_pages = 500
	df = scrape_listings(url, num_pages)

	#drop listings we already have in mongo
	df = df[~df['name'].isin(names)]

	#enrich the listings with details (from page and google maps)


if __name__ == '__main__':
	main()