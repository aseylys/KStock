import resources.gfc as gfc
from resources.rHood import rCall
import pandas as pd
import logging, datetime, pytz


class Tick():
    def __init__(self, tick, purPrice, trader, ah = False):
        self.__dict__.update({
            'T' : tick,                     #Ticker Symbol
            'C' : '',                       #Current Price
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
            'tradeable' : True              #Whether we're going to day-trade
        })

        #Price Reversal Sell Counter
        self.sellRev = 0
        #Price Reversale Buy Counter
        self.buyRev = 0
        self.pPrice = 0
        self.prevProfit = 0
        self._revert = ()
        self.trader = trader
        self.update(purPrice, ah)


    def update(self, purPrice, ah = False):
        '''
        Updates the ticker to its current values

        Args:
            purPrice (float): amount allocated to purchase stock at
            ah (bool): whether after hours or not

        Returns:
            (bool): whether the fetch to nasdaq was successful
        '''
        data = rCall(self.trader, self.T, ah)
        if data and type(data['LTP']) == float:
            self.__dict__.update({
                'C' : data['LTP'],
                'CP' : (data['C'], data['CP']),
                'V' : data['V'],
                'PC' : data['PC'],
                'TD' : [data['TL'], data['TH']],
                'YD' : [data['YL'], data['YH']],
                'D' : data['D'],
                'PQ' : int(purPrice / data['LTP'])
            })

            return True
        else: return False



    def close(self):
        '''
        Actually sells the ticker by setting the pos variables accordingly
        Args:
            None

        Returns:
            bool: whether it was successful
        ''' 
        self.prevProfit = (self.Q * self.C) - (self.Q * self.AP)
        self.Q, self.AP, self.SL = None, None, None
        self._revert = {
            'Q' : self.Q, 
            'AP' : self.AP, 
            'SL' : self.SL, 
            'Buy' : self.buyRev,
            'Sell' : self.sellRev
        }
        self.sellRev = 0


    def toSell(self, purPrice, tradeStrat, forced = False, ah = False):
        '''
        Determines whether to sell the ticker based on the current strategy

        Args:
            purpirce (float): tick current data
            tradeStrat (str): current trade strategy
            ah (bool): whether after hours or not
            forced (bool): whether it's being forced to be sold

        Returns:
            (bool): determination of whether to sell or not
        '''
        if not self.update(purPrice):
            logging.info('{} Fetch Empty'.format(self.T))
            return False

        #If short trading or price swing trading, the logic will be the same
        #Waits for price reversal then sell if the price reversal
        #Continues for 2 unique updates
        if self.Q:
            #If it falls below the limit loss, force sell it
            if (self.C <= self.SL) or forced:
                logging.info('{} Forced Sell At {}'.format(self.T, self.C))
                return True

            else:
                if self.C > self.AP:
                    if self.C < self.pPrice:
                        self.sellRev += 1
                    elif self.C > self.pPrice:
                        self.pPrice = self.C
                        self.sellRev = 0
                    else:
                        pass

                if self.sellRev == 3:
                    logging.info('{} Reached Sell Criteria At {}'.format(self.T, self.C))
                    return True

        return False


    def _open(self, rhood):
        '''
        Actually purchases the ticker by setting the pos variables accordingly
        Args:
            rhood (bool/tuple): if there is info to auto populate if forced to purchase

        Returns:
            bool: whether it was successful
        ''' 

        if not rhood:
            self.Q, self.AP, self.SL = self.PQ, self.C, round(self.C - (self.C * 0.025), 2)
        else:
            self.Q, self.AP, self.SL = rhood
        self._revert = {
            'Q' : self.Q, 
            'AP' : self.AP, 
            'SL' : self.SL, 
            'Buy' : self.buyRev,
            'Sell' : self.sellRev
        }
        self.buyRev = 0


    def purchase(self, purPrice, tradeStrat, forced = False, rhood = False, ah = False):
        '''
        Determines whether to purchase the ticker based on the current strategy

        Args:
            purpirce (float): tick current data
            tradeStrat (str): current trade strategy
            forced (bool): whether it's being forced to be purchased
            rhood (bool/tuple): if there is info to auto populate if forced to purchase
            ah (bool): whether after hours or not

        Returns:
            (bool): determination of whether to buy or not
        '''
        if forced:
            logging.info('{} Forced Purchase at {}'.format(self.T, self.C))
            self._open(rhood)
            return True

        if not self.update(purPrice):
            logging.info('{} Fetch Empty'.format(self.T))
            return False        

        else:
            if tradeStrat == 'ST':
                #If Short Trading, wait for a price reversal
                #If the price dropped 2x in a row, buy
                if self.C < self.pPrice:
                    self.pPrice = self.C
                    self.buyRev = 0
                elif self.C > self.pPrice:
                    self.buyRev += 1
                else:
                    pass

                if self.buyRev == 2:
                    logging.info('{} Reached ST Buy Criteria At {}'.format(self.T, self.C))
                    self._open(rhood)
                    return True

            if tradeStrat == 'PS':
                if (self.TD[1] - self.C) / self.C > 0.01:
                    if self.C < self.pPrice:
                        self.pPrice = self.C
                        self.buyRev = 0
                    elif self.C > self.pPrice:
                        self.pPrice = self.C
                        self.buyRev += 1
                    else:
                        pass

                    if self.buyRev == 3:
                        logging.info('{} Reached PS Buy Criteria At {}'.format(self.T, self.C))
                        self._open(rhood)
                        return True
        return False


    def revert(self):
        '''
        Reverts the ticker back to state before transaction if there was an error

        Args:
            None

        Returns:
            None
        '''
        self.__dict__.update(self._revert)
