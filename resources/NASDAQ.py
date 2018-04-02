from bs4 import BeautifulSoup
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import urllib.error as ue
from functools import wraps
from requests.exceptions import RequestException
import requests
import re
import socket

if __name__ == '__main__':
    import logging
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO)


class Retry(object):
    """Decorator that retries a function call a number of times, optionally
    with particular exceptions triggering a retry, whereas unlisted exceptions
    are raised.
    :param pause: Number of seconds to pause before retrying
    :param retreat: Factor by which to extend pause time each retry
    :param max_pause: Maximum time to pause before retry. Overrides pause times
                      calculated by retreat.
    :param cleanup: Function to run if all retries fail. Takes the same
                    arguments as the decorated function.
    """
    def __init__(self, times, exceptions = (IndexError), pause = 1, retreat = 1,
                 max_pause = None, cleanup = None):
        """Initiliase all input params"""
        self.times = times
        self.exceptions = exceptions
        self.pause = pause
        self.retreat = retreat
        self.max_pause = max_pause or (pause * retreat ** times)
        self.cleanup = cleanup

    def __call__(self, f):
        """
        A decorator function to retry a function (ie API call, web query) a
        number of times, with optional exceptions under which to retry.

        Returns results of a cleanup function if all retries fail.
        :return: decorator function.
        """
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            for i in range(self.times):
                # Exponential backoff if required and limit to a max pause time
                pause = min(self.pause * self.retreat ** i, self.max_pause)
                try:
                    return f(*args, **kwargs)
                except self.exceptions:
                    if self.pause is not None:
                        time.sleep(pause)
                    else:
                        pass
            if self.cleanup is not None:
                return self.cleanup(*args, **kwargs)
        return wrapped_f

def failed(*args, **kwargs):
    print('Failed Call: ' + str(args) + str(kwargs))

    raise RequestException

def clean(s):
    s = re.sub(r'[^0-9a-zA-Z. ]', '', s)
    return s



def tickCurrents(tick):
    url = 'https://www.nasdaq.com/symbol/{}/real-time'.format(tick)
    values = {
        'name' : 'KAY',
        'location' : 'San Antonio',
        'language' : 'Python' 
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

    data = urlencode(values)
    data = data.encode('ascii')
    req = Request(url, data = data, headers = headers)
    
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

    try:

        soup = BeautifulSoup(urlopen(req, timeout = 1).read(), 'html5lib')

        _tag2met = {
            'quotes_content_left__LastSale': 'LTP', 
            'quotes_content_left__NetChange': 'C', 
            '_updownImage': 'D', 
            'quotes_content_left__PctChange': 'CP', 
            'quotes_content_left__Volume': 'V', 
            'quotes_content_left__PreviousClose': 'PC', 
            'quotes_content_left__TodaysHigh': 'TH', 
            'quotes_content_left__TodaysLow': 'TL', 
            'quotes_content_left__52WeekHigh': 'YH', 
            'quotes_content_left__52WeekLow': 'YL'
        }

        if soup:
            for content in soup.find('div', {'class' : 'genTable'}).findAll('span'):
                if content.has_attr('id'):
                    tagId = content.get('id')
                    if tagId in _tag2met:
                        if tagId == '_updownImage':
                            tickMetrics['D'] = content.get('class')[0]
                        else:
                            tickMetrics[_tag2met[tagId]] = clean(content.text.encode('ascii', 'ignore').decode())

    except (ue.HTTPError, ue.URLError) as error:
        logging.info('Data of %s not retrieved because %s\nURL: %s', name, error, url)

    except socket.timeout:
        logging.info('Socket timed out - URL %s', url)
    
    finally:
        for item in tickMetrics:
            try:
                tickMetrics[item] = round(float(tickMetrics[item]), 2)
            except ValueError:
                pass
        return tickMetrics if tickMetrics['LTP'] else False
    

def tickRating(self):
    rating = {'r' : None, 'c' : None}
    rate = soup.find('a', {'id' : 'quotes_content_left_OverallStockRating1_hlIconLink'}).find('img')
    ratings = soup.find('div', {'id' : 'ratingtext'}).findAll('span')
    if 'bullish' in rate.get('src'): rating['r'] = 1
    elif 'bearing' in rate.get('src'): rating['r'] = -1
    rating['c'] = ' '.join(span.text for span in ratings)
    return rating


if __name__ == '__main__':
    
    print(tickCurrents('aapl'))