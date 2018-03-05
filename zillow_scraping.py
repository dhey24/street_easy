import time
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import unicodedata
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import re
import pprint
from pymongo import MongoClient
from commute_times import commute_time
from secret import MONGO_USER, MONGO_PW, SECRET_KEY
from places import place_agg
import googlemaps
import datetime
import random


def last_page(soup):
	"""are we on the last page of search results or not?"""
	last = False
	
	#find number of pages returned by search
	active_page = soup.find_all("li", "zsg-pagination_active")
	pg_num = int(active_page[0].a.contents[0])

	if len(pages) > 0:
		last_page = pages[-1]
	else:
		return last

	if "current" in last_page['class']:
		last = True

	return last


def scrape_zillow_listings(url, num_pages=1, page_cutoff=500):
	"""Given a street easy search URL, pull all the listings into a dataframe
	   Note: need to manually check how many pages of results there are
	"""
	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_argument("--incognito")
	browser = webdriver.Chrome(executable_path = "/Users/davidhey/Documents/chromedriver", 
							   chrome_options=chrome_options)
	browser.set_window_position(0, 0)
	browser.set_window_size(400, 1000)
	browser.get(url)

	apt_meta = []
	last = False
	retry = 0
	page_count = 1
	while last == False and retry < 10 and page_count <= page_cutoff:
		try:
			wait = WebDriverWait(browser, 10)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'on')))
			print "Page is ready!"
			html_doc = browser.page_source
			soup = BeautifulSoup(html_doc, "html.parser")
			
			#are we on the last search results page?
			#last = last_page(soup)

			xml_urls = soup.find_all("a", class_="zsg-photo-card-overlay-link")
			for xml_url in xml_urls:
				apt_meta.append({"url":
								 "https://www.zillow.com" + xml_url['href']})

			to_click = browser.find_elements_by_class_name('on')
			# make sure there is a next button
			if len(to_click) < 1:
				last = True
			else:
				to_click[0].click()

			page_count += 1

		except TimeoutException:
			html_doc = browser.page_source
			soup = BeautifulSoup(html_doc, "html.parser")
			#last = last_page(soup)
			if last == False:
				print "EXCEPTION: Loading took too much time!"
				retry += 1
				print "Retries so far = %i" % retry
		except Exception as e:
			print "EXCEPTION: other selinium exception (See below)"
			print e
			retry += 1

	df = pd.DataFrame.from_dict(apt_meta)

	return df


def scrape_zillow_details(browser, listings):
	"""same as scrape_details, but returns dict"""
	listing = listings.pop(0)
	url = listing['url']

	amens = []
	stops = []
	description = ''
	min_dist = 100
	nearest_stop = ''
	status = True
	no_fee = ''

	f_and_f = {"url": url, "status": True}

	# try:
	browser.get(url + "/?fullpage=true")
	#building URL
	if "/b/" in url:
		try:
			wait = WebDriverWait(browser, 60)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'bdp-info-container')))
			print "Page is ready!"

		except TimeoutException:
			print "page took too long to load..."
			f_and_f["status"] = False

		if f_and_f["status"]:
			html_doc = browser.page_source
			soup = BeautifulSoup(html_doc, "html.parser")
			for_rent = soup.find_all('div', id='units-panel-for-rent')
			if len(for_rent) > 0:
				apts = for_rent[0].find_all('a', href=True, class_='routable')
				# add listings from building
				for apt in apts:
					listings.append({"url": apt['href']})
					print apt['href']

	# INDIVIDUAL LISTING URL
	elif "/homedetails/" in url:
		try:
			wait = WebDriverWait(browser, 60)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'hdp-fact-category-title')))
			print "Page is ready!"

		except TimeoutException:
			print "page took too long to load..."
			f_and_f["status"] = False

		if f_and_f["status"]:
			try:
				html_doc = browser.page_source
				soup = BeautifulSoup(html_doc, "html.parser")

				# FACTS AND FEATURES, Expand for more
				to_click = browser.find_elements_by_class_name('hdp-fact-moreless-toggle')
				if len(to_click) > 0:
					to_click[0].click()
					time.sleep(random.randint(2,5))
				# view data summary
				to_click = browser.find_element_by_link_text("See data sources")
				to_click.click()
				time.sleep(random.randint(2,5))
				html_doc2 = browser.page_source
				soup2 = BeautifulSoup(html_doc2, "html.parser")
				table = soup2.find_all("table", summary="Home facts")[0]
				rows = table.find_all("tr", class_=False)
				rows.pop(0) # dont need header row
				
				for row in rows:
					cols = row.contents
					if cols[1].contents[0] != "--":
						f_key = cols[0].contents[0].split(":")[0]
						f_and_f[f_key] = cols[1].contents[0]
				# close data summary
				to_click = browser.find_elements_by_class_name('lightbox-close')
				to_click[1].click()
				time.sleep(random.randint(2,5))

				# ADDRESS
				addr = soup.find_all('h1', class_="notranslate")
				address = addr[0].contents[0]+addr[0].contents[1].contents[0]
				f_and_f["address"] = address

				# PRICE
				main_row = soup.find_all("div", "main-row  home-summary-row")
				price = main_row[0].contents[1].contents[0].strip()
				f_and_f['price'] = price

				# NEIGHBORHOOD
				hood = soup.find_all('section', id='hdp-neighborhood')
				h2s = hood[0].find_all('h2')
				hood_strings = h2s[0].string.split(":")
				neighborhood = hood_strings[1].strip()
				f_and_f['neighorhood'] = neighborhood
				# hood market
				market_temp = hood[0].find_all("div", "zsg-h2")[0].text
				market_change = hood[0].find_all("h5", "zsg-content_collapsed")[0].text
				market_median = hood[0].find_all("h2", "zsg-content_collapsed")[0].text

				# SELLER METRICS
				sms = soup.find_all("div", class_="seller-metric")
				for sm in sms:
					f_and_f[sm.contents[1].text.strip()] = sm.contents[0].text.strip()

				# SCHOOLS
				schools = soup.find_all("section", id="nearbySchools")
				ratings = schools[0].find_all("span", class_="gs-rating-number")
				school_ratings = []
				for rating in ratings:
					school_ratings.append(int(rating.text))
				f_and_f["school_ratings"] = school_ratings
			except Exception, e:
				print "EXCEPTION:", e
				f_and_f["status"] = False

	# except:
	# 	print "ERROR: URL get failed!"
	# 	f_and_f["status"] = False

	time.sleep(random.randint(1,5))

	return f_and_f


if __name__ == '__main__':
	main()