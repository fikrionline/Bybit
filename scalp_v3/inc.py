############### FUNCTION AND LIBRARY ###############
def get_linenumber():
	cf = currentframe()
	global line_number
	line_number = cf.f_back.f_lineno

def get_decimals():
	symbol_decimals = client.query_symbol()
	for decimal in symbol_decimals["result"]:
		if decimal["name"] == symbol:
			global decimals
			global leverage
			global tick_size
			global min_trading_qty
			global qty_step
			decimals = decimal["price_scale"]
			leverage = decimal["leverage_filter"]["max_leverage"]
			tick_size = decimal["price_filter"]["tick_size"]
			min_trading_qty = decimal["lot_size_filter"]["min_trading_qty"]
			qty_step = decimal["lot_size_filter"]["qty_step"]

def get_balance():
	my_balance = exchange.fetchBalance()
	#pprint(my_balance)
	global available_balance
	global realised_pnl
	global equity
	global wallet_balance
	global unrealised_pnl
	available_balance = my_balance["USDT"]["free"]
	#print(f"{available_balance=}")
	realised_pnl = my_balance["info"]["result"]["USDT"]["realised_pnl"]
	#print(f"{realised_pnl=}")
	unrealised_pnl = my_balance["info"]["result"]["USDT"]["unrealised_pnl"]
	#print(f"{unrealised_pnl=}")
	wallet_balance = my_balance["info"]["result"]["USDT"]["wallet_balance"]
	#print(f"{wallet_balance=}")
	equity = my_balance["info"]["result"]["USDT"]["equity"]
	#print(f"{equity=}")

def get_orderbook():
	orderbook = exchange.fetchOrderBook(symbol=symbol)
	global ask
	global bid
	bid = orderbook["bids"][0][0] if len(orderbook["bids"]) > 0 else None
	ask = orderbook["asks"][0][0] if len(orderbook["asks"]) > 0 else None

def get_position():
	positions = client.my_position(symbol=symbol)
	for position in positions["result"]:
		if position["side"] == "Sell":
			global sell_position_size
			global sell_position_price
			sell_position_size = position["size"]
			sell_position_price = position["entry_price"]
		if position["side"] == "Buy":
			global buy_position_size
			global buy_position_price
			buy_position_size = position["size"]
			buy_position_price = position["entry_price"]


def cancel_entry_orders():
	orders = client.get_active_order(symbol=symbol)
	for order in orders["result"]["data"]:
		if (
			order["order_status"] != "Filled"
			and order["side"] == "Sell"
			and order["order_status"] != "Cancelled"
			and order["reduce_only"] == False
		):
			client.cancel_active_order(symbol=symbol, order_id=order["order_id"])
		elif (
			order["order_status"] != "Filled"
			and order["side"] == "Buy"
			and order["order_status"] != "Cancelled"
			and order["reduce_only"] == False
		):
			client.cancel_active_order(symbol=symbol, order_id=order["order_id"])


def cancel_close_orders():
	orders = client.get_active_order(symbol=symbol)
	for order in orders["result"]["data"]:
		if (
			order["order_status"] != "Filled"
			and order["side"] == "Buy"
			and order["order_status"] != "Cancelled"
			and order["reduce_only"] == True
		):
			client.cancel_active_order(symbol=symbol, order_id=order["order_id"])
		elif (
			order["order_status"] != "Filled"
			and order["side"] == "Sell"
			and order["order_status"] != "Cancelled"
			and order["reduce_only"] == True
		):
			client.cancel_active_order(symbol=symbol, order_id=order["order_id"])

			
def get_close_orders():
	orders = client.get_active_order(symbol=symbol)

	for order in orders["result"]["data"]:

		global tp_buy_order_size
		global tp_buy_order_id
		global tp_buy_order_price
		global tp_sell_order_size
		global tp_sell_order_id
		global tp_sell_order_price

		if (
			order["order_status"] == "New"
			and order["order_status"]
			and order["order_status"] != "Filled"
			and order["side"] == "Buy"
			and order["reduce_only"] == True
		):

			tp_buy_order_size = order["qty"]
			tp_buy_order_id = order["order_id"]
			tp_buy_order_price = order["price"]

			print("     Buy Close Order:", tp_buy_order_size, "/", tp_buy_order_price)

		else:
			# print('No Close Buy orders found')
			pass

		if (
			order["order_status"] == "New"
			and order["order_status"]
			and order["order_status"] != "Filled"
			and order["side"] == "Sell"
			and order["reduce_only"] == True
		):

			tp_sell_order_size = order["qty"]
			tp_sell_order_id = order["order_id"]
			tp_sell_order_price = order["price"]

			print("    Sell Close Order:", tp_sell_order_size, "/", tp_sell_order_price)

		else:
			# print('No Close Sell orders found')
			pass


#--------------------------------------------------------------------------

def get_ema_3_1_low_bybit():
	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 3-1 Low"] = ta.trend.EMAIndicator(df["Low"], window=3).ema_indicator()
	global ema_3_1_low_bybit
	ema_3_1_low_bybit = round((df["EMA 3-1 Low"][2]).astype(float), decimals)

def get_ema_3_1_high_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 3-1 High"] = ta.trend.EMAIndicator(df["High"], window=3).ema_indicator()
	global ema_3_1_high_bybit
	ema_3_1_high_bybit = round((df["EMA 3-1 High"][2]).astype(float), decimals)


def get_ema_3_5_low_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 3-5 Low"] = ta.trend.EMAIndicator(df["Low"], window=3).ema_indicator()
	global ema_3_5_low_bybit
	ema_3_5_low_bybit = round((df["EMA 3-5 Low"][2]).astype(float), decimals)


def get_ema_3_5_high_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 3-5 High"] = ta.trend.EMAIndicator(df["High"], window=3).ema_indicator()
	global ema_3_5_high_bybit
	ema_3_5_high_bybit = round((df["EMA 3-5 High"][2]).astype(float), decimals)


def get_ema_3_15_low_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="15m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 3-15 Low"] = ta.trend.EMAIndicator(df["Low"], window=3).ema_indicator()
	global ema_3_15_low_bybit
	ema_3_15_low_bybit = round((df["EMA 3-15 Low"][2]).astype(float), decimals)


def get_ema_3_15_high_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="15m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 3-15 High"] = ta.trend.EMAIndicator(df["High"], window=3).ema_indicator()
	global ema_3_15_high_bybit
	ema_3_15_high_bybit = round((df["EMA 3-15 High"][2]).astype(float), decimals)


# ------------------------------


def get_ema_6_1_low_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=6)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 6-1 Low"] = ta.trend.EMAIndicator(df["Low"], window=6).ema_indicator()
	global ema_6_1_low_bybit
	ema_6_1_low_bybit = round((df["EMA 6-1 Low"][5]).astype(float), decimals)


def get_ema_6_1_high_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=6)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 6-1 High"] = ta.trend.EMAIndicator(df["High"], window=6).ema_indicator()
	global ema_6_1_high_bybit
	ema_6_1_high_bybit = round((df["EMA 6-1 High"][5]).astype(float), decimals)


def get_ema_6_5_low_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=6)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 6-5 Low"] = ta.trend.EMAIndicator(df["Low"], window=6).ema_indicator()
	global ema_6_5_low_bybit
	ema_6_5_low_bybit = round((df["EMA 6-5 Low"][5]).astype(float), decimals)


def get_ema_6_5_high_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=6)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 6-5 High"] = ta.trend.EMAIndicator(df["High"], window=6).ema_indicator()
	global ema_6_5_high_bybit
	ema_6_5_high_bybit = round((df["EMA 6-5 High"][5]).astype(float), decimals)


# ------------------------------


def get_ema_10_1_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=10)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 10-1 Close"] = ta.trend.EMAIndicator(df["Close"], window=10).ema_indicator()
	global ema_10_1_close_bybit
	ema_10_1_close_bybit = round((df["EMA 10-1 Close"][9]).astype(float), decimals)


def get_ema_30_1_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=30)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 30-1 Close"] = ta.trend.EMAIndicator(df["Close"], window=30).ema_indicator()
	global ema_30_1_close_bybit
	ema_30_1_close_bybit = round((df["EMA 30-1 Close"][29]).astype(float), decimals)


def get_ema_30_5_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=30)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 30-5 Close"] = ta.trend.EMAIndicator(df["Close"], window=30).ema_indicator()
	global ema_30_5_close_bybit
	ema_30_5_close_bybit = round((df["EMA 30-5 Close"][29]).astype(float), decimals)


# ------------------------------


def get_ema_60_1_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=60)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 60-1 Close"] = ta.trend.EMAIndicator(df["Close"], window=60).ema_indicator()
	global ema_60_1_close_bybit
	ema_60_1_close_bybit = round((df["EMA 60-1 Close"][59]).astype(float), decimals)


def get_ema_60_5_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=60)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 60-5 Close"] = ta.trend.EMAIndicator(df["Close"], window=60).ema_indicator()
	global ema_60_5_close_bybit
	ema_60_5_close_bybit = round((df["EMA 60-5 Close"][59]).astype(float), decimals)


# ------------------------------


def get_ema_120_1_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=120)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 120-1 Close"] = ta.trend.EMAIndicator(df["Close"], window=120).ema_indicator()
	global ema_120_1_close_bybit
	ema_120_1_close_bybit = round((df["EMA 120-1 Close"][119]).astype(float), decimals)


def get_ema_120_5_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=120)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["EMA 120-5 Close"] = ta.trend.EMAIndicator(df["Close"], window=120).ema_indicator()
	global ema_120_5_close_bybit
	ema_120_5_close_bybit = round((df["EMA 120-5 Close"][119]).astype(float), decimals)


# ------------------------------


def get_average_daily_range():
	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1d", limit=daily_range_compared)
	df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "vol"])
	df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
	df.set_index('timestamp', inplace=True)
	df['average_daily_range'] = df['high'] - df['low']
	global average_daily_range
	average_daily_range = round(df['average_daily_range'].tail(daily_range_compared).mean(), decimals)


def get_today_highest_lowest():
	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1d", limit=1)
	df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "vol"])
	df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
	#df.set_index('timestamp', inplace=True)
	global today_highest
	global today_lowest
	today_highest = df['high'][0]
	today_lowest = df['low'][0]


def get_volume():
	bars = exchange.fetch_ticker(symbol=symbol)
	global the_volume
	the_volume = round(bars['quoteVolume'], decimals)


def get_aadresearch():
	response = requests.get('https://aadresearch.xyz/api/api_data.php')
	if response.status_code == 200:
		data = json.loads(response.text)
		data.sort(key=operator.itemgetter(1), reverse=True)
		#pprint(data)
		#format('Asset', 'Volume', 'Dist', 'MA')
		for i in data:
			asset = i[0]
			volume = round(i[1])
			distance = i[2]
			ma_order = i[3]
			time_now = time.strftime('%S')
			if(asset == symbol):
				global aadresearch_volume
				global aadresearch_distance
				global aadresearch_ma_order
				global aadresearch_time
				aadresearch_volume = volume
				aadresearch_distance = distance
				aadresearch_ma_order = ma_order
				aadresearch_time = time_now
	else:
		pprint('Error: could not retrieve data')
		
############ END FUNCTION AND LIBRARY ###############
