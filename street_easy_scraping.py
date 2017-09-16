from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
import requests
import pprint as pp
from fake_useragent import UserAgent
import csv
import re
import time
import random
import pandas as pd


def scrape_tracklist(link, headers, artist, stage):
	"""scrape the tracklists info and write to csv"""
	tracklist = []
	time.sleep(random.randint(0, 5)) #occasionally pause for a few seconds

	page = requests.get(link, headers=headers)
	soup = BeautifulSoup(page.content, "lxml")
	tracks = soup.find_all("div", class_="details-title")

	with open(artist + "_TLwk2.csv", 'wb') as outfile:
		writer = csv.writer(outfile)

		for track in tracks:
			try:
				content = track.meta['content']
				pp.pprint(content)
				#replace unicode characters
				content = re.sub(r'[^\x00-\x7F]+', '*', content) 	
				writer.writerow([content, stage])
				tracklist.append(content)
			except TypeError:
				content = None
				continue

	return tracklist


def scrape_links(search_url, headers, all_artists, artist_meta, 
				 scrape_tracks=True):
	"""1. get all the tracklist URLs on a given page
	   2. navigate to those URLs and scrape the tracklists
	   3. write to csv"""
	page = requests.get(search_url, headers=headers)
	pp.pprint(page)
	soup = BeautifulSoup(page.content, "lxml")
	pages = soup.find_all("div", class_="tlLink")

	if len(pages) == 0:
		print "\nWE GOT BLOCKED?!?!\n"

	for page in pages:
		link = 'https://www.1001tracklists.com' + page.a['href']
		description = page.a.get_text()
		if "Tomorrowland Weekend " in description:
			description = description.split(" @ ")
			artist = description.pop(0)
			description = description[0].split(", ")
			stage = description.pop(0)
			weekend = description.pop(0)
			#only scrape tracklists if it has not been pulled already
			if artist not in all_artists:
				artist = re.sub(r'[^\x00-\x7F]+', '*', artist)
				artist_meta.append({'artist': artist, 
									'stage': stage, 
									'url': link,
									'weekend': weekend})
				all_artists.append(artist)

				print "\n" + artist, weekend + "\n"

				if scrape_tracks:
					scrape_tracklist(link, headers, artist, stage)

	return all_artists, artist_meta


def main():
	all_artists = []
	artist_meta = []

	for i in range(1, 1):
		if i == 1:
			search_url = "http://streeteasy.com/for-rent/nyc/status:open%7Carea:305,307%7Cbeds:1"
		else:
			search_url = "http://streeteasy.com/for-rent/nyc/status:open%7Carea:305,307%7Cbeds:1?page=" + \
						  str(i)
		time.sleep(random.randint(5, 15)) #occasionally pause for a few seconds

		ua = UserAgent()
		headers = {'User-Agent': str(ua.random)}

		all_artists, artist_meta = scrape_links(search_url, 
												headers, 
												all_artists, 
												artist_meta,
												scrape_tracks=True)

	#write artist reference metadata to seperate csv
	df = pd.DataFrame.from_dict(artist_meta)
	df.to_csv('Tomorrowland_wk2_artist_meta.csv')

if __name__ == '__main__':
	ua = UserAgent()
	headers = {'User-Agent': str(ua.random)}
	search_url = "http://streeteasy.com/for-rent/nyc/area:305%7Cbeds:1"
	#http://streeteasy.com/for-rent/nyc/area:305,307,320%7Cbeds:1
	page = requests.get(search_url, headers=headers)
	soup = BeautifulSoup(page.content, "lxml")
	apts = soup.find_all("article", class_="item")

	print len(apts)
	if len(apts) == 0:
		print page.content

	apt_meta = []	
	for apt in apts:
		apt_dict = {}
		apt_dict['name'] = apt.h3.a.string
		apt_dict['url'] = 'http://streeteasy.com' + apt.h3.a['href']
		apt_dict['price'] = apt.find_all('span', {'class': 'price'})[0].string
		try:
			apt_dict['neighborhood'] = apt.ul.a.string
		except AttributeError:
			apt_dict['neighborhood'] = "Unknown"
		apt_dict['n_bed'] = apt.find_all('li', {'class': 'first_detail_cell'})[0].string
		try:
			apt_dict['n_bath'] = apt.find_all('li', {'class': 'detail_cell'})[0].string
		except IndexError:
			apt_dict['n_bath'] = apt.find_all('li', {'class': 'last_detail_cell'})[0].string
			apt_dict['sq_feet'] = "?"
		if 'sq_feet' not in apt_dict.keys():
			apt_dict['sq_feet'] = re.sub(r'[^\x00-\x7F]+', '*', apt_dict['sq_feet']) 
		apt_dict['latlong'] = apt['se:map:point']

		pp.pprint(apt_dict)
		apt_meta.append(apt_dict)


	df = pd.DataFrame.from_dict(apt_meta)
	df.to_csv('apartment_meta_scrape.csv')



