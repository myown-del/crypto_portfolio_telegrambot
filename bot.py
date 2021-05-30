import telebot
import binance
from kucoin.client import Client
import asyncio
from urllib.request import urlopen
import json
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from operator import itemgetter
from telebot import types
import re
import configparser

# * initial config
config = configparser.ConfigParser()
config.read('config.ini')

bot_token = config['DEFAULT']['bot_token']

# in USD
include_with_value_higher_than = 3

bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['start'])
def handleStart(message):
    bot.send_message(message.chat.id, "Welcome to crypto portfolio bot. Made by @billyel\nSet your account in settings.")
    mainMenu(message)
    
    
def mainMenu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = list()
    buttons.append(types.KeyboardButton('Check portfolio'))
    buttons.append(types.KeyboardButton('Settings'))
    markup.row(buttons[0], buttons[1])
    bot.send_message(message.chat.id, "View your portfolio or change settings.",reply_markup=markup)
    bot.register_next_step_handler(message, handleMainMenu)


def handleMainMenu(message):
    if message.text == 'Check portfolio':
        startParsing(message)
        mainMenu(message)
    elif message.text == 'Settings':
        settings(message)
    else:
        mainMenu(message)
        

def settings(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = list()
    buttons.append(types.KeyboardButton('Set BNB address'))
    buttons.append(types.KeyboardButton('Set ADA address'))
    buttons.append(types.KeyboardButton('Setup Binance'))
    buttons.append(types.KeyboardButton('Setup Kucoin'))
    buttons.append(types.KeyboardButton('Set Coinmarketcap API key'))
    buttons.append(types.KeyboardButton('Set Blockfrost API key'))
    buttons.append(types.KeyboardButton('Cancel'))
    buttons.append(types.KeyboardButton('View saved settings'))
    markup.row(buttons[7])
    markup.row(buttons[0], buttons[1])
    markup.row(buttons[2], buttons[3])
    markup.row(buttons[4], buttons[5])
    markup.row(buttons[6])
    bot.send_message(message.chat.id, "Which one to change?",
                     reply_markup=markup)
    bot.register_next_step_handler(message, handleSettingsUpdate)


def handleSettingsUpdate(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    try:
        if message.text == 'Set BNB address':
            bot.send_message(
                message.chat.id, "Send the bnb address: ", reply_markup=markup)
            bot.register_next_step_handler(message, setaddress, "bnb")
        elif message.text == 'Set ADA address':
            bot.send_message(
                message.chat.id, "Send the ada address: ", reply_markup=markup)
            bot.register_next_step_handler(message, setaddress, "ada")
        elif message.text == 'Setup Binance':
            bot.send_message(
                message.chat.id, "Enter your API key: ", reply_markup=markup)
            bot.register_next_step_handler(message, setupBinanceapikey)
        elif message.text == 'Setup Kucoin':
            bot.send_message(
                message.chat.id, "Enter your API key: ", reply_markup=markup)
            bot.register_next_step_handler(message, setupKucoinapikey)
        elif message.text == 'Set Coinmarketcap API-key':
            bot.send_message(
                message.chat.id, "Send Coinmarketcap API key: ", reply_markup=markup)
            bot.register_next_step_handler(message, setupCoinmarketcapapi)
        elif message.text == 'Set Blockfrost API key':
            bot.send_message(
                message.chat.id, "Send Blockfrost API key: ", reply_markup=markup)
            bot.register_next_step_handler(message, setupBlockfrostapi)    
        elif message.text == 'Cancel':
            mainMenu(message)
        elif message.text == 'View saved settings':
            config.read('config.ini')
            binance_key = config['Binance']['binance_key']
            binance_sec = config['Binance']['binance_sec']
            kucoin_key = config['Kucoin']['kucoin_key']
            kucoin_sec = config['Kucoin']['kucoin_sec']
            kucoin_api_pass = config['Kucoin']['kucoin_api_pass']
            coinmarketcap_apikey = config['API']['coinmarketcap_apikey']
            blockfrost_apikey = config['API']['blockfrost_apikey']
            ada_address = config['Addresses']['ada_address']
            bnb_address = config['Addresses']['bnb_address']
            reply_msg = "*Binance*\nAPI key: " + binance_key + "\nAPI secret: " + binance_sec +"\n" + \
                "*Kucoin*\nAPI key: " + kucoin_key + "\nAPI secret: " + kucoin_sec +"\n" + "API password: " + kucoin_api_pass + "\n" +\
                "*API's*\nCoinmarketcap: " + coinmarketcap_apikey + "\nBlockfrost: " + blockfrost_apikey +"\n" + \
                "*Addresses*\n" + "ADA: " + ada_address + "\n" + "BNB: "+ bnb_address
            bot.send_message(
                message.chat.id, reply_msg, parse_mode='Markdown')
            settings(message) 
        else:
            settings(message)
    except:
        bot.send_message(message.chat.id, "Error occured.", reply_markup=markup)
        settings(message)

def setaddress(message, coin):
    address = message.text.lower()
    if coin == "bnb":
        if re.match(r"bnb[0-9a-zA-Z]{39}", address):
            bnb_address = address
            config['Addresses']['bnb_address'] = address
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            bot.send_message(message.chat.id, "Done. Your BNB address has been set to *" +
							address+"*.", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "Wrong BNB address.")
            settings(message)
            
    elif coin == "ada":
        if re.match(r"addr[0-9a-zA-Z]{99}", address):
            config['Addresses']['ada_address'] = address
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            bot.send_message(message.chat.id, "Done. Your ADA address has been set to *" +
							address+"*.", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "Wrong ADA address.")
            settings(message)
            
def setupBinanceapikey(message):
    config['Binance']['binance_key'] = message.text
    with open('config.ini', 'w') as configfile:
                config.write(configfile)
    finalmsg = "*Binance*\n" + "API key: " + message.text + "\n"
    bot.send_message(message.chat.id, "Enter Binance secret key: ")
    bot.register_next_step_handler(message, setupBinanceseckey, finalmsg)

def setupBinanceseckey(message, finalmsg):
    config['Binance']['binance_sec'] = message.text
    with open('config.ini', 'w') as configfile:
                config.write(configfile)
    finalmsg += "Secret key: " + message.text
    bot.send_message(message.chat.id, finalmsg, parse_mode='Markdown')
    settings(message)

def setupKucoinapikey(message):
    config['Kucoin']['kucoin_key'] = message.text
    with open('config.ini', 'w') as configfile:
                config.write(configfile)
    finalmsg = "*Kucoin*\n" + "API key: " + message.text + "\n"
    bot.send_message(message.chat.id, "Enter Kucoin secret key: ")
    bot.register_next_step_handler(message, setupKucoinseckey, finalmsg)

def setupKucoinseckey(message, finalmsg):
    config['Kucoin']['kucoin_sec'] = message.text
    with open('config.ini', 'w') as configfile:
                config.write(configfile)
    finalmsg += "Secret key: " + message.text + '\n'
    bot.send_message(message.chat.id, "Enter Kucoin API password: ")
    bot.register_next_step_handler(message, setupKucoinapipass, finalmsg)
    
def setupKucoinapipass(message, finalmsg):
    config['Kucoin']['kucoin_api_pass'] = message.text
    with open('config.ini', 'w') as configfile:
                config.write(configfile)
    finalmsg += "API password: " + message.text
    bot.send_message(message.chat.id, finalmsg, parse_mode='Markdown')
    settings(message)

def setupCoinmarketcapapi(message):
    config['API']['coinmarketcap_apikey'] = message.text
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    finalmsg = "*Coinmarketcap*\n" + "API key: " + message.text
    bot.send_message(message.chat.id, finalmsg, parse_mode='Markdown')
    settings(message)

def setupBlockfrostapi(message):
    config['API']['blockfrost_apikey'] = message.text
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    finalmsg = "*Blockfrost*\n" + "API key: " + message.text
    bot.send_message(message.chat.id, finalmsg, parse_mode='Markdown')
    settings(message)

def startParsing(message):
    asyncio.run(parser(message))

async def parser(message):
    config.read('config.ini')
    binance_key = config['Binance']['binance_key']
    binance_sec = config['Binance']['binance_sec']
    kucoin_key = config['Kucoin']['kucoin_key']
    kucoin_sec = config['Kucoin']['kucoin_sec']
    kucoin_api_pass = config['Kucoin']['kucoin_api_pass']
    coinmarketcap_apikey = config['API']['coinmarketcap_apikey']
    blockfrost_apikey = config['API']['blockfrost_apikey']
    ada_address = config['Addresses']['ada_address']
    bnb_address = config['Addresses']['bnb_address']
    total = []
    USDT = 0.
    RUB = 0.
    # * Getting coins info from Binance
    try:
        client = binance.Client(binance_key, binance_sec)
        await client.load()
        accinfo = await client.fetch_account_information(receive_window=None)
        for coin in accinfo['balances']:
            if coin['asset'] == "USDT":
                USDT += float(coin['free'])
            elif coin['asset'] == "RUB":
                RUB += float(coin['free'])
            else:
                amount = float(coin['free'])
                ticker = coin['asset'] + "USDT"
                if amount > 0.000001:
                    print(ticker[:-4] + f" amount: {amount}")
                    coin.pop('locked')
                    coin['amount'] = float(coin.pop('free'))
                    total.append(coin)
        await client.close()
    except:
        print("Wrong Binance credentials.")
        bot.send_message(message.chat.id, "You entered wrong Binance credentials.")
    
    # * Getting the amount of ADA on Yoroi
    link_cardano = "https://cardano-mainnet.blockfrost.io/api/v0/addresses/"
    headers = {
		'project_id': blockfrost_apikey
	}

    session = Session()
    session.headers.update(headers)
    try:
        response = session.get(link_cardano + ada_address)
        data = json.loads(response.text)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    try:
        ada_amount = float(data['amount'][0]['quantity'])
    except:
        ada_amount = 0
        bot.send_message(message.chat.id, "You entered wrong ADA address or Blockfrost API key.")
    if ada_amount > 1e+6:
        ada_amount /= 1e+6
    print(f"Found {ada_amount} ADA in Cardano Wallet")

    if not any(d['asset'] == 'ADA' for d in total):
        total.append({'asset': 'ADA', 'amount': ada_amount})
    else:
        for x in total:
            if x['asset'] == 'ADA':
                x['amount'] += ada_amount

    # * Getting the coins from BNB Wallet

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
                print(
                    f"creating {ticker} with {amount} in total | From BNB Wallet")
            else:
                for coin in total:
                    if coin['asset'] == ticker:
                        coin['amount'] += amount
                        print(
                            f"adding to {ticker} {amount} in total | From BNB Wallet")
                        break

    # *Getting coins from Kucoin
    try:
        client = Client(kucoin_key, kucoin_sec, kucoin_api_pass)
        kucoininfo = client.get_accounts()
        for coin in kucoininfo:
            if coin['type'] != 'trade':
                continue
            amount = float(coin['balance'])
            ticker = coin['currency']
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
    except:
        print("Wrong Kucoin credentials.")
        bot.send_message(message.chat.id, "You entered wrong Kucoin credentials.")
    
    try:
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
        response = session.get(coinmarketcap_url, params=parameters)
        data = json.loads(response.text)
        print("Got prices from Coinmarketcap")
        for coin in total:
            ticker = coin['asset']
            coin['price'] = data['data'][ticker]['quote']['USD']['price']
            coin['value_in_USD'] = coin['price'] * coin['amount']
        total = [i for i in total if not (i['value_in_USD'] < include_with_value_higher_than)]
        total = sorted(total, key=itemgetter('value_in_USD'), reverse=True)
        
        balance = 0.
        for coin in total:
            balance += coin['value_in_USD']
        balance += USDT + (RUB/74)
        balance = round(balance, 2)
        reply_msg = "*Total balance is " + str(balance) + " $*" + "\n\n"
        reply_msg += "*In coins:*\n"
        for coin in total:
            if coin['amount'] >= 1:
                amount = str(round(coin['amount'], 2))
            else:
                amount = str(round(coin['amount'], 6))
            reply_msg += coin['asset'] + ": " + amount + " | " + \
                str(round(coin['value_in_USD'], 2)) + " $\n"
        reply_msg += "\n*In fiat:*\n" + str(round(USDT,2)) +" $\n"
        if RUB!=0:
            reply_msg += str(round(RUB,2)) +" ₽\n"
            
        bot.reply_to(message, reply_msg, parse_mode='Markdown')
    except:
        print("Wrong API key for Coinmarketcap")
        bot.send_message(message.chat.id, "You entered wrong Coinmarketcap API key.")

bot.polling(none_stop=True)
