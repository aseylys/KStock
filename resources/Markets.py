from bs4 import BeautifulSoup
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError
from socket import timeout
from requests.exceptions import RequestException
import requests, logging


def fetchMarkets():
    markets = {
        'S&P' : {'Change' : '', 'Quote' : '', 'D' : ''},
        'Dow' : {'Change' : '', 'Quote' : '', 'D' : ''},
        'Nasdaq' : {'Change' : '', 'Quote' : '', 'D' : ''}
    }
    url = 'http://money.cnn.com/data/us_markets/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}\

    try:
        soup = BeautifulSoup(urlopen(Request(url, headers = headers), timeout = 1).read(), 'html5lib')

        if soup:
            for market in soup.find('div', {'id' : 'wsod_tickerRoll'}).findAll('li'):
                quote = market.find('div', {'class' : 'bannerQuote'}).text.strip()
                change = market.find('span', {'class' : 'quoteChange'}).text
                markets[market.find('a').text] = {
                    'Change' : change,
                    'Quote' : quote,
                    'D' : 'G' if '+' in change else 'R'
                }

    except (URLError, timeout, ConnectionResetError):
        logging.info('Market Fetch Timeout')

    return markets


if __name__ == '__main__':
    fetchMarkets()