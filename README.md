

# KStock - Robinhood Day Trading

**This is still in testing, please report all bugs!**


KStock is a Robinhood Day-Trading Bot written in Python >3.5. It uses the unofficial Robinhood API, as well as historical data to continuously monitor stocks and the user's portfolio, determining when the most opportune time would be to sell/buy an individual security. 

For those of you wondering, no. This does not have any cryptocurrency or options integration. Robinhood hasn't released crypto and options trading completely to everyone yet, so until that happens this is strictly just for securities.

![Live Tab](https://github.com/aseylys/KStock/blob/master/imgs/Front.png) ![Background Tab](https://github.com/aseylys/KStock/blob/master/imgs/Back.png)

### Features

KStock features two Tabs: **Live**, **Backend**. 
## Live tab

 The *"command power-house of the app"*. It features all the necessary information for monitoring KStock. The Current Holdings table contains all the ticker object that the user currently owns. This is continuously updated every three seconds. The top market bar shows the status of Dow, the S&P 500, and the NASDAQ.  On the bottom is a graph showing the trend of the user's equity throughout the time KStock has been on. On the right houses the settings and value of the user's account. 
    * **Buying Power**: The user's day trading buying power. This is reset everyday and is dependent on what type of account the user has and what stocks they are currently trading. This is pretty much the limiting factor on how many trades a user can do in a day.
    * **Cash**: The actual money the user is using to purchase the stocks. With an instant account this should be up to date with all instant settlements.
    * **Equity Min**: A user defined value (default: 25000); the minimum the user wants their total equity to drop to before stopping trading.
    * **Limit/Purchase**: A user defined value (default: 1000); how much KStock spends on each purchase
    * **Day Budget**: A user defined value (default: 0.00); how much the user wants to spend today (reflected under **Total Cost**), if set to 0.00 there is no budget and KStock will continue to purchase stock until **Cash** runs out. Disabled when trading has begun, **Pause** to edit this value.
    * **Re-Buy**: A user defined value (default: Checked); if checked and if a stock is sold, it will be put back on the **Queue** to try and be purchased again
    * **Equity**: Total net worth of the user
    * **Unsettled Debit**: How much funds are unsettled. This could get pretty high depending on how much trading is accomplished in a day. Basically how much funds are unsettled in your account - these take about three days to settle.
    * **Trading Control**: Starting and stopping trading is controlled with these two buttons. Trading is automatically stopped after 1558 EST after selling off all tradeable stocks. 
    * **Total Cost**: How much has been spent in total. If 0 securities were held throughout the night, the total cost will be the total spent today. Takes into account sales and profits.
    * **Today's Profit**: How much has been made today.
    * **Dump All**: If clicked, and if confirmed, sells off all tradeable stocks.

## Backend Tab

On the left is the Transactions Table. This shows all transactions that have currently been performed. If a security is bought, it's Ticker Symbol, Quantity Purchased, and Purchase Price are added to the table. Once sold, it's Sell Price is then added to it's row, updating it's color dependent on profitability (red = loss, green = profit)

On the right is the Queue Table. This shows all securities being analyzed, waiting to purchased. The user can add more securities by clicking **Add Tick** and searching for the securities ticker symbol. The user can also delete or manually purchase securities by right-clicking on the security. 

## Behind the Scenes

The **Holdings** and **Queue** table are built such that they actually house the `Tick` objects themselves. So when a transaction is performed, the actual `Tick` object is moved from one table to another. This makes it easy to change the trading logic of securities. 

 - If one wants to adjust the day-trading logic, all of it is housed in `Tick.py`. Right now it uses a Price Swinging strategy, where it looks for a peak/valley and performs the transaction if it meets the criteria.
 - Right now KStock features a Price Reversal strategy where it uses the days previous prices and puts it through a pivot seeking algorithm to determine when the most opportune time would be to preform a transaction. However, if the S&P is down below 1%, it just looks for any profit, so as soon as the price is above the average purchase price, it will sell. 

Right now, and possibly indefinitely, KStock only preforms Limit Orders. Market Orders with Robinhood are total garbage, so to implement a Limit Order KStock first sends the order. It then checks the response, and if it was filled, it executes normally (by doing all the math and putting it into the Holdings table). If however, the order wasn't filled immediately, it places the tick in a middle-man list and continuously monitors it waiting for it to be filled. 

/
KStock also features live paper-trading to test strategies. Testing is capable using the global variable `TESTING`, it allows the user to play with the live data and the logic without making a real-world trade. If `TESTING=False` it will execute the commands and send the execution order to Robinhood to purchase/sell, **make sure `TESTING` is set to how you want it to.**

### Installation

KStock requires a few dependencies to get it up and running.
* PyQt5
* holidays
* pandas
* pyqtgraph
* h5py
* demjson
* bs4
* html5lib
* [Robinhood](https://github.com/Jamonek/Robinhood)

All of the requirements are covered in `requirements.txt`

```sh
$ pip3 install -r requirements.txt
```

To run:
```sh
$ python KStock.py
```


On first initialization, a couple error windows will pop up. That's expected, seeing as how you haven't inputted your Robinhood data yet.
You'll need to input your Robinhood info by going to Settings -> API. Assuming everything is correct, you'll then need to verify your Robinhood account. Make sure you're at least an Instant account, Gold also works. Cash accounts are not yet supported so if you are cash, upgrade your account. You'll also need to disable Pattern Day Trading Protection by going into Robinhood -> Account -> Day Trade Settings.

Being developed in PyQt, KStock is cross-platform.

### Todos

 - Continue the never-ending testing
 - Cancel an order if it's un-filled for a while
  
License
----

GNU GPL v3.0


