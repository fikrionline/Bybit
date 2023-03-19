# Bybit Trading Bot v2.17
# (C) 2022 Ryan Hayabusa 2022
# Github: https://github.com/ryu878
# Discord: ryuryu#4087
# Web: https://aadresearch.xyz

import os
import ta
import ccxt
import time
import json
import uuid
import random
import sqlite3
import datetime
import requests
import operator
import pandas as pd

from inspect import currentframe
from pybit import usdt_perpetual
from colorama import init, Fore, Back, Style

from pprint import pprint
from config import *
from inc import *

ts = [['OPUSDT', 0.1], ['APTUSDT', 0.5], ['SOLUSDT', 0.1], ['APEUSDT', 0.1]]

os.system('clear')

exchange = ccxt.bybit({"apiKey": api_key, "secret": api_secret})
client = usdt_perpetual.HTTP(endpoint=endpoint, api_key=api_key, api_secret=api_secret)

response = requests.get('https://aadresearch.xyz/api/api_data.php')
if response.status_code == 200:
	data = json.loads(response.text)
	data.sort(key=operator.itemgetter(1), reverse=True)
	pprint(data)
	#format('Asset', 'Volume', 'Dist', 'MA')
	for i in data:
		asset = i[0]
		volume = round(i[1])
		distance = i[2]
		ma_order = i[3]
		time_now = time.strftime('%S')
else:
	pprint('Error: could not retrieve data')
