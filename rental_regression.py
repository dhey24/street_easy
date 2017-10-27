import pandas as pd 
import numpy as np
import pprint
from sklearn.cross_validation import train_test_split
from sklearn.linear_model import Lasso
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler


def combine_cols(row1, row2):
	"""combine columns that have missing data"""
	if pd.isnull(row1):
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


def print_features(feat_cols, coef):
	print "Coefficienct, Feature"
	for i in range(len(coef)):
		print coef[i], feat_cols[i]


def main():
	df = pd.read_csv("./mongo_listings.csv")
	print df.head()
	print df.columns.values

	#data cleanup
	df['description'] = df.apply(lambda row: combine_cols(row['description'], row['descricption']), axis=1)
	df['nearest_subway'] = df.apply(lambda row: combine_cols(row['nearest_subway_stop'], row['nearest_stop']), axis=1)
	df['nearest_subway_distance'] = df.apply(lambda row: combine_cols(row['min_dist'], row['min_subway_dist']), axis=1)
	df['work_distance'] = df.apply(lambda row: combine_cols(row['david_work_distance_m'], row['distance_meters']), axis=1)
	df['work_duration_s'] = df.apply(lambda row: combine_cols(row['david_work_duration_s'], row['duration_s']), axis=1)
	df['amenities'] = df.apply(lambda row: combine_cols(row['amenities'], row['amens']), axis=1)
	df['subways'] = df.apply(lambda row: combine_cols(row['stops'], row['subways']), axis=1)
	
	#fill missing square footage with mean -10
	df['sq_feet'] = df.apply(lambda row: sq_feet_cleanse(row['sq_feet']), axis=1)
	df['sq_feet'].fillna(df['sq_feet'].mean()-50, inplace=True)
	
	#cleanup price
	df['price'] = df.apply(lambda row: price_cleanse(row['price']), axis=1)
	#print df['price'].head()

	#drop unneeded columns
	wanted_cols = ['amenities', 'description', 'latlong', 'nearest_subway_distance',
				      'n_bath', 'n_bed', 'name', 'nearest_subway', 
				      'neighborhood', 'no_fee', 'price', 'sq_feet', 'subways',
				      'url', 'work_distance','work_duration_s']
	#only keep wanted columns
	print df.isnull().sum()
	df = df[wanted_cols]

	#add 0/1 for each amenity
	amenities = ['roof', 'dishwasher', 'terrace', 'balcony', 'doorman', 'elevator', 'washer/dryer in-unit']
	for amenity in amenities:
		df[amenity] = df.apply(lambda row: word_in_field(amenity, row['amenities']), axis=1)

	#1 if no fee, 0 if otherwise
	df['no_fee_bool'] = df.apply(lambda row: word_in_field("no fee", row['no_fee']), axis=1)

	#do multivariate linear regression to predict price
	feat_cols = [
				 'sq_feet', 
				 #'nearest_subway_distance', 
				 'work_duration_s',
		         'no_fee_bool', 
		         'roof', 
		         'dishwasher', 
		         #'terrace', 
		         'balcony', 
		         'doorman', 
		         #'elevator', 
		         'washer/dryer in-unit',
		         'price'] #price needs to be last
	#restrict columns used again
	df = df[feat_cols]
	
	#drop rows with null values
	print df.describe()
	print df.isnull().sum()
	df.dropna(inplace=True)
	print df.isnull().sum()

	#standardize numeric fields
	sq_feet_mean = df['sq_feet'].mean()
	sq_feet_sd = df['sq_feet'].std()
	df['sq_feet_std'] = df.apply(lambda row: (row['sq_feet'] - sq_feet_mean) / sq_feet_sd, axis=1)

	work_duration_s_mean = df['work_duration_s'].mean()
	work_duration_s_sd = df['work_duration_s'].std()
	df['work_duration_s_std'] = df.apply(lambda row: (row['work_duration_s'] - work_duration_s_mean) / work_duration_s_sd, axis=1)

	#replace og with standardized features
	feat_cols.remove('sq_feet')
	feat_cols.remove('work_duration_s')
	feat_cols.extend(['work_duration_s_std', 'sq_feet_std'])

	#test train split
	msk = np.random.rand(len(df)) < 0.8
	train_df = df[msk]
	test_df = df[~msk]
	print train_df.shape, "train"
	print test_df.shape, "test"

	feat_cols.remove("price")	#remove price from features
	y_train = train_df['price'].values
	X_train = train_df[list(feat_cols)].values

	y_test = test_df['price'].values
	X_test = test_df[list(feat_cols)].values
	print type(X_test)

	#lasso regression
	alphas = [100, 10, 5, 1, .5, .25, .1, .05, .025, .01, .001, 0]
	for alpha in alphas:
		print "\n### alpha = %s ###\n" % str(alpha)
		lasso = Lasso(alpha=alpha)

		clf = lasso.fit(X_train, y_train)
		y_pred_lasso = clf.predict(X_test)
		r2_score_lasso = r2_score(y_test, y_pred_lasso)
		print(lasso)
		print("r^2 on test data : %f" % r2_score_lasso)
		print "Intercept:\n", clf.intercept_
		print_features(feat_cols, clf.coef_)

		#error
		y_test = np.array(y_test)
		y_pred_lasso = np.array(y_pred_lasso)
		y_err = (y_pred_lasso - y_test)
		print "ERROR of first 5..."
		print y_err[0:5]


if __name__ == '__main__':
	main()