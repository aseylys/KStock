# coding: utf-8
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


def get_closing_data(queries, period):
    closing_data = []
    for query in queries:
        query['i'] = 86400
        query['p'] = period
        r = requests.get("https://www.google.com/finance/getprices", params=query)
        lines = r.text.splitlines()
        data = []
        index = []
        basetime = 0
        for price in lines:
            cols = price.split(",")
            if cols[0][0] == 'a':
                basetime = int(cols[0][1:])
                date = basetime
                data.append(float(cols[1]))
                index.append(datetime.fromtimestamp(date).date())
            elif cols[0][0].isdigit():
                date = basetime + (int(cols[0])*int(query['i']))
                data.append(float(cols[1]))
                index.append(datetime.fromtimestamp(date).date())
        s = pd.Series(data,index=index,name=query['q'])
        closing_data.append(s[~s.index.duplicated(keep='last')])
    return pd.concat(closing_data, axis=1)

def get_open_close_data(queries, period):
    open_close_data = pd.DataFrame()
    for query in queries:
        query['i'] = 86400
        query['p'] = period
        r = requests.get("https://www.google.com/finance/getprices", params=query)
        lines = r.text.splitlines()
        data = []
        index = []
        basetime = 0
        for price in lines:
            cols = price.split(",")
            if cols[0][0] == 'a':
                basetime = int(cols[0][1:])
                date = basetime
                data.append([float(cols[4]), float(cols[1])])
                index.append(datetime.fromtimestamp(date).date())
            elif cols[0][0].isdigit():
                date = basetime + (int(cols[0])*int(query['i']))
                data.append([float(cols[4]), float(cols[1])])
                index.append(datetime.fromtimestamp(date).date())
        df = pd.DataFrame(data, index=index, columns=[query['q']+'_Open',query['q']+'_Close'])
        open_close_data = pd.concat([open_close_data, df[~df.index.duplicated(keep='last')]], axis=1)
    return open_close_data

def get_prices_data(queries):
    prices_data = pd.DataFrame()
    for query in queries:
        r = requests.get("https://www.google.com/finance/getprices", params=query)
        lines = r.text.splitlines()
        data = []
        index = []
        basetime = 0
        for price in lines:
            cols = price.split(",")
            if cols[0][0] == 'a':
                basetime = int(cols[0][1:])
                date = basetime
                data.append([float(cols[4]), float(cols[2]), float(cols[3]), float(cols[1]), int(cols[5])])
                index.append(datetime.fromtimestamp(date).date())
            elif cols[0][0].isdigit():
                date = basetime + (int(cols[0])*int(query['i']))
                data.append([float(cols[4]), float(cols[2]), float(cols[3]), float(cols[1]), int(cols[5])])
                index.append(datetime.fromtimestamp(date).date())
        df = pd.DataFrame(data, index=index, columns=[query['q']+'_Open',query['q']+'_High',query['q']+'_Low',query['q']+'_Close',query['q']+'_Volume'])
        prices_data = pd.concat([prices_data, df[~df.index.duplicated(keep='last')]], axis=1)
    return prices_data

def get_prices_time_data(queries, period, interval):
    prices_time_data = pd.DataFrame()
    for query in queries:
        query['i'] = interval
        query['p'] = period
        r = requests.get("https://www.google.com/finance/getprices", params=query)
        lines = r.text.splitlines()
        data = []
        index = []
        basetime = 0
        for price in lines:
            cols = price.split(",")
            if cols[0][0] == 'a':
                basetime = int(cols[0][1:])
                date = basetime
                data.append([float(cols[4]), float(cols[2]), float(cols[3]), float(cols[1]), int(cols[5])])
                index.append(datetime.fromtimestamp(date))
            elif cols[0][0].isdigit():
                date = basetime + (int(cols[0])*int(query['i']))
                data.append([float(cols[4]), float(cols[2]), float(cols[3]), float(cols[1]), int(cols[5])])
                index.append(datetime.fromtimestamp(date))
        df = pd.DataFrame(data, index=index, columns=[query['q']+'_Open',query['q']+'_High',query['q']+'_Low',query['q']+'_Close',query['q']+'_Volume'])
        prices_time_data = pd.concat([prices_time_data, df[~df.index.duplicated(keep='last')]], axis=1)
    return prices_time_data


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
if __name__ == '__main__':
    # Dow Jones
    param = {
        'q': ".DJI",
        'i': "86400",
        'x': "INDEXDJX",
        'p': "1Y"
    }
    df = get_price_data(param)
    print(df.iloc[-1]['Close'])
