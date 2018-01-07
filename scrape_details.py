import numpy as np
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
import csv
import time
import random
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options
import pprint


def scrape_details_wrapper(browser, url):
	"""same as scrape_details, but returns dict"""
	amens = []
	stops = []
	description = ''
	min_dist = 100
	nearest_stop = ''
	status = True
	no_fee = ''
	try:
		browser.get(url)
		try:
			wait = WebDriverWait(browser, 30)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'building-title')))
			print "Page is ready!"
			html_doc = browser.page_source
			soup = BeautifulSoup(html_doc, "html.parser")

			#no fee?
			s_fee = soup.find_all('div', class_='status nofee')
			if len(s_fee) > 0: 	#double check this doesnt break with fee apts
				no_fee = s_fee[0].text
			else:
				no_fee = "FEE"

			#find amenities
			s_amens = soup.find_all('div', class_='third')
			for div in s_amens:
				if div.find("li") != None:
					amens.append(div.find("li").string)

			#highlights
			s_amens = soup.find_all('img', class_='amenities_icon')
			for img in s_amens:
				amens.append(img.parent.text.strip())

			#description
			desc = soup.find_all('blockquote')
			#check if we got blocked
			if len(desc) == 0:
				print "BLOCKED??!?"
				print page.content
				description = ''
			else:
				description = desc[0].text
				description = re.sub(r'[^\x00-\x7F]+', '*', description)

			#subways
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
				#find nearest subway
				for stop in stops:
				 	dist = float(stop['distance'].split(' ')[0])
				 	if dist < min_dist:
				 		nearest_stop = stop['stop'] + ' ' + str(stop['lines'])
				 		min_dist = dist

			except:
				print "subway extract failed"
				
		except TimeoutException:
			print "page took too long to load..."
			status = False

	except:
		print "ERROR: URL get failed!"
		status = False

	time.sleep(random.randint(1,5))

	details_dict = {"url": url,
					"amenities": amens,
					"description": description,
					"stops": stops,
					"status": status,
					"min_dist": min_dist,
					"nearest_stop": nearest_stop,
					"no_fee": no_fee}

	return details_dict


def scrape_details(browser, url):
	amens = []
	stops = []
	description = ''
	min_dist = 100
	nearest_stop = ''
	status = True
	try:
		browser.get(url)
		try:
			wait = WebDriverWait(browser, 10)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'initial')))
			print "Page is ready!"
			html_doc = browser.page_source
			soup = BeautifulSoup(html_doc, "html.parser")

			#find amenities
			s_amens = soup.find_all('div', class_='third')
			for div in s_amens:
				if div.find("li") != None:
					amens.append(div.find("li").string)

			#highlights
			s_amens = soup.find_all('img', class_='amenities_icon')
			for img in s_amens:
				amens.append(img.parent.text.strip())

			#description
			desc = soup.find_all('blockquote')
			#check if we got blocked
			if len(desc) == 0:
				print "BLOCKED??!?"
				print page.content
				description = ''
			else:
				description = desc[0].text
				description = re.sub(r'[^\x00-\x7F]+', '*', description)

			#subways
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
				#find nearest subway
				for stop in stops:
				 	dist = float(stop['distance'].split(' ')[0])
				 	if dist < min_dist:
				 		nearest_stop = stop['stop'] + ' ' + str(stop['lines'])
				 		min_dist = dist

			except:
				print "subway extract failed"
				
		except TimeoutException:
			print "page took too long to load..."
			status = False

	except:
		print "ERROR: URL get failed!"
		status = False

	time.sleep(random.randint(1,5))

	return amens, description, stops, status, min_dist, nearest_stop


def main():
	browser = webdriver.Chrome(executable_path = "/Users/davidhey/Documents/chromedriver")
	browser.set_window_position(0, 0)
	browser.set_window_size(700, 1000)

	filepath = './apartment_meta_scrape2.csv'

	url_backlog = []

	#read pre scraped metadata
	with open(filepath, 'rb') as infile:
		reader = csv.reader(infile.read().splitlines())
		
		headers = reader.next()
		for header in headers:
			print headers.index(header), header
		new_headers = ["amenities", "description", "subways", "min_subway_dist", "nearest_subway_stop"]
		headers = headers + new_headers

		#open file to write enriched data to
		with open("./apartment_meta_scrape-enriched2.csv", "wb") as outfile:
			writer = csv.writer(outfile)
			writer.writerow(headers)
			for row in reader:
				url = row[8]
				amens, description, stops, status, min_dist, nearest_stop = scrape_details(browser, url)
				if status:
					row.append(amens)
					row.append(description)
					row.append(stops)
					row.append(min_dist)
					row.append(nearest_stop)
					pprint.pprint({"description": description, "amens": amens})

					writer.writerow(row)
				else:
					url_backlog.append(row)

			#now handle all the pages that timed out
			while len(url_backlog) > 0:
				row = url_backlog.pop(0)
				url = row[8]
				amens, description, stops, status, min_dist, nearest_stop = scrape_details(browser, url)
				if status:
					row.append(amens)
					row.append(description)
					row.append(stops)
					row.append(min_dist)
					row.append(nearest_stop)
					pprint.pprint({"description": description, "amens": amens})

					writer.writerow(row)
					print str(len(url_backlog)) + " items remaining in the backlog. \n"
				else:
					url_backlog.append(url)
					print str(len(url_backlog)) + " items remaining in the backlog. \n"
					time.sleep(random.randint(1, 10))


if __name__ == '__main__':
	main()