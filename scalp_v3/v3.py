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
	realised_pnl = my_balance["info"]["result"]["list"][0]["coin"][0]["cumRealisedPnl"]
	unrealised_pnl = my_balance["info"]["result"]["list"][0]["coin"][0]["unrealisedPnl"]
	wallet_balance = my_balance["USDT"]["total"]
	equity = my_balance["info"]["result"]["list"][0]["coin"][0]["equity"]

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

	# print(orders)

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

			print("│     Buy Close order:", tp_buy_order_size, tp_buy_order_price)

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

			print("│     Sell Close order:", tp_sell_order_size, tp_sell_order_price)

		else:
			# print('No Close Sell orders found')
			pass


#--------------------------------------------------------------------------

def get_sma_3_1_low_bybit():
	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 3-1 Low"] = ta.trend.SMAIndicator(df["Low"], window=3).sma_indicator()
	global sma_3_1_low_bybit
	sma_3_1_low_bybit = round((df["SMA 3-1 Low"][2]).astype(float), decimals)

def get_sma_3_5_low_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 3-5 Low"] = ta.trend.SMAIndicator(df["Low"], window=3).sma_indicator()
	global sma_3_5_low_bybit
	sma_3_5_low_bybit = round((df["SMA 3-5 Low"][2]).astype(float), decimals)


def get_sma_3_1_high_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 3-1 High"] = ta.trend.SMAIndicator(df["High"], window=3).sma_indicator()
	global sma_3_1_high_bybit
	sma_3_1_high_bybit = round((df["SMA 3-1 High"][2]).astype(float), decimals)


def get_sma_3_5_high_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=3)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 3-5 High"] = ta.trend.SMAIndicator(df["High"], window=3).sma_indicator()
	global sma_3_5_high_bybit
	sma_3_5_high_bybit = round((df["SMA 3-5 High"][2]).astype(float), decimals)


# ------------------------------


def get_sma_6_5_high_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=6)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 6-5 High"] = ta.trend.SMAIndicator(df["High"], window=6).sma_indicator()
	global sma_6_5_high_bybit
	sma_6_5_high_bybit = round((df["SMA 6-5 High"][5]).astype(float), decimals)


def get_sma_6_1_high_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=6)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 6-1 High"] = ta.trend.SMAIndicator(df["High"], window=6).sma_indicator()
	global sma_6_1_high_bybit
	sma_6_1_high_bybit = round((df["SMA 6-1 High"][5]).astype(float), decimals)


def get_sma_6_5_low_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=6)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 6-5 Low"] = ta.trend.SMAIndicator(df["Low"], window=6).sma_indicator()
	global sma_6_5_low_bybit
	sma_6_5_low_bybit = round((df["SMA 6-5 Low"][5]).astype(float), decimals)


def get_sma_6_1_low_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=6)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 6-1 Low"] = ta.trend.SMAIndicator(df["Low"], window=6).sma_indicator()
	global sma_6_1_low_bybit
	sma_6_1_low_bybit = round((df["SMA 6-1 Low"][5]).astype(float), decimals)


# ------------------------------


def get_sma_30_5_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=30)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 30-5 Close"] = ta.trend.SMAIndicator(df["Close"], window=30).sma_indicator()
	global sma_30_5_close_bybit
	sma_30_5_close_bybit = round((df["SMA 30-5 Close"][29]).astype(float), decimals)


def get_sma_30_1_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=30)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 30-1 Close"] = ta.trend.SMAIndicator(df["Close"], window=30).sma_indicator()
	global sma_30_1_close_bybit
	sma_30_1_close_bybit = round((df["SMA 30-1 Close"][29]).astype(float), decimals)


# ------------------------------


def get_sma_60_5_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=60)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 60-5 Close"] = ta.trend.SMAIndicator(df["Close"], window=60).sma_indicator()
	global sma_60_5_close_bybit
	sma_60_5_close_bybit = round((df["SMA 60-5 Close"][59]).astype(float), decimals)


def get_sma_60_1_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=60)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 60-1 Close"] = ta.trend.SMAIndicator(df["Close"], window=60).sma_indicator()
	global sma_60_1_close_bybit
	sma_60_1_close_bybit = round((df["SMA 60-1 Close"][59]).astype(float), decimals)


# ------------------------------


def get_sma_120_5_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="5m", limit=120)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 120-5 Close"] = ta.trend.SMAIndicator(df["Close"], window=120).sma_indicator()
	global sma_120_5_close_bybit
	sma_120_5_close_bybit = round((df["SMA 120-5 Close"][119]).astype(float), decimals)


def get_sma_120_1_close_bybit():

	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1m", limit=120)
	df = pd.DataFrame(bars, columns=["Time", "Open", "High", "Low", "Close", "Vol"])
	df["SMA 120-1 Close"] = ta.trend.SMAIndicator(df["Close"], window=120).sma_indicator()
	global sma_120_1_close_bybit
	sma_120_1_close_bybit = round((df["SMA 120-1 Close"][119]).astype(float), decimals)


# ------------------------------


def get_average_daily_range():
	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1d", limit=daily_range_compared)
	df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "vol"])
	df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
	df.set_index('timestamp', inplace=True)
	df['average_daily_range'] = df['high'] - df['low']
	global average_daily_range
	average_daily_range = round(df['average_daily_range'].tail(daily_range_compared).mean(), decimals)


def get_today_range():
	bars = exchange.fetchOHLCV(symbol=symbol, timeframe="1d", limit=1)
	df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "vol"])
	df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
	df.set_index('timestamp', inplace=True)
	df['today_range'] = df['high'] - df['low']
	global today_range_poin
	today_range_poin = round(df['today_range'].tail(daily_range_compared).mean(), decimals)

############ END FUNCTION AND LIBRARY ###############

exchange = ccxt.bybit({"apiKey": api_key, "secret": api_secret})
client = usdt_perpetual.HTTP(endpoint=endpoint, api_key=api_key, api_secret=api_secret)

#enable_trading = input("Enable Trading? (0 - Disable, 1 - Enable) ")
enable_trading = "0"

#symbol = input("What Asset To trade? ")
symbol = "eos"
symbol = (symbol + "USDT").upper()

try:
	get_decimals()
except Exception as e:
	get_linenumber()
	print(line_number, "exeception: {}".format(e))
	pass

time.sleep(0.01)

print("Min lot size for", symbol, "is:", min_trading_qty)
print("Max leverage is:", leverage)

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

print("        1x size:", what_1x_is)
print("        0.1x is:", what_1x_is / 10)
print("          0.01x:", what_1x_is / 100)

#min_lot_size = input("What size to trade? ")
min_lot_size = 0.1

daily_range_compared = 2

pipstep_devide = 10

started = datetime.datetime.now().strftime("%H:%M:%S")

while True:

	os.system('clear')

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

		get_sma_3_1_high_bybit()
		get_sma_3_1_low_bybit()
		time.sleep(0.01)
		get_sma_3_5_high_bybit()
		get_sma_3_5_low_bybit()
		time.sleep(0.01)
		get_sma_6_1_high_bybit()
		get_sma_6_1_low_bybit()
		time.sleep(0.01)
		get_sma_6_5_high_bybit()
		get_sma_6_5_low_bybit()
		time.sleep(0.01)
		get_sma_30_1_close_bybit()
		get_sma_30_5_close_bybit()
		time.sleep(0.01)
		get_sma_60_1_close_bybit()
		get_sma_60_5_close_bybit()
		time.sleep(0.01)
		get_sma_120_1_close_bybit()
		get_sma_120_5_close_bybit()
		time.sleep(0.01)
		get_average_daily_range()
		get_today_range()
		time.sleep(0.01)

	except Exception as e:
		get_linenumber()
		print(line_number, "exeception: {}".format(e))
		pass

	if (sma_30_1_close_bybit > sma_60_1_close_bybit
		and sma_60_1_close_bybit > sma_120_1_close_bybit
		and sma_3_1_low_bybit > sma_30_1_close_bybit):
		good_short_1m = True
	else:
		good_short_1m = False


	if (sma_30_5_close_bybit > sma_60_5_close_bybit
		and sma_60_5_close_bybit > sma_120_5_close_bybit
		and sma_3_5_low_bybit > sma_30_5_close_bybit):
		good_short_5m = True
	else:
		good_short_5m = False


	good_short_trade_conditions = good_short_1m == True and good_short_5m == True

	#-------------------------------------------------------------

	if (sma_30_1_close_bybit < sma_60_1_close_bybit
		and sma_60_1_close_bybit < sma_120_1_close_bybit
		and sma_3_1_high_bybit < sma_30_1_close_bybit):
		good_long_1m = True
	else:
		good_long_1m = False


	if (sma_30_5_close_bybit < sma_60_5_close_bybit
		and sma_60_5_close_bybit < sma_120_5_close_bybit
		and sma_3_5_high_bybit < sma_30_5_close_bybit):
		good_long_5m = True
	else:
		good_long_5m = False


	good_long_trade_conditions = good_long_1m == True and good_long_5m == True

	print(Fore.YELLOW + "─────────────────────────────────────────────" + Style.RESET_ALL)
	print("          " + Fore.YELLOW + "Ryuryu's bybit bot v2.14" + Style.RESET_ALL + "           ")
	print(Fore.YELLOW + "─────────────────────────────────────────────" + Style.RESET_ALL)
	print("               Asset:", symbol)
	print("        Max leverage:", leverage)
	print("            Lot size:", min_lot_size, "| 1x:", what_1x_is)
	print("─────────────────────────────────────────────")

	if enable_trading == "1":
		print("             " + Fore.GREEN + "Trading: Enabled" + Style.RESET_ALL)
	if enable_trading == "0":
		print("             " + Fore.RED + "Trading: Disabled" + Style.RESET_ALL)

	profit = (float(realised_pnl) / (float(wallet_balance) - float(realised_pnl))) * 100
	profit = round(profit, 2)

	today_range_percent = round((today_range_poin / average_daily_range) * 100, 2)

	pipstep = round((average_daily_range / pipstep_devide), decimals)

	print("   Available Balance:", available_balance)
	print("      Wallet Balance:", wallet_balance)
	print("              Equity:", equity)
	print("        Realized PnL:", realised_pnl)
	print("      UnRealized PnL:", unrealised_pnl)
	print(Fore.GREEN + "              Profit:", profit, "%" + Style.RESET_ALL)
	print("─────────────────────────────────────────────")
	print("                 Ask:", ask)
	print("                 Bid:", bid)
	print("                ADRs:", average_daily_range, "/", daily_range_compared)
	print("     Today Distances:", today_range_poin, "/", today_range_percent, "%")
	print("             Pipstep:", pipstep)
	print("─────────────────────────────────────────────")
	print("        sma_3_1_high:", sma_3_1_high_bybit)
	print("         sma_3_1_low:", sma_3_1_low_bybit)
	print("        sma_3_5_high:", sma_3_5_high_bybit)
	print("         sma_3_5_low:", sma_3_5_low_bybit)
	print("      sma_30_1_close:", sma_30_1_close_bybit)
	print("      sma_30_5_close:", sma_30_5_close_bybit)
	print("      sma_60_1_close:", sma_60_1_close_bybit)
	print("      sma_60_5_close:", sma_60_5_close_bybit)
	print("     sma_120_1_close:", sma_120_1_close_bybit)
	print("     sma_120_5_close:", sma_120_5_close_bybit)
	print("─────────────────────────────────────────────")

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
		sell_position_price
	except NameError:
		sell_position_price = 0

	if(sell_position_size == 0):

		if good_short_1m == True:
			print("            " + Fore.RED + "Short 1M: Good" + Style.RESET_ALL)
		else:
			print("            Short 1M: Not Good")

		if good_short_5m == True:
			print("            " + Fore.RED + "Short 5M: Good" + Style.RESET_ALL)
		else:
			print("            Short 5M: Not Good")

		if good_short_trade_conditions == True:
			print("            " + Fore.RED + "You must: Sell Now" + Style.RESET_ALL)
		else:
			print("            You must: Wait")

	else:

		print("           Sell Size:", sell_position_size)
		print("          Sell Price:", sell_position_price)
		print("            You must: Wait until TP or CL")

	#-----------------------------------------------------------------
	
	print("─────────────────────────────────────────────")
	
	#-----------------------------------------------------------------

	try:
		buy_position_size
	except NameError:
		buy_position_size = 0

	try:
		buy_position_price
	except NameError:
		buy_position_price = 0

	if(buy_position_size == 0):

		if good_long_1m == True:
			print("             " + Fore.RED + "Long 1M: Good" + Style.RESET_ALL)
		else:
			print("             Long 1M: Not Good")

		if good_long_5m == True:
			print("             " + Fore.RED + "Long 5M: Good" + Style.RESET_ALL)
		else:
			print("             Long 5M: Not Good")

		if good_long_trade_conditions == True:
			print("            " + Fore.RED + "You must: Buy Now" + Style.RESET_ALL)
		else:
			print("            You must: Wait")

	else:

		print("            Buy Size:", buy_position_size)
		print("           Buy Price:", buy_position_price)
		print("            You must: Wait until TP or CL")


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
				qty=min_lot_size,
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
		if float(ask) < sma_30_1_close_bybit:
			try:
				close_entry_order_sell = client.place_active_order(
				side="Buy",
				symbol=symbol,
				order_type="Market",
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
				qty=min_lot_size,
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

	#Exit (Market) Entry Order Buy
	if buy_position_size > 0:
		if float(bid) > sma_30_1_close_bybit:
			try:
				close_entry_order_buy = client.place_active_order(
				side="Sell",
				symbol=symbol,
				order_type="Market",
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
	else:
		pass


	time.sleep(1)
