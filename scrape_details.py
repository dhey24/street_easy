import pandas as pd
import numpy as np
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re

df = pd.read_csv('./apartment_meta_scrape.csv')
ua = UserAgent()
headers = {'User-Agent': str(ua.random)}

for i in range(3):
	page = requests.get(df['url'][i], headers=headers)
	soup = BeautifulSoup(page.content, "lxml")

	#find amenities
	amens = []
	s_amens = soup.find_all('div', class_='third')
	for s_amen in s_amens:
		amen.append(s_amen.ul.li.string)

	#description
	desc = soup.find_all('blockquote')
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
			subway_dict['lines'] = lines
			subway_dict['distance'] = subway.find('b').string
			stops.append[subway_dict]

	#any other details

	#add columns to df/csv

	#write to csv
	