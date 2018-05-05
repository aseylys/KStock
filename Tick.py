import resources.gfc as gfc
from collections import deque
import pandas as pd
from numpy import NaN, Inf, arange, isscalar, asarray, array, mean, diff, polyfit
import logging, datetime, pytz

def zigzag(data, delta):
    '''
    Calculates the peaks and valleys, in relation to the data it's 
    corresponding delta

    Args:
        data (list): list of y values that it's searching through
        delta (float): value that the change needs to be greater than

    Returns:
        peaks (list): list of tuples with peak points (xPeak, yPeak)
        valls (list): list of tuples with valley points (xValley, yValley)
    '''
    xRange = arange(len(data))
    peaks, valls = [], []
    minVal, maxVal = Inf, -Inf
    minPos, maxPos = NaN, NaN

    maxFlip = True
    for i in xRange:
        val = data[i]
        if val > maxVal:
            maxVal = val
            maxPos = xRange[i]
        if val < minVal:
            minVal = val
            minPos = xRange[i]

        if maxFlip:
            if val < maxVal - delta:
                peaks.append((maxPos, maxVal))
                minVal = val
                minPos = xRange[i]
                maxFlip = False
        else:
            if val > minVal + delta:
                valls.append((minPos, minVal))
                maxVal = val
                maxPos = xRange[i]
                maxFlip = True

    return peaks, valls 
 

class Tick():
    def __init__(self, tick = '', purPrice = 0, trader = '', spy = '', ah = False):
        self.__dict__.update({
            'T' : tick,                     #Ticker Symbol
            'C' : '',                       #Current Price
            'A' : '',                       #Last Ask Price
            'CP' : [],                      #Price Change [$,%]
            'V' : '',                       #Volume
            'AV' : '',                      #Average Volume
            'D' : '',                       #Direction of change
            'PQ' : 0,                       #Proposed quantity
            'PC' : '',                      #Previous Close
            'TD' : [],                      #Todays Data [Low, High]
            'YD' : [],                      #Years Data [Low, High]
            'Q' : None,                     #Quantity, once purchased
            'AP' : None,                    #Average Price, once purchased
            'SL' : None,                    #Stop Loss, once purchased
            'SPY' : spy,                    #Tracks the SPY ETF for algo
            'PV' : [[], []]                 #The peaks and valleys of the stack [[P], [V]]
        })

        #Whether this will be trade
        self.tradeable = True
        #transID ID (side, ID)
        self.transID = None
        #A stack of last 10 closing prices, used to determine Sell/Buy
        self.stack = []
        #Previous profit
        self.prevProfit = 0
        #Revert tuple incase of failure to purchase, resets Tick
        self._revert = ()
        #Robinhood trader object
        self.trader = trader
        #self.update(purPrice, spy, ah)
        self.buyRev, self.sellRev = 0, 0


    def update(self, data, purPrice, spy):
        '''
        Updates the ticker to its current values

        Args:
            data (dict): current tick information
            purPrice (float): amount allocated to purchase stock at
            spy (str): current s&p value (R/G)

        Returns:
            (bool): whether the fetch to nasdaq was successful
        '''
        if len(self.stack) == 0 and self.tradeable:
            prevData = gfc.get_price_data({'q': self.T, 'i': '60', 'p': '1d'})
            self.stack = [(idx.time(), row['Close']) for idx, row in prevData.iterrows()]

        if data and type(data['LTP']) == float:
            curPrice = data['LTP']
            self.stack.append((datetime.datetime.now().time(), curPrice))
            
            #List of peaks and valleys to be updated to __dict__
            ps_vs = [[], []]

            if curPrice > 1:
                #If a full stack, perform analysis
                if len(self.stack) >= 5:
                    prices = [i[1] for i in self.stack]
                    delta = mean(prices) * 0.01
                    ps_vs = list(zigzag(prices, delta))


            self.__dict__.update({
                'C' : data['LTP'],
                'A' : data['LAP'],
                'CP' : (data['C'], data['CP']),
                'V' : data['V'],
                'PC' : data['PC'],
                'TD' : [data['TL'], data['TH']],
                'YD' : [data['YL'], data['YH']],
                'D' : data['D'],
                'PQ' : int(purPrice / data['LTP']),
                'SPY' : spy,
                'PV' : ps_vs
            })

            return True
        else: return False


    def close(self):
        '''
        Actually sells the ticker by setting the pos variables accordingly

        Args:
            None

        Returns:
            None
        ''' 
        self._revert = {
            'Q' : self.Q, 
            'AP' : self.AP, 
            'SL' : self.SL,
            'Buy' : self.buyRev,
            'transID' : self.transID
        }
        self.prevProfit = (self.Q * self.C) - (self.Q * self.AP)
        self.Q, self.AP, self.SL, self.transID = None, None, None, None        


    def toSell(self, purPrice, spy):
        '''
        Determines whether to sell the ticker based on the current strategy

        Args:
            purpirce (float): tick current data
            spy (str): current s&p value (R/G)
            forced (bool): whether it's being forced to be sold

        Returns:
            (bool): determination of whether to sell or not
        '''

        #If short trading or price swing trading, the logic will be the same
        #Waits for price reversal then sell if the price reversal
        #Continues for 2 unique updates
        if self.Q:
            #If it falls below the limit loss, force sell it
            if self.C <= self.SL:
                logging.info('{} Hit Stop Loss at {}'.format(self.T, self.C))
                return True

            #Conservative with Red days and non-penny stocks
            if self.SPY == 'R':
                if self.C > self.AP and self.C > 1:
                    logging.info('{} Reached SPY R Sell Criteria At {}'.format(self.T, self.C))
                    return True

            #We're real conservative with penny stocks, if the price is above the purchase price
            #and the profit will be > $1, we immediately sell
            if self.C < 2:
                if self.C > self.AP and ((self.Q * self.C) - (self.Q * self.AP) > 1):
                    logging.info('{} Reached Penny Stock Sell Criteria At {}'.format(self.T, self.C))
                    return True
            else:
                if self.C > self.AP:
                    if len(self.PV[0]) > 0:
                        #If the peak has an idex of >5, the peak occured w/in the last 15 seconds
                        #so therefore it'd be good to sell
                        if self.PV[0][-1][0] > len(self.stack) - 5:
                            return True

        return False


    def _open(self, rhood):
        '''
        Actually purchases the ticker by setting the pos variables accordingly

        Args:
            rhood (bool/tuple): if there is info to auto populate if forced to purchase

        Returns:
            None
        ''' 
        self._revert = {
            'Q' : self.Q, 
            'AP' : self.AP, 
            'SL' : self.SL,
            'Buy' : self.buyRev,
            'transID' : self.transID
        }

        if not rhood:
            if self.C > 1:
                sellLimit = round(self.C - (self.C * 0.05), 2)
                #Redundancy, some penny stocks seem to slip through this crack and I have
                #no idea why
                if sellLimit < 1: sellLimit = 0
            else:
                sellLimit = 0

            self.Q, self.AP, self.SL = self.PQ, self.C, sellLimit
        else:
            self.Q, self.AP, self.SL = rhood
        
        self.transID = None
        self.buyRev = 0


    def toBuy(self, purPrice, spy, forced = False, rhood = False):
        '''
        Determines whether to purchase the ticker based on the current strategy

        Args:
            purPrice (float): tick current data
            spy (str): current s&p value (R/G)
            forced (bool): whether it's being forced to be purchased
            rhood (bool/tuple): if there is info to auto populate if forced to purchase

        Returns:
            (bool): determination of whether to buy or not
        '''
        if forced:
            logging.info('{} Forced Purchase at {}'.format(self.T, self.C))
            self._open(rhood)
            return True

        #We don't want a penny stock with a wide (relatively) spread
        if self.C < 1:
            if (self.A - self.C) > 0.1:
                return False

        #If there's ample data, fit that shit, we're looking for positive upward trends.
        #We don't want to go down with the ship
        if len(self.stack) > 100:
            prices = [i[1] for i in self.stack]
            fit = polyfit(range(len(prices)), prices, 1)[0]
            if fit < -1: 
                return False

        if self.C > 1:
            if len(self.PV[1]) > 0:
                #If the peak has an index which occured w/in the last 15 (5 * 3) seconds
                #so therefore it'd be good to sell
                if self.PV[1][-1][0] > (len(self.stack) - 1) - 5:
                    self._open(rhood)
                    return True
        else:
            #If the last price is less than the price before
            if self.stack[-1][1] < self.stack[-2][1]:
                self.buyRev = 0
            #Elif the last price is greater than the price before
            elif self.stack[-1][1] > self.stack[-2][1]:
                self.buyRev += 1
            else:
                pass

            if self.buyRev == 3:
                self._open(rhood)
                return True
             

    def revert(self):
        '''
        Reverts the ticker back to state before transID if there was an error

        Args:
            None

        Returns:
            None
        '''
        self.__dict__.update(self._revert)

