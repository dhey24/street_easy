import csv
import googlemaps
import pprint
from secret import *


def commute_time(origins, desinations, api_key, client=None):
	"""Get distance and time information from Google Maps API, using 
	   public transit
			origins = list of starting points
			destinations = list of end points
			api_key = key from google developers website

	   returns response of distance, and duration of travel (sec.), as well as
	   		the google api client for future usage

	   Note: basically assumes there is 1 origin and destination"""
	
	#error handling on input variables
	if type(origins) != type([]) or type(desinations) != type([]):
		print "ERROR: origins/destinations must be input as arrays!"
		return None
	elif len(origins) == 0 or len(desinations) == 0:
		print "ERROR: please enter at least one origin/destination!"
		return None

	#set up new api client if needed
	if client == None:
		client = googlemaps.Client(key=api_key)

	#query google maps API
	matrix = client.distance_matrix(origins, desinations, 
								   mode='transit',
								   units='imperial')
	pprint.pprint(matrix)
	
	# add distance and time to rows
	payload = {"distance": None,
			   "distance_m": None,
			   "duration_s": None}
	### IMPLEMENTATION ASSUMPTION ###
	#	this basically assumes a 1:1 origin to destination relationship
	#	if there are more that 1 response oject, this pulls the last one
	if matrix['status'] == 'OK':
		for m_row in matrix['rows']:
			for element in m_row['elements']:
				if element['status'] == 'OK':
					payload['distance'] = element['distance']['text']
					payload['distance_m'] = element['distance']['value']
					payload['duration_s'] = element['duration']['value']
				else:
					print 'ERROR: no content in Google Maps API element!'
	else:
		print 'ERROR: Google Maps API request failed!'

	return payload, client


def main():
	"""Use case looping through csv to enrich it with commute time data"""
	desinations = ["320 Park Ave S, New York, NY 10010"]

	api_key =  SECRET_KEY
	gmaps = googlemaps.Client(key=api_key)
	#### note distance matrix usage limits ###
	# 2,500 free elements per day, calculated as the sum of client-side and 
	#	server-side queries.
	# Maximum of 25 origins or 25 destinations per request.
	# 100 elements per request.

	filepath = './apartment_meta_scrape-enriched.csv'

	#read pre scraped metadata
	with open(filepath, 'rb') as infile:
		reader = csv.reader(infile.read().splitlines())

		headers = reader.next()
		for header in headers:
			print headers.index(header), header

		#new headers being added from Google Maps API
		new_headers = ['distance', 'distance_meters', 'duration_s']
		headers = headers + new_headers

		with open("./apartment_meta_scrape-enriched3.csv", "wb") as outfile:
			writer = csv.writer(outfile)
			writer.writerow(headers)
			for row in reader:
				#parse latlong info from street easy data
				ll_row = row[1].split(',')
				latlng = {"lat": float(ll_row[0]), 
						   "lng": float(ll_row[1])}
				origins = [latlng]

				#query google maps API
				matrix = gmaps.distance_matrix(origins, desinations, 
											   mode='transit',
											   units='imperial')
				pprint.pprint(matrix)
				# add distance and time to rows
				if matrix['status'] == 'OK':
					for m_row in matrix['rows']:
						for element in m_row['elements']:
							if element['status'] == 'OK':
								distance = element['distance']['text']
								distance_m = element['distance']['value']
								duration_s = element['duration']['value']
								#extend the row array
								row = row + [distance, distance_m, duration_s]
							else:
								print 'ERROR: no content in Google Maps API element!'
				else:
					print 'ERROR: Google Maps API request failed!'

				#write row to new csv
				writer.writerow(row)


if __name__ == '__main__':
	main()