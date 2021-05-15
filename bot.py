import telebot
import binance
from kucoin.client import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import asyncio
from urllib.request import urlopen
import json
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from operator import itemgetter

# initial config

bot_token = "*****"
binance_key = "*****"
binance_sec = "*****"
kucoin_key = "*****"
kucoin_sec = "*****"
kucoin_api_pass = "*****"
coinmarketcap_apikey = "*****"
address_cardano = "your_ada_address"
bnb_address = "your_bnb_address"


# in USD
include_with_value_higher_than = 3

bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['check'])
def send_welcome(message):
	start_events(message)

def start_events(message):
	asyncio.run(parser(message))

async def parser(message):

	# Getting coins info from Binance

	client = binance.Client(binance_key, binance_sec)
	await client.load()

	accinfo = await client.fetch_account_information(receive_window=None)

	total = []
	for coin in accinfo['balances']:
		if coin['asset'] == "USDT" or coin['asset'] == "RUB":
			continue
		else:
			amount = float(coin['free'])
			ticker = coin['asset'] + "USDT"
			if amount > 0.000001:
				print(ticker[:-4] + f" amount: {amount}")
				coin.pop('locked')
				coin['amount'] = float(coin.pop('free'))
				total.append(coin)
	await client.close()

	# Getting the amount of ADA on Yoroi

	link_cardano = "https://www.cointracker.io/wallet/cardano"

	options = Options()
	options.add_argument('--headless')
	options.add_argument('--disable-gpu')
	
	browser = webdriver.Chrome(chrome_options = options)
	browser.get(link_cardano + "?address=" + address_cardano)
	time.sleep(6)
	html = BeautifulSoup(browser.page_source)
	browser.quit()

	div = html.find_all("div", {"id": "balance-quantity-container"})
	ada_amount = float(div[0].get_text().replace(',',''))

	if not any(d['asset'] == 'ADA' for d in total):
		total.append({'asset': 'ADA', 'amount': ada_amount})

	# Getting the coins from BNB Wallet

	bnb_api_link = "https://dex.binance.org/api/v1/account/"

	response = urlopen(bnb_api_link + bnb_address)
	data_json = (json.loads(response.read()))['balances']
	for coin in data_json:
		amount = float(coin['free'])
		ticker = coin['symbol']
		if "CBB" in ticker:
			ticker = ticker[:-4]
		if amount > 0.000001:
			if not any(d['asset'] == ticker for d in total):
				total.append({'asset': ticker, 'amount': amount})
				print(f"creating {ticker} with {amount} in total | From BNB Wallet")
			else:
				for coin in total:
					if coin['asset'] == ticker:
						coin['amount'] += amount
						print(f"adding to {ticker} {amount} in total | From BNB Wallet")
						break

	 # Getting coins from Kucoin

	client = Client(kucoin_key, kucoin_sec, kucoin_api_pass)

	kucoininfo = client.get_accounts()

	for coin in kucoininfo:
		if coin['type'] != 'trade':
			continue
		amount = float(coin['balance'])
		ticker =  coin['currency']
		if amount > 0.000001 and ticker != "USDT":
			if not any(d['asset'] == ticker for d in total):
				total.append({'asset': ticker, 'amount': amount})
				print(f"creating {ticker} with {amount} in total | From Kucoin")
			else:
				for coin in total:
					if coin['asset'] == ticker:
						coin['amount'] += amount
						print(f"adding to {ticker} {amount} in total | From Kucoin")
						break
	coinmarketcap_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
	alltickers = ""
	for coin in total:
		alltickers += (coin['asset'] + ",")
	alltickers = alltickers[:-1] 
	parameters = {
			'symbol': alltickers
			}
	headers = {
			'Accepts': 'application/json',
			'X-CMC_PRO_API_KEY': coinmarketcap_apikey,
			}

	session = Session()
	session.headers.update(headers)
	try:
		response = session.get(coinmarketcap_url, params=parameters)
		data = json.loads(response.text)
	except (ConnectionError, Timeout, TooManyRedirects) as e:
		print(e)

	for coin in total:
		ticker = coin['asset']
		coin['price'] = data['data'][ticker]['quote']['USD']['price']
		coin['value_in_USD'] = coin['price'] * coin['amount']
	total = [i for i in total if not (i['value_in_USD'] < include_with_value_higher_than)]
	total = sorted(total, key=itemgetter('value_in_USD'), reverse=True)

	balance = 0.
	for coin in total:
		balance += coin['value_in_USD']
	balance = round(balance, 2)
	reply_msg = "*Total balance is " + str(balance) + " $*" +"\n\n"
	for coin in total:
		reply_msg += coin['asset'] + ": " +str(round(coin['amount'],3)) + " | " + str(round(coin['value_in_USD'],2))+" $\n" 
	bot.reply_to(message, reply_msg, parse_mode= 'Markdown')

bot.polling(none_stop=True)
