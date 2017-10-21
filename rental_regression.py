import pandas as pd 
import pprint

def combine_cols(row1, row2):
	"""combine columns that have missing data"""
	if row1 == "NaN":
		return row2
	else:
		return row1


def word_in_field(word, field):
	"""look for a word in a field and return a 1 if present, 0 if not"""
	found = 0
	if type(field) == type([]):
		for item in field:
			if word in item.lower():
				found = 1
				break
	elif type(field) == type("string"):
		if word in field.lower():
			found = 1

	return found


def sq_feet_cleanse(field):
	"""data cleansing for sq_feet field"""
	if field == "?" or "bath" in field or "bed" in field:
		sq_feet = None
	else:
		field = field.split(" ")
		sq_feet = int(field[0].replace(",", ""))

	return sq_feet


def price_cleanse(field):
	"""take str(price) and turn it into int"""
	price = field.replace("$", "")
	price = price.replace(",", "")
	price = int(price)

	return price

def main():
	df = pd.read_csv("./mongo_listings.csv")
	print df.head()
	print df.columns.values

	#data cleanup
	df['description'] = df.apply(lambda row: combine_cols(row['description'], row['descricption']), axis=1)
	df['nearest_subway'] = df.apply(lambda row: combine_cols(row['nearest_subway_stop'], row['nearest_stop']), axis=1)
	df['nearest_subway_distance'] = df.apply(lambda row: combine_cols(row['min_dist'], row['min_subway_dist']), axis=1)
	df['work_distance'] = df.apply(lambda row: combine_cols(row['david_work_distance'], row['distance']), axis=1)
	df['work_duration_s'] = df.apply(lambda row: combine_cols(row['david_work_duration_s'], row['duration_s']), axis=1)
	df['amenities'] = df.apply(lambda row: combine_cols(row['amenities'], row['amens']), axis=1)
	df['subways'] = df.apply(lambda row: combine_cols(row['stops'], row['subways']), axis=1)
	
	#fill missing square footage with mean -10
	df['sq_feet'] = df.apply(lambda row: sq_feet_cleanse(row['sq_feet']), axis=1)
	print df['sq_feet'].head()
	df['sq_feet'].fillna(df['sq_feet'].mean()-50, inplace=True)
	print df['sq_feet'].head()
	
	#cleanup price
	df['price'] = df.apply(lambda row: price_cleanse(row['price']), axis=1)
	print df['price'].head()

	#drop unneeded columns
	wanted_cols = ['amenities', 'description', 'latlong', 'nearest_subway_distance',
				      'n_bath', 'n_bed', 'name', 'nearest_stop', 'nearest_subway', 
				      'neighborhood', 'no_fee', 'price', 'sq_feet', 'subways',
				      'url', 'work_distance','work_duration_s']
	#only keep wanted columns
	df = df[wanted_cols]

	#add 0/1 for each amenity
	amenities = ['roof', 'dishwasher', 'terrace', 'balcony', 'doorman', 'elevator', "washer/dryer in-unit"]
	for amenity in amenities:
		df[amenity] = df.apply(lambda row: word_in_field(amenity, row['amenities']), axis=1)

	#1 if no fee, 0 if otherwise
	df['no_fee_bool'] = df.apply(lambda row: word_in_field("no fee", row['no_fee']), axis=1)

	print df.head()
	print df.columns.values

	#do multivariate linear regression to predict price


if __name__ == '__main__':
	main()