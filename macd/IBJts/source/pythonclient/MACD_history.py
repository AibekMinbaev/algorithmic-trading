import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order


class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []  
        self.current_prices = {}
        self.ema_12 = None
        self.ema_26 = None
        self.macd = None
        self.signal = None
        self.account_balance = None
        self.current_position = 0  

    def nextValidId(self, orderId: int):
        self.orderId = orderId
        # Define the Apple (AAPL) contract
        self.contract = Contract()
        self.contract.symbol = "AAPL"
        self.contract.secType = "STK"
        self.contract.exchange = "SMART"
        self.contract.currency = "USD"

        # Request account details to get the current balance
        self.reqAccountSummary(9001, "All", "TotalCashValue")

    def accountSummary(self, reqId, account, tag, value, currency):
        if tag == "TotalCashValue" and currency == "USD":
            self.account_balance = float(value)
            print(f"Account balance: {self.account_balance} USD")
            print(f"Used money: {self.account_balance * 0.001}")

        # Request historical data for initialization after getting account balance
        if self.account_balance is not None:
            self.reqHistoricalData(
                self.orderId, self.contract, "", "1 M", "1 day", "MIDPOINT", 0, 1, False, [])

    def accountSummaryEnd(self, reqId):
        print("Account summary end")

    def historicalData(self, reqId, bar):
        self.data.append([bar.date, bar.close])

    def historicalDataEnd(self, reqId, start, end):
        # Convert data to pandas DataFrame
        df = pd.DataFrame(self.data, columns=["date", "close"])
        df["date"] = pd.to_datetime(df["date"], format='%Y%m%d')
        df.set_index("date", inplace=True)

        # Calculate initial technical indicators
        df['12d_EMA'] = df['close'].ewm(span=12, adjust=False).mean()
        df['26d_EMA'] = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['12d_EMA'] - df['26d_EMA']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        self.ema_12 = df['12d_EMA'].iloc[-1]
        self.ema_26 = df['26d_EMA'].iloc[-1]
        self.macd = df['MACD'].iloc[-1]
        self.signal = df['Signal'].iloc[-1]

        # Now request real-time market data
        self.reqMktData(self.orderId, self.contract, "", False, False, [])

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 4:  # Last price
            self.current_prices['last'] = price
            self.onPriceUpdate(price)

    def tickSize(self, reqId, tickType, size):
        pass  # You can handle size updates if needed

    def onPriceUpdate(self, price):
        print("Price is updated: ", price)
        if self.ema_12 is None or self.ema_26 is None or self.macd is None or self.signal is None:
            return  

        alpha_12 = 2 / (12 + 1)
        alpha_26 = 2 / (26 + 1)
        signal_alpha = 2 / (9 + 1)

        # Update the EMAs, MACD, and Signal line
        self.ema_12 = (price - self.ema_12) * alpha_12 + self.ema_12
        self.ema_26 = (price - self.ema_26) * alpha_26 + self.ema_26
        new_macd = self.ema_12 - self.ema_26
        self.signal = (new_macd - self.signal) * signal_alpha + self.signal
        self.macd = new_macd

        # Make trading decisions based on updated indicators and account balance
        if self.macd > self.signal and self.current_position == 0:
            print("Bought")
            self.placeBuyOrder(self.orderId, self.contract)
        elif self.macd < self.signal and self.current_position > 0:
            print("Sold")
            self.placeSellOrder(self.orderId, self.contract)
        else:
            print("No trading signal")

    def placeBuyOrder(self, orderId, contract):
        if self.account_balance is None:
            print("Account balance not available")
            return

        # Risk management: 20% of balance 
        amount_to_use = self.account_balance * 0.2

        if 'last' in self.current_prices:
            last_price = self.current_prices['last']
            quantity = amount_to_use // last_price

            if quantity <= 0:
                print("Not enough balance to buy even a single share")
                return

            myorder = Order()
            myorder.orderId = orderId
            myorder.action = "BUY"
            myorder.orderType = "MKT"
            myorder.totalQuantity = quantity

            self.placeOrder(orderId, contract, myorder)
            self.current_position += quantity
            print(f"Bought {quantity} of {self.contract.symbol} for {amount_to_use} USD")

    def placeSellOrder(self, orderId, contract):
        myorder = Order()
        myorder.orderId = orderId
        myorder.action = "SELL"
        myorder.orderType = "MKT"
        myorder.totalQuantity = self.current_position

        self.placeOrder(orderId, contract, myorder)
        self.current_position = 0


app = TestApp()
app.connect("127.0.0.1", 7496, 1)
app.run()
