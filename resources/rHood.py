from Robinhood import Robinhood
import requests
import logging


logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO)


def robinTick(trader, tick, ah = False):
    tickMetrics = {
            'LTP' : '',
            'LAP' : '',
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
            ltp = float(tickQuote['last_extended_hours_trade_price'])
            lap = float(tickQuote['ask_price'])
            c = float(tickQuote['last_trade_price'])
            if ltp > 1:
                ltp = round(ltp, 2)
                lap = round(lap, 2)
            
        else:
            ltp = float(tickQuote['last_trade_price'])
            lap = float(tickQuote['ask_price'])
            c = float(tickQuote['previous_close'])
            if ltp > 1:
                ltp = round(ltp, 2)
                lap = round(lap, 2)
            

        c = round(ltp - c, 2)
        cp = round((c / ltp) * 100, 2) 

        tickMetrics.update({
            'LTP' : ltp,
            'LAP' : lap,
            'C' : c,
            'CP' : cp,
            'TH' : round(float(tickFund['high']), 2),
            'TL' : round(float(tickFund['low']), 2),
            'YH' : round(float(tickFund['high_52_weeks']), 2),
            'YL' : round(float(tickFund['low_52_weeks']), 2),
            'V' : int(float(tickFund['volume'])),
            'D' : 'G' if c > 0 else 'R'
        })

    except TypeError:
        logging.info('~~~~ {} Does Not Seem to Have Data, Dropping ~~~~'.format(tick))
    except requests.exceptions.ConnectionError:
        logging.info('~~~~ Robinhood Connection Error ~~~~')

    return tickMetrics


def robinTicks(trader, ticks, ah = False):
    tickList = []
    try:
        ticksQuote = trader.quotes_data(ticks)
        for tick in ticksQuote:
            sym = tick['symbol']
            tickMetrics = {
                    'LTP' : '',
                    'LAP' : '',
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
            tickList.append({'Sym' : sym, 'Data' : tickMetrics})

            tickFund = trader.fundamentals(stock = sym)
            inst = tick['instrument'].split('/')[-2]
            if ah:
                ltp = float(tick['last_extended_hours_trade_price'])
                lap = float(tick['ask_price'])
                c = float(tick['last_trade_price'])
                if ltp > 1:
                    ltp = round(ltp, 2)
                    lap = round(lap, 2)
                
            else:
                ltp = float(tick['last_trade_price'])
                lap = float(tick['ask_price'])
                c = float(tick['previous_close'])
                if ltp > 1:
                    ltp = round(ltp, 2)
                    lap = round(lap, 2)
                

            c = round(ltp - c, 2)
            cp = round((c / ltp) * 100, 2) 

            tickList[-1]['Data'].update({
                'LTP' : ltp,
                'LAP' : lap,
                'C' : c,
                'CP' : cp,
                'TH' : round(float(tickFund['high']), 2),
                'TL' : round(float(tickFund['low']), 2),
                'YH' : round(float(tickFund['high_52_weeks']), 2),
                'YL' : round(float(tickFund['low_52_weeks']), 2),
                'V' : int(float(tickFund['volume'])),
                'D' : 'G' if c > 0 else 'R'
            })

    except TypeError:
        logging.info('~~~~ An Invalid Tick Seems to Exist ~~~~')
    except requests.exceptions.ConnectionError:
        logging.info('~~~~ Robinhood Connection Error ~~~~')

    return tickList