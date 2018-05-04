import logging, sys
logFormat = logging.Formatter('%(name)s _ %(levelname)s _ %(message)s')
rootLog = logging.getLogger()
rootLog.setLevel(logging.INFO)

fileHandler = logging.FileHandler('TradeLogs.log')
fileHandler.setFormatter(logFormat)
rootLog.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormat)
rootLog.addHandler(consoleHandler)

import os, datetime, pytz, holidays, json, requests, sys
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtWidgets import QMenu, QTableWidget
from PyQt5 import uic, QtCore, QtGui
from ObjList import ObjListTableModel, ObjListTable
from Robinhood import Robinhood, exceptions
from resources.rHood import robinTick, robinTicks
from resources.Markets import fetchMarkets
from Helpers import *
import pyqtgraph as pg
from Tick import Tick
from Worker import *
import pandas as pd

TESTING = False

form, base = uic.loadUiType('ui/KStock.ui')

class MainWindow(base, form):
    def __init__(self):
        super(base, self).__init__()
        self.setupUi(self)

        self.qTicks, self.hTicks, self.midTicks = [], [], []
        self.graphData = [[],[]]
        self.qModel, self.hModel = None, None
        self.spy = 'G'

        #Day trading cost which doesn't factor in sales
        self._dtCost = 0

        #Sets the eastern timezone
        self.tz = pytz.timezone('US/Eastern')
        self._us_holidays = holidays.US()

        #List of company names for use later
        self.comps = pd.read_csv('./resources/companyList.csv', sep = ',')[['Symbol', 'Name']]

        #The pool where all the hard calculations and GETS take place
        self.pool = QtCore.QThreadPool()
        logging.info('Max threads: ' + str(self.pool.maxThreadCount()))

        #Signal handling
        self.addQ.clicked.connect(self.addQueue)
        self.startBut.clicked.connect(self.tradeActs)
        self.pauseBut.clicked.connect(self.tradeActs)
        self.actionAPI.triggered.connect(self.api)
        self.budgetBox.valueChanged.connect(self.budgetHandler)
        self.dumpBut.clicked.connect(lambda : self.dump(True))

        #Create Context Menu if right clicked
        self.queue.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.queue.customContextMenuRequested.connect(self.queueContext)

        #Graph options
        self.ePen = pg.mkPen(color = 'b', width = 2)
        self.graph.hideAxis('bottom')

        #Sets up the Robinhood API from the config file if it exists and is correct
        if os.path.isfile('core.cfg'):
            logging.info('Config File Found')
            with open('core.cfg', 'r') as fileIn:
                try:
                    data = json.load(fileIn)
                    self.rUser = data['API']['User']
                    self.rPass = data['API']['Password']
                    
                    try:
                        self.trader = Robinhood()
                        self.trader.login(username = self.rUser, password = self.rPass)
                        logging.info('Successfully Logged Into Robinhood')
                        
                        self.startup(data)
                        self.update()
                        
                        #Starts background threads
                        timer = TimeThread(parent = self)
                        timer.update.connect(self.update)
                        timer.start()

                    except (requests.exceptions.HTTPError, exceptions.LoginFailed):
                        logging.error('Unsuccessful Login For Robinhood')
                        self.warn('Login Fail')

                except json.decoder.JSONDecodeError as e:
                    logging.error(str(e))
                    self.warn('Corrupt')
                    self.rUser, self.rPass, self.qTicks = [], [], []
                    self.trader = None
        else:
            self.warn('No CFG')  
        

    def startup(self, data):
        '''
        Defines the appropriate columns and types for the tables
        Also defines the models for the tables

        Args:
            data (dict): dictionary of config file

        Returns:
            None
        '''
        qproperties = [
            {'attr' : 'T', 'header' : 'Ticker'},
            {'attr' : 'C', 'header' : 'Price'},
            {'attr' : 'PQ', 'header' : 'Qty to Buy'},
        ]
        hproperties = [
            {'attr' : 'T', 'header' : 'Ticker'},
            {'attr' : 'C', 'header' : 'Price'},
            {'attr' : 'Q', 'header' : 'Quantity'},
            {'attr' : 'AP', 'header' : 'Avg Price'},
            {'attr' : 'SL', 'header' : 'Stop Loss'},
            {'attr' : 'tradeable', 'header' : 'Tradeable'}
        ]

        #These models are neat because they actually contain the Tick objects themselves, not just
        #the object's data. When adding to a table, you're adding the actual Tick object to it
        self.qModel = ObjListTableModel(self.qTicks, qproperties, isRowObjects = True, isDynamic = True)
        self.hModel = ObjListTableModel(self.hTicks, hproperties, isRowObjects = True, isDynamic = True, templateObject = Tick())

        self.holding.setModel(self.hModel)
        self.queue.setModel(self.qModel)

        #Sets the budget initial value
        self.budgetHandler(self.budgetBox.value())

        #Initialization time of KStock
        self.startTime = datetime.datetime.now(self.tz).time()

        #Sets the market bar data labels
        self.marketBar(fetchMarkets())

        #Gathers all current Robinhood holdings, this is mostly for if the program crashes
        #mid-day so it can pick back up where it left off
        positions = self.trader.positions()['results']
        if positions:
            logging.info('Previous Items in Robinhood Found, Adding Them')
            for pos in positions:
                inst = self.trader.instrument(pos['instrument'].split('/')[-2])
                if float(pos['quantity']) > 0:
                    if inst['symbol'] not in [tick.T for tick in self.hTicks]:
                        ticker = Tick(inst['symbol'], self.purPrice.value(), self.trader, self.spy)
                        ticker.tradeable = False
                        rhood = (
                            int(float(pos['quantity'])), 
                            round(float(pos['average_buy_price']), 2), 
                            round(float(pos['average_buy_price']) - (float(pos['average_buy_price']) * 0.1), 2)
                        )
                        self.hTicks.append(ticker)
                        ticker.toBuy(
                            purPrice = self.purPrice, 
                            spy = self.spy,
                            forced = True, 
                            rhood = rhood
                        )
                        self.totalCost.setText('%.2f' % (float(self.totalCost.text()) + float(ticker.Q * ticker.AP)))
        
        for tick in set(data['Queue']):
            if tick not in [ticker.T for ticker in self.hTicks]:
                self.qTicks.append(Tick(tick, self.purPrice.value(), self.trader, self.spy)) 
        self.qModel.layoutChanged.emit()
        

    def warn(self, warn):
        '''
        Calls a QDialog to warn about something

        Args:
            warn (str): warning to...uh...warn about

        Returns:
            None
        '''
        warnMessage = {
            'Login Fail' : 'Login Failed for Robinhood',
            'No CFG' : 'No .cfg File Found\nManually Input API Info in Settings > API',
            'Corrupt' : 'The .cfg File Seems to be Corrupt, Re-Input API Info',
            'Near Thresh' : 'Inching Close to Minimum Non-Margin Amount of {}'.format(self.marginSpin.value()),
            'Below Thresh' : 'Non-Margin Fell Below Minimum, Stopping Trading',
            'General' : 'Something Went Wrong With the Execution'
        }

        QMessageBox.critical(None, warn, warnMessage[warn], QMessageBox.Ok)


    def api(self):
        '''
        Sets up the API to RH if able, otherwise warns

        Args:
            None

        Returns:
            None
        '''
        api = Api(self)
        if api.exec_():
            self.rUser = api.user
            self.rPass = api.password
            data = {'Queue': [], 'API': {'Password': self.rPass, 'User': self.rUser}}
            logging.info('Successfully Created Keys and Config')
            self.autosave()
            self.trader = Robinhood()
            try:
                self.trader.login(username = self.rUser, password = self.rPass)
                logging.info('Successfully Logged Into Robinhood')
                if not self.qModel:
                    self.startup(data)
                self.update()
            except requests.exceptions.HTTPError:
                logging.error('Unsuccessful Login For Robinhood')
                self.warn('Login Fail')
                self.api()


    def afterHours(self):
        '''
        Determines whether the market is open (0930-1600, weekdays, non-federal holidays)

        Args:
            None

        Returns:
            (bool): True if market closed, else False
        '''
        now = datetime.datetime.now(self.tz)
        openTime = datetime.time(hour = 9, minute = 30, second = 0, tzinfo = self.tz)
        closeTime = datetime.time(hour = 16, minute = 0, second = 0, tzinfo = self.tz)
        #If a holiday
        if now.strftime('%Y-%m-%d') in self._us_holidays:
            return True
        #If before 0930 or after 1600
        if (now.time() < openTime) or (now.time() > closeTime):
            return True
        #If it's a weekend
        if now.date().weekday() > 4:
            return True

        return False


    def marketBar(self, data):
        '''
        Sets the market bar labels accordingly and colors them

        Args:
            data (dict): Dow, Nasdaq and S&P market data

        Returns:
            None
        '''
        labels = {
            'Dow' : (self.dowQuote, self.dowChange),
            'Nasdaq' : (self.nasdaqQuote, self.nasdaqChange),
            'S&P' : (self.spQuote, self.spChange)
        }

        for item in labels:
            for i in range(len(labels[item])):
                dType = 'Quote' if i == 0 else 'Change'
                labels[item][i].setText(data[item][dType])
                if data[item]['D']:
                    if data[item]['D'] == 'R':
                        style = 'background-color: rgb(166, 0, 0);'
                    else:
                        style = 'background-color: rgb(0, 170, 0);'
                    labels[item][i].setStyleSheet(style)

        if data['S&P']['D']:
            self.spy = data['S&P']['D']
        

    def budgetHandler(self, value):
        '''
        Handles the data change of the budget spin box

        Args:
            value (float): value of qspinbox

        Returns:
            None
        '''
        if value == 0:
            #If it's set to 0, there is no budget
            self.budget = 99999999
        else:    
            if not TESTING:
                #If real-trading, maximum budget is set to what you have available
                self.budgetBox.setMaximum(float(self.cash.text()))

            self.budget = value
            logging.info('--- Budget Changed to: {} ----'.format(self.budget))


    def tradeActs(self):
        '''
        Disables/Enables Trading Start/Stop buttons
        Basically starts the whole trading process if `startBut` is disabled

        Args:
            None

        Returns:
            None
        '''
        self.pauseBut.setEnabled(not self.pauseBut.isEnabled())
        self.startBut.setEnabled(not self.startBut.isEnabled())

        if not self.startBut.isEnabled():
            logging.info('---- Started Trading ----')
            self.budgetBox.setEnabled(False)
            self.dumpBut.setEnabled(True)
        else:
            logging.info('---- Paused Trading ----')
            self.budgetBox.setEnabled(True)
            self.dumpBut.setEnabled(False)


    def queueContext(self, pos):
        '''
        Creates the context menu for the Queue

        Args:
            pos (QModelIndex): index of the selected row

        Returns:
            None
        '''
        if self.qModel.rowCount() > 0:
            menu = QMenu()
            buyX = menu.addAction('Buy Tick')
            delX = menu.addAction('Remove From Queue')

            action = menu.exec_(self.queue.mapToGlobal(pos))
            rowTick = self.qTicks[self.queue.rowAt(pos.y())]

            if action == delX:
                #Removes row from table
                logging.info('Removed {} From Queue'.format(rowTick.T))
                self.qModel.removeRow(self.qTicks.index(rowTick))
                self.qTicks.remove(rowTick)


            if action == buyX:
                reply = QMessageBox.question(
                    None, 
                    'Purchase?', 
                    'Purchase {} shares of {} for at {}'.format(rowTick.PQ, rowTick.T, rowTick.C),
                    QMessageBox.Yes, QMessageBox.No)

                if reply == QMessageBox.Yes:
                    try:
                        rowTick.toBuy(
                            purPrice = self.purPrice.value(), 
                            spy = self.spy,
                            forced = True
                        )
                        self.totalCost.setText('%.2f' % (float(self.totalCost.text()) + float(rowTick.Q * rowTick.AP)))
                        self._dtCost += float(rowTick.Q * rowTick.AP)
                        self.transTable.bought(rowTick)
                        self.hTicks.append(rowTick)
                        self.qTicks.remove(rowTick)

                        self.hModel.layoutChanged.emit()
                        self.queue.viewport().update()
                    except TypeError as e:
                        logging.info('General Error: {}'.format(e))
                        self.warn('General')


    def dump(self, clicked = False):
        '''
        Sells the remaining stocks if there are any current purchases

        Args:
            clicked (bool): whether the 'Dump All' button was pressed

        Returns:
            None
        '''
        if self.hModel.rowCount() > 0:
            if clicked:
                msg = 'Are you sure you want to dump all currently held stocks?'
                dumpDia = QMessageBox.question(self, 'Are You Sure', msg, QMessageBox.Yes, QMessageBox.No)
                if dumpDia == QMessageBox.No: return

            logging.info('---- Selling all positions ----')
            ticksToSell = [tick for tick in self.hTicks if tick.tradeable]

            while len(ticksToSell) > 0:
                ticker = ticksToSell.pop(0)
                self.sell(ticker)
                time.sleep(0.25)

        if not clicked:
            self.tradeActs()


    def revert(self, ticker, fromList, toList):
        '''
        Undos the transaction if there was an error

        Args:
            None

        Returns:
            None
        '''
        ticker.revert()
        if ticker.T in [tick.T for tick in fromList]:
            fromList.remove(ticker)
        if ticker.T not in [tick.T for tick in toList]:
            toList.append(ticker)


    def purchase(self, ticker, fromMidPrice = None):
        '''
        Purchases the stock by removing it from the Queue, placing it on the Holding table and 
        making the Robninhood call

        Args:
            ticker (Tick): Tick object of ticker we're actually purchasing

        Returns:
            None
        '''
        try:
            #Takes the ticker, puts it in Holdings, remove it from Queue and adds the transaction to Transaction
            self.transTable.bought(ticker)
            self.hTicks.append(ticker)

            if fromMidPrice:
                self.midTicks.remove(ticker)
                tprice = fromMidPrice
            else:
                tPrice = ticker.AP
            
            self._dtCost += float(ticker.Q * tPrice)    
            self.totalCost.setText('%.2f' % (float(self.totalCost.text()) + float(ticker.Q * tPrice)))

            logging.info('---- Bought {} shares of {} at {}, SL: {} ----'.format(ticker.Q, ticker.T, tPrice, ticker.SL))

            return True

        except ValueError:
            #Reverts back the purchase
            logging.error('~~~~ Error With Purchase, Reverting Back ~~~~')
            self.revert(ticker, self.hTicks, self.qTicks)

        return False


    def sell(self, ticker, fromMidPrice = None):
        '''
        Sells the stock by removing it from the Holding, placing it on the Queue, if re-buy and 
        making the Robninhood call

        Args:
            ticker (Tick): Tick object of ticker we're actually purchasing

        Returns:
            None
        '''
        if fromMidPrice:
            tPrice = fromMidPrice
            self.midTicks.remove(ticker)
        else:
            tPrice = ticker.C

        logging.info('---- Sold {} shares of {} at {} ----'.format(ticker.Q, ticker.T, tPrice))

        #Updates profit and costs
        indprofit = float(ticker.Q * tPrice) - float(ticker.Q * ticker.AP)      
        profitLabel = float(self.profitLabel.text()) + indprofit
           
        logging.info('---- {} Profit: {} ----'.format(ticker.T, round(indprofit, 2)))
        self.profitLabel.setText('%.2f' % (profitLabel))
        self.totalCost.setText('%.2f' % (float(self.totalCost.text()) - (ticker.Q * tPrice)))

        #If rebuying puts the old tick back on the Queue
        if self.rebuy.isChecked():
            self.qTicks.append(ticker)
            self.qModel.layoutChanged.emit()

        ticker.close()

        self.transTable.sold(ticker)
        
        return True


    
    def update(self):
        '''
        The main function that gets called every X contains all the child
        table updating functions

        Args:
            None

        Returns:
            None
        '''

        def _success(worker):
            #Called when one of the workers is successfully completed
            return


        def _error(worker):
            #Called if there was an error
            logging.error('~~~~ Error with the {} ~~~~'.format(worker))


        def _midCheck():
            '''
            Monitors the middle man list for unfilled orders

            Args:
                None

            Returns:
                None
            '''
            headers = {'Accept': 'application/json', 'Authorization' : self.trader.headers['Authorization']}

            for tick in self.midTicks:
                if tick.transID:
                    url = 'https://api.robinhood.com/orders' + '/' + tick.transID[1]
                    res = requests.get(url, headers = headers).json()
                    if tick.transID[0] == 'sell':
                        if res['state'] in ['partially_filled', 'filled', 'confirmed']:
                            self.sell(tick, fromMidPrice = float(res['price']))
                    else:
                        if res['state'] in ['partially_filled', 'filled']:
                            self.purchase(tick, fromMidPrice = float(res['price']))


        def _tickUpdate(curList):
            '''
            Updates the tick objects in the respective list

            Args:
                curList (str): string name of list that is being updated

            Returns:
                None
            '''
            listDict = {'Hold' : self.hTicks, 'Queue' : self.qTicks}
            tickData = robinTicks(self.trader, [tick.T for tick in listDict[curList]], self.afterHours())
            if len(tickData) != len(listDict[curList]):
                logging.error('~~~~ {} and Fetch Lengths Do Not Match ~~~~'.format(curList))
                return
            else:
                for tickDict in tickData:
                    try:
                        idx = [tick.T for tick in listDict[curList]].index(tickDict['Sym'])
                    except ValueError:
                        return
                    listDict[curList][idx].update(
                        data = tickDict['Data'], 
                        purPrice = self.purPrice.value(), 
                        spy = self.spy 
                    )


        def _queueCall():
            '''
            Performs all the necessaries for the Queue table, is put in a worker
            and executes in the background

            Args:
                None

            Returns:
                None
            '''
            if len(self.qTicks) > 0:
                _tickUpdate('Queue')

            #If actually trading, iterate through Queue and if the projected cost doesn't exceed budget see if
            #it meets purchasing criteria, else just update
            if not self.startBut.isEnabled():
                for tick in self.qTicks:
                    logging.info('Queue {}'.format(tick.T))
                    transPrice = tick.C * tick.PQ
                    try:
                        if self._dtCost + transPrice < self.budget and transPrice < float(self.buyingPower.text()) and transPrice < float(self.cash.text()):
                            if tick.toBuy(
                                purPrice = self.purPrice.value(), 
                                spy = self.spy
                            ):
                                if not TESTING:
                                    if float(self.buyingPower.text()) > transPrice:
                                        resp = self.trader.place_limit_buy_order(
                                            symbol = tick.T, 
                                            time_in_force = 'GFD', 
                                            price = tick.C, 
                                            quantity = tick.PQ
                                        ).json()

                                        if resp['state'] in ['unconfirmed', 'queued']:
                                            logging.info('---- {} Added to MiddleMan, Waiting for Buy Confirmation ----'.format(tick.T))
                                            tick.transID = (resp['side'], resp['id'])
                                            self.midTicks.append(tick)
                                            self.qTicks.remove(tick)
                                            self.qModel.layoutChanged.emit()
                                        elif resp['state'] in ['partially_filled', 'filled']:
                                            self.purchase(tick)
                                        else:
                                            logging.error('~~~~ Something Went Wrong With {}s Purchase ~~~~'.format(tick.T))
                                            logging.error('~~~~ Robinhood Response for {}: {}'.format(tick.T, resp['state']))
                                            self.revert(tick, self.qTicks, self.hTicks)
                                else:
                                    self.purchase(tick)
                    except TypeError:
                        pass                                   


        def _holdCall():
            '''
            Performs all the necessaries for the Holdings table, is put in a worker
            and executes in the background

            Args:
                None

            Returns:
                None
            '''
            if len(self.hTicks):
                _tickUpdate('Hold')

            if not self.startBut.isEnabled():
                for tick in self.hTicks:
                    if tick.tradeable:
                        logging.info('Hold {}'.format(tick.T))
                        if tick.toSell(
                            purPrice = self.purPrice.value(), 
                            spy = self.spy 
                        ):
                            if not TESTING:
                                resp = self.trader.place_limit_buy_order(
                                    symbol = tick.T, 
                                    time_in_force = 'GFD', 
                                    price = tick.C, 
                                    quantity = tick.PQ
                                ).json()

                                if resp['state'] in ['unconfirmed', 'queued']:
                                    logging.info('---- {} Added to MiddleMan, Waiting for Buy Confirmation ----'.format(tick.T))
                                    tick.transID = (resp['side'], resp['id'])
                                    self.midTicks.append(tick)
                                    self.hTicks.remove(tick)
                                    self.hModel.layoutChanged.emit()
                                elif resp['state'] in ['partially_filled', 'filled', 'confirmed']:
                                    self.sell(tick)
                                else:
                                    logging.error('~~~~ Something Went Wrong With {}s Sale ~~~~'.format(tick.T))
                                    logging.error('~~~~ Robinhood Response for {}: {}'.format(tick.T, resp['state']))
                                    self.revert(tick, self.qTicks, self.hTicks)
                            else:
                                self.sell(tick)


        #Robinhood portfolio, creates an empty one if an error is thrown
        #such as having 0 in the portfolio
        try:
            self.portfolio = self.trader.portfolios()
            self.account = self.trader.get_account()['margin_balances']
        except IndexError:
            logging.info('~~~~ Portfolio Empty ~~~~')
            self.portfolio = {
                'equity' : 0,
                'extended_hours_equity' : 0,
            }
            self.account = {
                'unsettled_funds' : 0,
                'start_of_day_dtbp' : 0,
                'unallocated_margin_cash': 0
            }

        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError, TimeoutError) as e:
            logging.info('~~~~ Connection Error: {} ~~~~'.format(e))
            return

        #Updates the market tracker bar
        self.marketBar(fetchMarkets())

        now = datetime.datetime.now(self.tz).time()
        
        #Set the Equity to current value depending on if it's aH or not
        if self.afterHours():
            self.equity.setText('%.2f' % (float(self.portfolio['extended_hours_equity'])))

            #Disable Trading aH
            if not TESTING:
                if not self.startBut.isEnabled():
                    self.tradeActs()

        else:
            self.equity.setText('%.2f' % (float(self.portfolio['equity'])))

            if self.portfolio['equity']:
                #Plt that stuff if it's during the trading day
                
                self.graphData[0].append(now.strftime('%H:%M:%S'))
                self.graphData[1].append(float(self.portfolio['equity']))

                xdict = dict(enumerate(self.graphData[0]))
                ax = self.graph.getAxis('bottom')
                ax.setTicks([xdict.items()])
                
                self.graph.plot(list(xdict.keys()), self.graphData[1], pen = self.ePen, clear = False)

        self.buyingPower.setText('%.2f' % (float(self.account['start_of_day_dtbp'])))
        self.cash.setText('%.2f' % (float(self.account['unallocated_margin_cash'])))
        self.uFund.setText('%.2f' % (float(self.account['unsettled_funds'])))
        
        if not TESTING:
            if not self.startBut.isEnabled():
                #If end of day approaching, close out all positions regardless of profit
                if now > datetime.time(hour = 15, minute = 58, second = 0, tzinfo = self.tz):
                    self.dump()

                #Safety-net for SEC guideline of >25000 on Non-Margin for day trading
                if self.marginSpin.value() < float(self.equity.text()) < self.marginSpin.value() + 100:
                    self.warn('Near Thresh')
                if float(self.equity.text()) < self.marginSpin.value():
                    logging.info('~~~~ Equity Fell Below Threshold ~~~~')
                    self.warn('Below Thresh')
                    self.tradeActs()
            
            self.purPrice.setMaximum(float(self.cash.text()))

        else:
            #Allow for dumping of stocks at end of the day if just testing
            if not self.startBut.isEnabled():
                if self.startTime < datetime.time(hour = 16, minute = 0, second = 0, tzinfo = self.tz):
                    if now > datetime.time(hour = 15, minute = 58, second = 0, tzinfo = self.tz):
                        self.dump()

        if len(self.hTicks) > 0:
            holdWorker = Worker(_holdCall)
            holdWorker.signals.finished.connect(lambda : _success('Hold'))
            holdWorker.signals.error.connect(lambda : _error('Hold'))

            self.pool.start(holdWorker)
            self.hModel.layoutChanged.emit()
            self.holding.viewport().update()

        #Only calls the update function if there's stuff in the table, saves memory
        if len(self.qTicks) > 0:
            queueWorker = Worker(_queueCall)
            queueWorker.signals.finished.connect(lambda : _success('Queue'))
            queueWorker.signals.error.connect(lambda : _error('Queue'))

            self.pool.start(queueWorker)
            self.qModel.layoutChanged.emit()
            self.queue.viewport().update()
            
        if len(self.midTicks) > 0:
            midWorker = Worker(_midCheck)
            midWorker.signals.finished.connect(lambda : _success('Middle'))
            midWorker.signals.error.connect(lambda : _error('Middle'))

            self.pool.start(midWorker)


    def addQueue(self, ticks = False):
        '''
        Adds a ticker to to the Queue, whether from the config file
        or the dialog

        Args:
            ticks (bool): whether adding ticks from the config file

        Returns:
            None
        '''
        def _add(ticker):
            '''
            Actually adds the ticker obj to the queue

            Args:
                ticker (str): ticker name to be added

            Returns:
                None
            '''
            if ticker not in [tick.T for tick in self.qTicks + self.hTicks]:
                inst = self.trader.instruments(ticker)[0]

                #Whether it's actually tradeable on RH
                if not inst['tradeable']: return

                #Whether it's a high volatilty stock (RH has some rules against this)
                sig = float(inst['maintenance_ratio'])
                if  sig > 0.5:
                    msg = '{} is a High Volatility stock (σ = {}), are you sure you want to add it?'.format(ticker, sig)
                    addWarn = QMessageBox.question(self, 'High Volatility Stock', msg, QMessageBox.Yes, QMessageBox.No)
                    if addWarn == QMessageBox.No: return

                self.qTicks.append(Tick(ticker, self.purPrice.value(), self.trader, self.spy))
                self.qModel.layoutChanged.emit()
                logging.info('Added ' + ticker + ' to Queue')



        if not ticks:
            tick = AddTick(self.comps['Symbol'].values, self)
            if tick.exec_():
                if tick.result() and tick.tickEdit.text():
                    if not TESTING:
                        if float(self.equity.text()) > 25000:
                            _add(tick.tickEdit.text())

                            #Autosaves...duh
                            self.autosave()
                    else: 
                        _add(tick.tickEdit.text())
        else:
            for item in self.qTicks:
                _add(item)


    def autosave(self, close = False):
        '''
        Saves the RH user/pass and every tick in Queue

        Args:
            close (bool): whether the program is closing or not

        Returns:
            None
        '''    
        if self.rUser and self.rPass:
            if not close: logging.info('Autosaving...')
            with open('core.cfg', 'w') as fileOut:
                data = {
                    'API' : {'User' : self.rUser, 'Password' : self.rPass},
                    'Queue' : [tick.T for tick in self.qTicks if self.qTicks]
                }

                json.dump(data, fileOut)


    def closeEvent(self, event):
        '''
        Handles the closing event, calls autosave()

        Args:
            event (QEvent): close event

        Returns:
            None
        '''
        logging.info('Closing and Resubmitting Config File')
        try:
            self.autosave(True)
        except AttributeError:
            pass



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())