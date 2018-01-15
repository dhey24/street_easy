from pymongo import MongoClient
from street_easy_scraping2 import scrape_listings
from scrape_details import scrape_details_wrapper
from commute_times import commute_time
from secret import MONGO_USER, MONGO_PW, SECRET_KEY
from places import place_agg
import googlemaps
import pprint
from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
import datetime


def mongo_connect(user, pw):
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

	#set up street easy browser
	browser = webdriver.Chrome(executable_path = "/Users/davidhey/Documents/chromedriver")
	browser.set_window_position(0, 0)
	browser.set_window_size(700, 1000)

	#look for listings that are not in names
	url = "https://streeteasy.com/for-rent/nyc/area:100,300%7Cbeds:1"
	#url = "https://streeteasy.com/for-rent/long-island-city/beds:1"
	df = scrape_listings(url, page_cutoff=50)

	#drop listings we already have in mongo
	df = df[~df['name'].isin(names)]

	#set up google maps client/variables
	api_key =  SECRET_KEY
	client = googlemaps.Client(key=api_key)
	origins_dict = {"wework_49th_" : "Tower 49, 12 E 49th St, New York, NY 10017"}

	#convert df to list of dicts
	print df.head()
	listings = df.to_dict(orient='records')
	print type(listings)
	pprint.pprint(listings)

	#connect to mongo
	coll = mongo_connect(MONGO_USER, MONGO_PW)

	#ENRICH
	while len(listings) > 0:
		listing = listings.pop(0)

		try:
			#query google maps distance matrix info for each url
			ll = listing["latlong"].split(',')
			latlng = {"lat": float(ll[0]), 
					   "lng": float(ll[1])}
			destinations = [latlng]

			for prefix, addr in origins_dict.iteritems():
				origins = [addr]
				commute_payload, client = \
					commute_time(origins, destinations, api_key, client)
				for key, val in commute_payload.iteritems():
					listing[prefix+key] = val
			
			#query google maps places api for important stuff nearby
			try:
				place_fields = place_agg(listing['latlong'])
				for key, val in place_fields.iteritems():
					listing[key] = val
			except Exception as ex:
				print "ERROR: While getting nearby places \n%s" % str(ex)

			#query street easy details for each url
			deets_payload = scrape_details_wrapper(browser, listing["url"])
			#pprint.pprint(deets_payload)
			if deets_payload['status']:
				#combine payload with listing
				for key, val in deets_payload.iteritems():
					if key != "status":
						listing[key] = val

				#add created datetime to listing record
				listing['created_at'] = datetime.datetime.now()
				pprint.pprint(listing)

				#insert listing into mongo
				result = coll.insert_one(listing)
				print "mongo now has %s rows" % (str(coll.count()))
			else:
				#add it back to the end of the list
				listings.append(listing)

			print str(len(listings)) + " items remaining \n"
		except Exception as e:
			print "EXCEPTION: some sort of error during listing enrichment"
			print e
			listings.append(listing)


if __name__ == '__main__':
	main()