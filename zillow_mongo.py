from pymongo import MongoClient
from zillow_scraping import scrape_zillow_listings, scrape_zillow_details
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
import random

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
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_argument("--incognito")
	browser = webdriver.Chrome(executable_path = "/Users/davidhey/Documents/chromedriver",
							   chrome_options=chrome_options)
	browser.set_window_position(0, 0)
	browser.set_window_size(700, 1000)

	#look for listings that are not in names
	url = 'https://www.zillow.com/homes/for_rent/Brooklyn-New-York-NY/house,condo,' + \
		  'apartment_duplex,mobile,townhouse_type/37607_rid/1-_beds/0-889125_price/' + \
		  '0-3500_mp/40.743225,-73.813878,40.567154,-74.06107_rect/11_zm/'
	# url = "https://www.zillow.com/homes/for_rent/Gowanus-Brooklyn-New-York-NY/house,condo,apartment_duplex,mobile,townhouse_type/270846_rid/1-_beds/0-888807_price/0-3500_mp/40.686512,-73.974274,40.66451,-74.005173_rect/14_zm/"
	df = scrape_zillow_listings(url, page_cutoff=1)

	#drop listings we already have in mongo
	#df = df[~df['name'].isin(names)]

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
		# go to the listing page and get the needed details
		deets_payload = scrape_zillow_details(browser, listings)
		#pprint.pprint(deets_payload)
		# if deets_payload['status']:
		# 	#combine payload with listing
		# 	for key, val in deets_payload.iteritems():
		# 		if key != "status":
		# 			listing[key] = val

		pprint.pprint(deets_payload)
		print len(listings)

		# if listing["address"] in names:
		# 	print "DONT WRITE TO MONGO"

		# try:
		# 	#query google maps distance matrix info for each url
		# 	ll = listing["latlong"].split(',')
		# 	latlng = {"lat": float(ll[0]), 
		# 			   "lng": float(ll[1])}
		# 	destinations = [latlng]

		# 	for prefix, addr in origins_dict.iteritems():
		# 		origins = [addr]
		# 		commute_payload, client = \
		# 			commute_time(origins, destinations, api_key, client)
		# 		for key, val in commute_payload.iteritems():
		# 			listing[prefix+key] = val
			
		# 	#query google maps places api for important stuff nearby
		# 	try:
		# 		place_fields = place_agg(listing['latlong'])
		# 		for key, val in place_fields.iteritems():
		# 			listing[key] = val
		# 	except Exception as ex:
		# 		print "ERROR: While getting nearby places \n%s" % str(ex)

			

		# 		#add created datetime to listing record
		# 		listing['created_at'] = datetime.datetime.now()
		# 		pprint.pprint(listing)

		# 		#insert listing into mongo
		# 		result = coll.insert_one(listing)
		# 		print "mongo now has %s rows" % (str(coll.count()))
		# 	else:
		# 		#add it back to the end of the list
		# 		listings.append(listing)

		# 	print str(len(listings)) + " items remaining \n"
		# except Exception as e:
		# 	print "EXCEPTION: some sort of error during listing enrichment"
		# 	print e
		# 	listings.append(listing)


if __name__ == '__main__':
	main()