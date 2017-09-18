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
import pprint


def scrape_details(browser, url):
	browser.get(url)
	amens = []
	stops = []
	description = ''
	status = True
	try:
		wait = WebDriverWait(browser, 10)
		wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'next')))
		print "Page is ready!"
		html_doc = browser.page_source
		soup = BeautifulSoup(html_doc, "html.parser")

		#find amenities
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
			
	except TimeoutException:
		print "page took too long to load..."
		status = False

	time.sleep(random.randint(1,5))

	return amens, description, stops, status


def main():
	ua = UserAgent()

	request_headers = {'User-Agent': str(ua.random)}
	browser = webdriver.Chrome(executable_path = "/Users/davidhey/Documents/chromedriver")
	browser.set_window_position(0, 0)
	browser.set_window_size(400, 1000)

	filepath = './apartment_meta_scrape.csv'

	url_backlog = []

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
				#page = requests.get(url, headers=request_headers)
				#soup = BeautifulSoup(page.content, "lxml")
				amens, description, stops, status = scrape_details(browser, url)
				if status:
					row.append(amens)
					row.append(description)
					row.append(stops)
					pprint.pprint({"description": description, "amens": amens})

					writer.writerow(row)
				else:
					url_backlog.append(url)

			#now handle all the pages that timed out
			while len(url_backlog) > 0:
				url = url_backlog.pop(0)
				amens, description, stops, status = scrape_details(browser, url)
				if status:
					row.append(amens)
					row.append(description)
					row.append(stops)
					pprint.pprint({"description": description, "amens": amens})

					writer.writerow(row)
				else:
					url_backlog.append(url)
					time.sleep(random.randint(1,10))


if __name__ == '__main__':
	main()
