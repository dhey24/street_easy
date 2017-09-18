import numpy as np
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
import csv
import time
import random


ua = UserAgent()
request_headers = {'User-Agent': str(ua.random)}
filepath = './apartment_meta_scrape.csv'

#read pre scraped metadata
with open(filepath, 'rb') as infile:
	reader = csv.reader(infile.read().splitlines())
	
	headers = reader.next()
	for header in headers:
		print headers.index(header), header
	new_headers = ["amenities", "description", "subways"]
	headers = headers + new_headers

	#open file to write enriched data to
	with open("./apartment_meta_scrape-enriched.csv", "wb") as outfile:
		writer = csv.writer(outfile)
		writer.writerow(headers)
		for row in reader:
			url = row[8]
			page = requests.get(url, headers=request_headers)
			soup = BeautifulSoup(page.content, "lxml")

			#find amenities
			amens = []
			s_amens = soup.find_all('div', class_='third')
			for div in s_amens:
				if div.find("li") != None:
					amens.append(div.find("li").string)

			#description
			desc = soup.find_all('blockquote')
			#check if we got blocked
			if len(desc) == 0:
				print "BLOCKED??!?"
				print page.content
				description = ''
			else:
				description = desc[0].text

			#subways
			stops = []
			try:
				transportation = soup.find_all('div', class_='transportation')	#assumes subway is first
				subways = transportation[0].find_all('li')
				subway_dict = {}
				for subway in subways:
					lines = []
					for line in subway.find_all('span'):
						lines.append(line.string)
					#extract stop w/ regex
					found = re.search('at ([\w\s]+)\n', subway.text)
					stop = ''
					if found:
						stop = found.group(1)
					#write to dict of closest stops
					subway_dict['lines'] = lines
					subway_dict['distance'] = subway.find('b').string
					subway_dict['stop'] = stop
					stops.append(subway_dict)
			except:
				print "subway extract failed"

			#any other details

			#add columns to df/csv

			#write to csv
			row.append(amens)
			row.append(description)
			row.append(stops)

			writer.writerow(row)

			#sleep at random intervals
			time.sleep(random.randint(1,5))