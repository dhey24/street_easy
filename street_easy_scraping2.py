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


def last_page(soup):
	"""are we on the last page of search results or not?"""
	last = False
	
	#find number of pages returned by search
	pages = soup.find_all('span', class_='page')
	if len(pages) > 0:
		last_page = pages[-1]
	else:
		return last

	if "current" in last_page['class']:
		last = True

	return last


def main():
	browser = webdriver.Chrome(executable_path = "/Users/davidhey/Documents/chromedriver")
	browser.set_window_position(0, 0)
	browser.set_window_size(400, 1000)
	browser.get('http://streeteasy.com/for-rent/nyc/area:115,107,105,157,305,321,328,307,303,304,320,319,302%7Cbeds:1')


	num_pages = 100
	apt_meta = []	
	for i in range(num_pages):
		try:
			wait = WebDriverWait(browser, 10)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'next')))
			print "Page is ready!"
			html_doc = browser.page_source
			
			soup = BeautifulSoup(html_doc, "html.parser")
			apts = soup.find_all("article", class_="item")
			
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
					try:
						apt_dict['n_bath'] = apt.find_all('li', {'class': 'last_detail_cell'})[0].string
					except IndexError:
						apt_dict['n_bath'] = "?"
					apt_dict['sq_feet'] = "?"
				if 'sq_feet' not in apt_dict.keys():
					apt_dict['sq_feet'] = re.sub(r'[^\x00-\x7F]+', '*', apt.find_all('li', {'class': 'last_detail_cell'})[0].string) 
				apt_dict['latlong'] = apt['se:map:point']

				pprint.pprint(apt_dict)
				apt_meta.append(apt_dict)

			to_click = browser.find_elements_by_class_name('next')
			pprint.pprint(to_click)
			to_click[0].click()

			#//*[@id="result-details"]/main/div[3]/nav/span[2]/a
			#//*[@id="result-details"]/main/div[3]/nav/span[2]/a
		except TimeoutException:
			print "Loading took too much time!"

	df = pd.DataFrame.from_dict(apt_meta)
	df.to_csv('apartment_meta_scrape.csv')

	return None


def scrape_listings(url, num_pages=1):
	"""Given a street easy search URL, pull all the listings into a dataframe
	   Note: need to manually check how many pages of results there are
	"""
	browser = webdriver.Chrome(executable_path = "/Users/davidhey/Documents/chromedriver")
	browser.set_window_position(0, 0)
	browser.set_window_size(400, 1000)
	browser.get(url)

	apt_meta = []
	last = False
	retry = 0
	while last == False and retry < 10:
		try:
			wait = WebDriverWait(browser, 10)
			wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'next')))
			print "Page is ready!"
			html_doc = browser.page_source
			soup = BeautifulSoup(html_doc, "html.parser")
			
			#are we on the last search results page?
			last = last_page(soup)

			apts = soup.find_all("article", class_="item")
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
					try:
						apt_dict['n_bath'] = apt.find_all('li', {'class': 'last_detail_cell'})[0].string
					except IndexError:
						apt_dict['n_bath'] = "?"
					apt_dict['sq_feet'] = "?"
				if 'sq_feet' not in apt_dict.keys():
					apt_dict['sq_feet'] = re.sub(r'[^\x00-\x7F]+', '*', apt.find_all('li', {'class': 'last_detail_cell'})[0].string) 
				apt_dict['latlong'] = apt['se:map:point']

				pprint.pprint(apt_dict)
				apt_meta.append(apt_dict)

			to_click = browser.find_elements_by_class_name('next')
			pprint.pprint(to_click)
			to_click[0].click()

		except TimeoutException:
			html_doc = browser.page_source
			soup = BeautifulSoup(html_doc, "html.parser")
			last = last_page(soup)
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

if __name__ == '__main__':
	main()