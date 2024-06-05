import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order


class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}
        self.current_prices = {}
        self.ema_12 = {}
        self.ema_26 = {}
        self.macd = {}
        self.signal = {}
        self.account_balance = None
        self.current_position = {}

        self.securities = {
            "AAPL": {"contract": self.createContract("AAPL")},
            "MSFT": {"contract": self.createContract("MSFT")},
            "GOOGL": {"contract": self.createContract("GOOGL")},
            "TSLA": {"contract": self.createContract("TSLA")},
            "AMZN": {"contract": self.createContract("AMZN")},
            "NFLX": {"contract": self.createContract("NFLX")},
            "KO": {"contract": self.createContract("KO")},
            "XOM": {"contract": self.createContract("XOM")},
        }

    def createContract(self, symbol):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def nextValidId(self, orderId: int):
        self.orderId = orderId
        self.reqAccountSummary(9001, "All", "TotalCashValue")
        # Request historical data and market data for each security
        for symbol, info in self.securities.items():
            reqId = self.orderId + len(self.securities)  # Generate a unique reqId for each security
            info["reqId"] = reqId  # Store the reqId in the info dictionary
            self.reqHistoricalData(
                reqId, info["contract"], "", "1 M", "1 day", "MIDPOINT", 0, 1, False, [])
            self.reqMktData(reqId, info["contract"], "", False, False, [])


    def accountSummary(self, reqId, account, tag, value, currency):
        if tag == "TotalCashValue" and currency == "USD":
            self.account_balance = float(value)

        if self.account_balance is not None:
            for symbol, info in self.securities.items():
                # Generate a unique reqId for each security
                reqId = self.orderId + len(self.securities)
                info["reqId"] = reqId  # Store the reqId in the info dictionary
                self.reqHistoricalData(
                    reqId, info["contract"], "", "1 M", "1 day", "MIDPOINT", 0, 1, False, [])

    def historicalData(self, reqId, bar):
        symbol = self.getSymbolFromRequestId(reqId)
        if symbol not in self.data:
            self.data[symbol] = []
        self.data[symbol].append([bar.date, bar.close])

    def historicalDataEnd(self, reqId, start, end):
        for symbol, symbol_data in self.data.items():
            df = pd.DataFrame(symbol_data, columns=["date", "close"])
            df["date"] = pd.to_datetime(df["date"], format='%Y%m%d')
            df.set_index("date", inplace=True)
            df['12d_EMA'] = df['close'].ewm(span=12, adjust=False).mean()
            df['26d_EMA'] = df['close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['12d_EMA'] - df['26d_EMA']
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

            self.ema_12[symbol] = df['12d_EMA'].iloc[-1]
            self.ema_26[symbol] = df['26d_EMA'].iloc[-1]
            self.macd[symbol] = df['MACD'].iloc[-1]
            self.signal[symbol] = df['Signal'].iloc[-1]

        for symbol, info in self.securities.items():
            self.reqMktData(
                self.orderId, info["contract"], "", False, False, [])

    def tickPrice(self, reqId, tickType, price, attrib):
        symbol = self.getSymbolFromRequestId(reqId)
        if tickType == 4:
            if symbol not in self.current_prices:
                self.current_prices[symbol] = {}
            self.current_prices[symbol]['last'] = price
            self.onPriceUpdate(symbol, price)

    def getSymbolFromRequestId(self, reqId):
        for symbol, info in self.securities.items():
            if info["reqId"] == reqId:
                return symbol
        return None

    def onPriceUpdate(self, symbol, price):
        if symbol not in self.ema_12 or symbol not in self.ema_26 or symbol not in self.macd or symbol not in self.signal:
            return

        alpha_12 = 2 / (12 + 1)
        alpha_26 = 2 / (26 + 1)
        signal_alpha = 2 / (9 + 1)

        self.ema_12[symbol] = (price - self.ema_12[symbol]) * \
            alpha_12 + self.ema_12[symbol]
        self.ema_26[symbol] = (price - self.ema_26[symbol]) * \
            alpha_26 + self.ema_26[symbol]
        new_macd = self.ema_12[symbol] - self.ema_26[symbol]
        self.signal[symbol] = (new_macd - self.signal[symbol]) * \
            signal_alpha + self.signal[symbol]
        self.macd[symbol] = new_macd

        if self.macd[symbol] > self.signal[symbol] and self.current_position.get(symbol, 0) == 0:
            print(f"Bought {symbol}")
            # self.placeBuyOrder(self.orderId, self.securities[symbol]["contract"])
        elif self.macd[symbol] < self.signal[symbol] and self.current_position.get(symbol, 0) > 0:
            print(f"Sold {symbol}")
            # self.placeSellOrder(self.orderId, self.securities[symbol]["contract"])
        else:
            print(f"No trading signal for {symbol}")

    def placeBuyOrder(self, orderId, contract, quantity):
        if self.account_balance is None:
            print("Account balance not available")
            return

        # Calculate the amount to use for buying (20% of account balance)
        amount_to_use = self.account_balance * 0.2

        if 'last' in self.current_prices:
            last_price = self.current_prices['last']
            max_quantity = amount_to_use // last_price

            if max_quantity <= 0:
                print("Not enough balance to buy even a single share")
                return

            # Adjust quantity if it exceeds available cash
            quantity = min(quantity, max_quantity)

            myorder = Order()
            myorder.orderId = orderId
            myorder.action = "BUY"
            myorder.orderType = "MKT"
            myorder.totalQuantity = quantity

            self.placeOrder(orderId, contract, myorder)
            # Update current position only for bought securities
            if contract.symbol not in self.current_position:
                self.current_position[contract.symbol] = 0
            self.current_position[contract.symbol] += quantity

    def placeSellOrder(self, orderId, contract, quantity):
        if contract.symbol not in self.current_position or self.current_position[contract.symbol] <= 0:
            print("No shares of this security to sell")
            return

        myorder = Order()
        myorder.orderId = orderId
        myorder.action = "SELL"
        myorder.orderType = "MKT"
        myorder.totalQuantity = min(
            quantity, self.current_position[contract.symbol])

        self.placeOrder(orderId, contract, myorder)
        self.current_position[contract.symbol] -= min(
            quantity, self.current_position[contract.symbol])


app = TestApp()
app.connect("127.0.0.1", 7496, 1)
app.run()
