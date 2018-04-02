from Robinhood import Robinhood
import requests
import logging

logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO)

def rCall(trader, tick, ah = False):
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
        tickQuote = trader.quote_data(stock = tick)
        tickFund = trader.fundamentals(stock = tick)
        inst = tickQuote['instrument'].split('/')[-2]
        if ah:
            ltp = round(float(tickQuote['last_extended_hours_trade_price']), 2)
            c = round(ltp - float(tickQuote['last_trade_price']), 2)
            
        else:
            ltp = round(float(tickQuote['last_trade_price']), 2)
            c = round(ltp - float(tickQuote['previous_close']), 2)

        cp = round((c / ltp) * 100, 2) 

        tickMetrics.update({
            'LTP' : ltp,
            'C' : c,
            'CP' : cp,
            'TH' : round(float(tickFund['high']), 2),
            'TL' : round(float(tickFund['low']), 2),
            'YH' : round(float(tickFund['high_52_weeks']), 2),
            'YL' : round(float(tickFund['low_52_weeks']), 2),
            'V' : int(float(tickFund['volume'])),
            'D' : 'G' if c > 0 else 'R'
        })

        
    except requests.exceptions.ConnectionError:
        logging.info('~~~~ Robinhood Connection Error ~~~~')

    return tickMetrics
