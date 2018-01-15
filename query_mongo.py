import pandas as pd
import pymongo
from secret import MONGO_USER, MONGO_PW
from mongo import mongo_connect
from commute_times import commute_time
import pprint
from places import *
import re
import pprint
import googlemaps
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By


def replace_unicode(field):
	field = re.sub(r'[^\x00-\x7F]+', '*', field)

	return field 	


def main():
	"""pull all data from mongo into a csv
	"""
	coll = mongo_connect(MONGO_USER, MONGO_PW)
	#listings = coll.find({"no_fee": {"$regex": u"NO"}}).limit(10)
	listings = coll.find()
	df = pd.DataFrame(list(listings))
	#pprint.pprint(listings[0])
	pprint.pprint(df.columns.values)
	df['coffee_names'] = df.apply(lambda row: replace_unicode(row['coffee_names']), axis=1)
	df['grocery_names'] = df.apply(lambda row: replace_unicode(row['grocery_names']), axis=1)
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


def fill_null_neighborhoods():
	"""fill in the listings in mongo with null neighborhoods!
	"""
	coll = mongo_connect(MONGO_USER, MONGO_PW)
	listings = coll.find({"neighborhood":  None},
						 {'_id': 1, 
						  'url': 1}).sort( "_id", -1)

	# print len(listings), "listings to fix"

	browser = webdriver.Chrome(executable_path = "/Users/davidhey/Documents/chromedriver")
	browser.set_window_position(0, 0)
	browser.set_window_size(400, 1000)

	for listing in listings:
		pprint.pprint(listing)
		browser.get(listing['url'])
		try:
			wait = WebDriverWait(browser, 30)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'actions')))
			
			html_doc = browser.page_source
			soup = BeautifulSoup(html_doc, "html.parser")
			
			# extract hood from page
			neighborhood = ''
			if "This unit is not currently listed on StreetEasy" in soup.text:
				print "\nNO LONGER LISTED\n"
				details = soup.find_all("div", class_="details_info")
				try:
					neighborhood = details[0].text.strip().split(" in ")[1]
				except IndexError:
					neighborhood = details[0].text.strip()
			else:
				nobreaks = soup.find_all("span", class_="nobreak")
				for nobreak in nobreaks:
					if nobreak.find("a") != None:
						neighborhood = nobreak.a.text
			
			# update hood in mongo			
			if neighborhood != '':
				print neighborhood
				result = coll.update_one({"_id": listing['_id']},
						    			 {"$set": {"neighborhood": neighborhood}})
				print "modified:", result.modified_count
		except TimeoutException:
			print "page took too long to load..."


def add_commute(destination_address, destination_name):
	"""add a commute time for a new place of work
	"""
	coll = mongo_connect(MONGO_USER, MONGO_PW)
	ids = coll.find({destination_name + "distance_m": {"$exists": False}}, 
					{'_id': 1, 'latlong': 1})

	#set up google maps client/variables
	api_key =  SECRET_KEY
	client = googlemaps.Client(key=api_key)
	origins_dict = {destination_name: destination_address}

	for m_id in ids:
		ll = m_id["latlong"].split(',')
		latlng = {"lat": float(ll[0]), 
				   "lng": float(ll[1])}
		destinations = [latlng]

		for prefix, addr in origins_dict.iteritems():
			origins = [addr]
			commute_payload, client = \
				commute_time(origins, destinations, api_key, client)
			for key in commute_payload.keys():
				#key = prefix + key
				commute_payload[prefix + key] = commute_payload.pop(key)
			
			result = coll.update_one({"_id": m_id['_id']},
					    {"$set": commute_payload})

			#test = coll.find({"_id": m_id['_id']})
			#pprint.pprint(test[0])

			#print "modified:", result.modified_count
	return None


def test_commute(destination_name):
	coll = mongo_connect(MONGO_USER, MONGO_PW)
	ids = coll.find({destination_name + "distance_m": {"$exists": True}}).limit(5)
	for m_id in ids:
		pprint.pprint(m_id)

	return None


def query():
	"""fill in the listings in mongo with null neighborhoods!
	"""
	coll = mongo_connect(MONGO_USER, MONGO_PW)
	count = coll.find({"neighborhood":  "Unknown"}).count()

	print count


if __name__ == '__main__':
	#update_places()
	# main()
	fill_null_neighborhoods()
	#query()
	# add_commute("115 W 18th St, New York, NY 10011", "wework_chelsea_")
	# test_commute("wework_chelsea_")