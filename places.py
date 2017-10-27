import pprint
import requests
from secret import *
import time
from math import radians, sin, cos, sqrt, asin
 

def haversine(lat1, lon1, lat2, lon2):
  R = 6372.8 # Earth radius in miles
 
  dLat = radians(lat2 - lat1)
  dLon = radians(lon2 - lon1)
  lat1 = radians(lat1)
  lat2 = radians(lat2)
 
  a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
  c = 2*asin(sqrt(a))
 
  return R * c 


def google_places(payload):
	url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
	r = requests.get(url, params=payload)
	response = r.json()

	print "Status:", r.status_code

	return response


def count_places(query, location, cutoff_dist=.25):
	key = PLACES_SECRET_KEY	
	payload = {"query": query,
			   "key": key,
			   "rankby": "distance",
			   "location": location} #"40.744340, -73.978388"
	response = google_places(payload)

	token = True
	within_dist = True
	cutoff_dist = cutoff_dist
	places = []
	lat1 = float(location.split(",")[0])
	lon1 = float(location.split(",")[1])

	if response['status'] == "OK":
		results = response['results']
		for result in results:
			place = {'name': result['name'],
					 'location': result['geometry']['location']}
			lat2 = place['location']['lat']
			lon2 = place['location']['lng']
			distance = haversine(lat1, lon1, lat2, lon2)
			
			#only pull info within 200m
			if distance > cutoff_dist:
				within_dist = False
				break
			else:
				place['distance'] = distance
				places.append(place)

	while token and within_dist:
		if 'next_page_token' in response.keys():
			payload['pagetoken'] = response['next_page_token']
			time.sleep(2) #give the token a second to load
			response = google_places(payload)
			if response['status'] == "OK":
				results = response['results']
				for result in results:
					place = {'name': result['name'],
							 'location': result['geometry']['location']}
					lat2 = place['location']['lat']
					lon2 = place['location']['lng']
					distance = haversine(lat1, lon1, lat2, lon2)
					
					#only pull info within 200m
					if distance > cutoff_dist:
						within_dist = False
						break
					else:
						place['distance'] = distance
						places.append(place)
		else:
			token = False

	#pprint.pprint(places)
	return places


def place_agg(location):
	coffee_shops = count_places("coffee", location)
	shop_names = ""
	for shop in coffee_shops:
		shop_names = shop_names + shop['name'] + ", "
	shop_names = shop_names[:-2]

	groceries = count_places("grocery stores", location, cutoff_dist=.4)
	store_names = ""
	for shop in groceries:
		store_names = store_names + shop['name'] + ", "
	store_names = store_names[:-2]

	place_fields = {"coffee_count": len(coffee_shops),
					"coffee_names": shop_names,
					"grocery_count": len(groceries),
					"grocery_names": store_names}

	pprint.pprint(place_fields)
	
	return place_fields


def main():
	place_fields = place_agg("40.740674, -73.986164")
	

if __name__ == '__main__':
	main()