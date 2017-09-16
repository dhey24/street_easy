import csv

filepath = '/Users/davidhey/Documents/G2_medianAskingRent_OneBd.csv'

with open(filepath, 'rb') as infile:
	reader = csv.reader(infile.read().splitlines())
	headers = reader.next()
	for header in headers:
		print headers.index(header), header

	new_header = ["Area", "Boro", "Area Type", "Date", "Median Price"]

	name_changes = {"Bedford-Stuyvesant": "Bedford Stuyvesant",
					"Soho": "SoHo",
					"Stuyvesant Town": "Stuyvesant Town/PCV",
					"Nolita": "NoHo",
					"Flatiron": "Flatiron District",
					"Gramercy Park": "Gramercy",
					"Central Park South": "Midtown",
					"Lincoln Square": "Columbus Circle",
					"Kips Bay": "Tudor City",
					"Downtown Brooklyn": "Downtown",
					"Columbia St Waterfront District": "Columbia Street Waterfront District"}

	with open("/Users/davidhey/Documents/G2_medianAskingRent_OneBd_trans.csv", "wb") as outfile:
		writer = csv.writer(outfile)
		writer.writerow(new_header)
		for row in reader:
			#correct names
			if row[0] in name_changes.keys():
				row[0] = name_changes[row[0]]

			for col in row[4:]:
				write_row = row[0:3]
				write_row.append(headers[row.index(col)])
				write_row.append(col)
				writer.writerow(write_row)