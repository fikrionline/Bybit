import os
import requests
import json, operator
import time
from pprint import pprint

while True:

	os.system('clear')

	# send an HTTP request to the server
	response = requests.get('https://aadresearch.xyz/api/api_data.php')

	# check if the request was successful (status code 200)
	if response.status_code == 200:
		# parse the JSON data into a Python object
		data = json.loads(response.text)
		data.sort(key=operator.itemgetter(1), reverse=True)
		# print the data
		#pprint(data)
		print ("{:<13} {:<9} {:<7} {:<6} {:<7}".format('Asset', 'Volume', 'Dist', 'MA', 'Time'))
		print("-----------------------------------------------")
		for i in data:
			asset = i[0]
			volume = round(i[1])
			distance = i[2]
			ma_order = i[3]
			time_now = time.strftime('%H:%M:%S')

			if(volume > 10000):
				if(distance > 0.1):
					print ("{:<13} {:<9} {:<7} {:<6} {:<7}".format(asset, volume, distance, ma_order, time_now))
	else:
		pprint('Error: could not retrieve data')


	time.sleep(5)
