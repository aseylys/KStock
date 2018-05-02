import requests, time, json, demjson
from datetime import datetime
import pandas as pd
from urllib.request import Request, urlopen
from html.parser import unescape


def get_price_data(query):
    r = requests.get("https://finance.google.com/finance/getprices", params=query)
    lines = r.text.splitlines()
    data = []
    index = []
    basetime = 0
    for price in lines:
        cols = price.split(",")
        if cols[0][0] == 'a':
            basetime = int(cols[0][1:])
            index.append(datetime.fromtimestamp(basetime))
            data.append([float(cols[4]), float(cols[2]), float(cols[3]), float(cols[1]), int(cols[5])])
        elif cols[0][0].isdigit():
            date = basetime + (int(cols[0])*int(query['i']))
            index.append(datetime.fromtimestamp(date))
            data.append([float(cols[4]), float(cols[2]), float(cols[3]), float(cols[1]), int(cols[5])])
    return pd.DataFrame(data, index = index, columns = ['Open', 'High', 'Low', 'Close', 'Volume'])


def buildNewsUrl(symbol, qs='&start=0&num=5'):
   return 'http://www.google.com/finance/company_news?output=json&q=' \
        + symbol + qs
 

def request(symbols):
    url = buildUrl(symbols)
    req = Request(url)
    resp = urlopen(req)
    # remove special symbols such as the pound symbol
    content = resp.read().decode('ascii', 'ignore').strip()
    content = content[3:]
    return content
 
 
def getNews(symbol):
    url = buildNewsUrl(symbol)
 
    content = urlopen(url).read().decode('utf-8')
 
    content_json = demjson.decode(content)
 
    article_json = []
    news_json = content_json['clusters']
    for cluster in news_json:
        for article in cluster:
            if article == 'a':
                article_json.extend(cluster[article])
 
    return [[unescape(art['t']).strip(), art['u']] for art in article_json]
