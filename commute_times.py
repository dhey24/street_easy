import csv
import googlemaps
import pprint
from secret import *

desinations = ["320 Park Ave S, New York, NY 10010"]

api_key =  SECRET_KEY
gmaps = googlemaps.Client(key=api_key)
#### note distance matrix usage limits ###
# 2,500 free elements per day, calculated as the sum of client-side and server-side queries.
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