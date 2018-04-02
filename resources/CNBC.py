from bs4 import BeautifulSoup
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import urllib.error as ue
from functools import wraps
from requests.exceptions import RequestException
import requests


def fetchStock(tick, ah = False):
    url = 'https://www.cnbc.com/quotes/?symbol={}'.format(tick)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}\

    tickMetrics = {
            'LTP' : '',
            'C' : '',
            'CP' : '',
            'PC' : '',
            'TH' : '',
            'TL' : '',
            'YH' : '',
            'YL' : '',
            'V' : '',
            'D' : ''
        }
    soup = BeautifulSoup(urlopen(Request(url, headers = headers), timeout = 1).read(), 'html5lib')

    if soup:
        table = soup.find('table', {'class' : 'quote-horizontal regular'})
        if ah:
            for content in table.findAll('tr', {'class' : 'extend'})[1].findAll('div'):
                print(content)
                


if __name__ == '__main__':
    fetchStock('AAPL', ah = True)