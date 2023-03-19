# Bybit Trading Bot v2.14
# (C) 2022 Ryan Hayabusa 2022
# Github: https://github.com/ryu878
# Discord: ryuryu#4087
# Web: https://aadresearch.xyz
#######################################################################################################
# pip install -U pip
# pip install pybit
# pip install colorama
# pip install pandas
# pip install ta
# pip install ccxt==2.0.90

import os
import ta
import ccxt
import time
import json
import uuid
import random
import sqlite3
import datetime
import pandas as pd
from config import *
from inspect import currentframe
from pybit import usdt_perpetual
from colorama import init, Fore, Back, Style
from pprint import pprint

import requests
import operator

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

os.system('clear')

exchange = ccxt.bybit({"apiKey": api_key, "secret": api_secret})
client = usdt_perpetual.HTTP(endpoint=endpoint, api_key=api_key, api_secret=api_secret)

#enable_trading = input("Enable Trading? (0 - Disable, 1 - Enable) ")
enable_trading = "0"

#symbol = input("What Asset To trade? ")
symbol = "op"
symbol = (symbol + "USDT").upper()

try:
	get_decimals()
except Exception as e:
	get_linenumber()
	print(line_number, "exeception: {}".format(e))
	pass
time.sleep(0.01)

try:
	get_balance()
except Exception as e:
	get_linenumber()
	print(line_number, "exeception: {}".format(e))
	pass
time.sleep(0.01)

try:
	get_orderbook()
except Exception as e:
	get_linenumber()
	print(line_number, "exeception: {}".format(e))
time.sleep(0.01)

what_1x_is = round((float(equity) / float(ask)) / (100 / float(leverage)), 2)
max_size = what_1x_is

#lot_size = input("What size to trade? ")
lot_size = 0.1

daily_range_compared = 5

pipstep_devide = 10

try:
	get_average_daily_range()
except Exception as e:
	get_linenumber()
	print(line_number, "exeception: {}".format(e))
time.sleep(0.01)

try:
	get_today_highest_lowest()
except Exception as e:
	get_linenumber()
	print(line_number, "exeception: {}".format(e))
time.sleep(0.01)

started = datetime.datetime.now().strftime("%H:%M:%S")

while True:

	#os.system('clear')

	try:
		aadresearch_time
	except NameError:
		get_aadresearch()
		time.sleep(0.01)

	time_now = time.strftime('%S')
	if(float(time_now) - float(aadresearch_time) > 5 or float(time_now) - float(aadresearch_time) < 0):
		get_aadresearch()
		time.sleep(0.01)

	if(aadresearch_distance > 0.3 and aadresearch_volume > 10000):
		enable_trading = "1"
	else:
		enable_trading = "0"

	try:
		get_balance()
	except Exception as e:
		get_linenumber()
		print(line_number, "exeception: {}".format(e))
		pass
	time.sleep(0.01)

	try:
		get_orderbook()
	except Exception as e:
		get_linenumber()
		print(line_number, "exeception: {}".format(e))
	time.sleep(0.01)

	try:
		get_ema_3_15_high_bybit()
		get_ema_3_15_low_bybit()
		time.sleep(0.01)
	except Exception as e:
		get_linenumber()
		print(line_number, "exeception: {}".format(e))
		pass

	good_short_trade_conditions = bid > ema_3_15_high_bybit

	good_long_trade_conditions = ask < ema_3_15_low_bybit

	print(Fore.YELLOW + "─────────────────────────────────────────────" + Style.RESET_ALL)
	print("          " + Fore.YELLOW + "Ryuryu's bybit bot v2.14" + Style.RESET_ALL)
	print(Fore.YELLOW + "─────────────────────────────────────────────" + Style.RESET_ALL)
	print("               Asset:", symbol)
	print("     Min Trading QTY:", min_trading_qty)
	print("            Leverage:", leverage)
	print("             1x size:", what_1x_is)
	print("             0.1x is:", round(what_1x_is / 10, decimals))
	print("               0.01x:", round(what_1x_is / 100, decimals))
	print("─────────────────────────────────────────────")
	print("            Lot Size:", lot_size)
	print("─────────────────────────────────────────────")

	profit = (float(realised_pnl) / (float(wallet_balance) - float(realised_pnl))) * 100
	profit = round(profit, 2)

	if(bid > today_highest):
		today_highest = bid

	if(ask < today_lowest):
		today_lowest = ask

	today_range_poin = round(today_highest - today_lowest, decimals)

	today_range_percent = round((today_range_poin / average_daily_range) * 100, 2)

	pipstep = round((average_daily_range / pipstep_devide), decimals)

	print("   Available Balance:", available_balance)
	print("      Wallet Balance:", wallet_balance)
	print("              Equity:", equity)
	print("        Realized PnL:", realised_pnl)
	print("      UnRealized PnL:", unrealised_pnl)
	print(Fore.GREEN + "              Profit:", profit, "%" + Style.RESET_ALL)
	print("─────────────────────────────────────────────")
	print("                ADRs:", average_daily_range, "/", daily_range_compared)
	print("     Today Distances:", today_range_poin, "/", today_range_percent, "%")
	print("             Pipstep:", pipstep, "/", pipstep_devide)
	print("         AadResearch:", aadresearch_volume, "/", aadresearch_distance, "/", aadresearch_ma_order, "/", aadresearch_time)

	if enable_trading == "1":
		print("             " + Fore.GREEN + "Trading: Enabled" + Style.RESET_ALL)
	if enable_trading == "0":
		print("             " + Fore.RED + "Trading: Disabled" + Style.RESET_ALL)

	print("─────────────────────────────────────────────")
	print("                 Ask:", ask)
	print("                 Bid:", bid)
	#-----------------------------------------------------------------

	try:
		get_position()
		time.sleep(0.01)
	except Exception as e:
		get_linenumber()
		print(line_number, "exeception: {}".format(e))
		pass

	try:
		sell_position_size
	except NameError:
		sell_position_size = 0

	try:
		buy_position_size
	except NameError:
		buy_position_size = 0

	if(sell_position_size == 0 or buy_position_size == 0):
		try:
			get_ema_3_15_high_bybit()
			get_ema_3_15_low_bybit()
			time.sleep(0.01)
		except Exception as e:
			get_linenumber()
			print(line_number, "exeception: {}".format(e))
			pass

		print(" ema_3_15_high_bybit:", ema_3_15_high_bybit)
		print("  ema_3_15_low_bybit:", ema_3_15_low_bybit)

	else:
		pass
		
	print("─────────────────────────────────────────────")

	#-----------------------------------------------------------------

	if(sell_position_size == 0):
		if good_short_trade_conditions == True:
			print("      " + Fore.RED + "Short Position: Sell Now" + Style.RESET_ALL)
		else:
			print("      Short Position: Wait")

	else:

		print("           Sell Size:", sell_position_size)
		print("          Sell Price:", sell_position_price)
		print("            You must: Wait until TP or CL")

	#-----------------------------------------------------------------
	
	print("─────────────────────────────────────────────")

	if(buy_position_size == 0):
		if good_long_trade_conditions == True:
			print("       " + Fore.RED + "Long Position: Buy Now" + Style.RESET_ALL)
		else:
			print("       Long Position: Wait")

	else:

		print("            Buy Size:", buy_position_size)
		print("           Buy Price:", buy_position_price)
		print("            You must: Wait until TP or CL")


	#--------------------------------------------------------
	if(sell_position_size > 0 or buy_position_size > 0):
		try:
			get_ema_3_1_high_bybit()
			get_ema_3_1_low_bybit()
			time.sleep(0.01)
			get_ema_3_5_high_bybit()
			get_ema_3_5_low_bybit()
			time.sleep(0.01)
			get_ema_6_1_high_bybit()
			get_ema_6_1_low_bybit()
			time.sleep(0.01)
		except Exception as e:
			get_linenumber()
			print(line_number, "exeception: {}".format(e))
			pass


	#--------------------------------------------------------
	#First Short Entry
	if (
		enable_trading == "1"
		and sell_position_size == 0
		and sell_position_size < max_size
		and good_short_trade_conditions == True
	):

		try:
			place_first_entry_market_order_sell = client.place_active_order(
				side="Sell",
				symbol=symbol,
				order_type="Market",
				qty=lot_size,
				time_in_force="GoodTillCancel",
				reduce_only=False,
				close_on_trigger=False,
			)
			time.sleep(0.01)
		except Exception as e:
			get_linenumber()
			print(line_number, "exeception: {}".format(e))
			pass
	else:
		pass

	#Cancel Entry Order Sell
	if sell_position_size > 0:

		if float(ask) < float(ema_3_1_high_bybit) or float(ask) < float(ema_3_5_high_bybit):

			try:
				cancel_entry_orders()
				print("             I Think: if float(ask) < float(ema_3_1_high_bybit) or float(ask) < float(ema_3_5_high_bybit):")
				time.sleep(0.01)
			except Exception as e:
				get_linenumber()
				print(line_number, "exeception: {}".format(e))
				pass

	#Take Profir for Short
	if sell_position_size > 0:

		sell_tp_price = round(
			sell_position_price - (ema_6_1_high_bybit - ema_6_1_low_bybit), decimals
		)

		tp_buy_order_price = 0
		tp_buy_order_size = 0

		try:
			get_close_orders()
			time.sleep(0.01)
		except Exception as e:
			get_linenumber()
			print(line_number, "exeception: {}".format(e))
			pass

		print("     Take Profit Now:", sell_tp_price)

		if tp_buy_order_price != sell_tp_price or tp_buy_order_size != sell_position_size:

			try:
				cancel_close_orders()
				print("             I Think: if tp_buy_order_price != sell_tp_price or tp_buy_order_size != sell_position_size:")
				time.sleep(0.01)
			except Exception as e:
				get_linenumber()
				print(line_number, "exeception: {}".format(e))
				pass

			try:
				place_active_buy_limit_tp_order = client.place_active_order(
					side="Buy",
					symbol=symbol,
					order_type="Limit",
					price=sell_tp_price,
					qty=sell_position_size,
					time_in_force="GoodTillCancel",
					reduce_only=True,
					close_on_trigger=True,
				)
				time.sleep(0.01)
			except Exception as e:
				get_linenumber()
				print(line_number, "exeception: {}".format(e))
				pass

	#Additional Short Entry Orders
	if(sell_position_size > 0):
		not_good_short_take_profit = sell_position_price < ema_6_1_low_bybit
		if not_good_short_take_profit == True:
			print("     What happen now: " + Fore.RED + "sell_position_price < ema_6_1_low_bybit" + Style.RESET_ALL)
			print("   So, what the next: Wait to best position...")
	else:
		pass


	if (
		sell_position_size > 0
		and sell_position_size < max_size
		and good_short_trade_conditions == True
		and not_good_short_take_profit == True
	):

		print("   I can't wait more: OK, let's more order")

		try:
			cancel_entry_orders()
			time.sleep(0.01)
			place_entry_order = client.place_active_order(
				side="Sell",
				symbol=symbol,
				order_type="Limit",
				price=ask,
				qty=lot_size,
				time_in_force="GoodTillCancel",
				reduce_only=False,
				close_on_trigger=False,
			)
			time.sleep(0.01)
		except Exception as e:
			get_linenumber()
			print(line_number, "exeception: {}".format(e))
			pass
	else:
		pass



	#--------------------------------------------------------
	#First Long Entry
	if (
		enable_trading == "1"
		and buy_position_size == 0
		and buy_position_size < max_size
		and good_long_trade_conditions == True
	):

		try:
			place_first_entry_market_order_buy = client.place_active_order(
				side="Buy",
				symbol=symbol,
				order_type="Market",
				qty=lot_size,
				time_in_force="GoodTillCancel",
				reduce_only=False,
				close_on_trigger=False,
			)
			time.sleep(0.01)
		except Exception as e:
			get_linenumber()
			print(line_number, "exeception: {}".format(e))
			pass
	else:
		pass

	#Cancel Entry Order Buy
	if buy_position_size > 0:

		if float(bid) > float(ema_3_1_low_bybit) or float(bid) > float(ema_3_5_low_bybit):

			try:
				cancel_entry_orders()
				print("             I Think: if float(bid) > float(ema_3_1_low_bybit) or float(bid) > float(ema_3_5_low_bybit):")
				time.sleep(0.01)
			except Exception as e:
				get_linenumber()
				print(line_number, "exeception: {}".format(e))
				pass

	#Take Profir for Long
	if buy_position_size > 0:

		buy_tp_price = round(
			buy_position_price + (ema_6_1_high_bybit - ema_6_1_low_bybit), decimals
		)

		tp_sell_order_price = 0
		tp_sell_order_size = 0

		try:
			get_close_orders()
			time.sleep(0.01)
		except Exception as e:
			get_linenumber()
			print(line_number, "exeception: {}".format(e))
			pass

		print("     Take Profit Now:", buy_tp_price)

		if tp_sell_order_price != buy_tp_price or tp_sell_order_size != buy_position_size:

			try:
				cancel_close_orders()
				print("             I Think: if tp_sell_order_price != buy_tp_price or tp_sell_order_size != buy_position_size:")
				time.sleep(0.01)
			except Exception as e:
				get_linenumber()
				print(line_number, "exeception: {}".format(e))
				pass

			try:
				place_active_sell_limit_tp_order = client.place_active_order(
					side="Sell",
					symbol=symbol,
					order_type="Limit",
					price=buy_tp_price,
					qty=buy_position_size,
					time_in_force="GoodTillCancel",
					reduce_only=True,
					close_on_trigger=True,
				)
				time.sleep(0.01)
			except Exception as e:
				get_linenumber()
				print(line_number, "exeception: {}".format(e))
				pass

	#Additional Long Entry Orders
	if(buy_position_size > 0):
		not_good_long_take_profit = buy_position_price > ema_6_1_high_bybit
		if not_good_long_take_profit == True:
			print("     What happen now: " + Fore.RED + "sell_position_price > ema_6_1_high_bybit" + Style.RESET_ALL)
			print("   So, what the next: Wait to best position...")
	else:
		pass


	if (
		buy_position_size > 0
		and buy_position_size < max_size
		and good_long_trade_conditions == True
		and not_good_long_take_profit == True
	):

		print("   I can't wait more: OK, let's more order")

		try:
			cancel_entry_orders()
			time.sleep(0.01)
			place_entry_order = client.place_active_order(
				side="Buy",
				symbol=symbol,
				order_type="Limit",
				price=ask,
				qty=lot_size,
				time_in_force="GoodTillCancel",
				reduce_only=False,
				close_on_trigger=False,
			)
			time.sleep(0.01)
		except Exception as e:
			get_linenumber()
			print(line_number, "exeception: {}".format(e))
			pass
	else:
		pass




	time.sleep(0.1)
