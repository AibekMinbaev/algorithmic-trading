import yfinance as yf
import numpy as np
from scipy.signal import argrelextrema
from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import *
from ibapi.order import *

class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId: int):
        # Define the Apple (AAPL) contract
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"  # Stock type
        contract.exchange = "SMART"  # Use SMART exchange for best execution
        contract.currency = "USD"

        # Request contract details for Apple (AAPL)
        self.reqContractDetails(orderId, contract)

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        # Print the contract details received
        print(contractDetails.contract)

        # Get the latest data
        ticker = contractDetails.contract.symbol
        data = yf.download(ticker, start='2024-01-01', end='2024-06-01')
        
        # Check if data is available
        if data.empty:
            print("No data available for", ticker)
            return

        # Calculate technical indicators
        data['12d_EMA'] = data['Close'].ewm(span=12, adjust=False).mean()
        data['26d_EMA'] = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = data['12d_EMA'] - data['26d_EMA']
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['200d_SMA'] = data['Close'].rolling(window=200).mean()

        # Find support and resistance levels
        data['Min'] = data.iloc[argrelextrema(data['Close'].values, np.less_equal, order=5)[0]]['Close']
        data['Max'] = data.iloc[argrelextrema(data['Close'].values, np.greater_equal, order=5)[0]]['Close']
        data['Support'] = data['Min'].fillna(method='bfill')
        data['Resistance'] = data['Max'].fillna(method='bfill')

        current_data = data.iloc[-1]

        # Check MACD strategy and support/resistance levels
        if current_data['MACD'] > current_data['Signal'] and \
                current_data['Close'] > current_data['200d_SMA'] and \
                current_data['Close'] <= current_data['Support'] * 1.01:
            # Place buy order
            self.placeBuyOrder(reqId, contractDetails.contract)

        elif current_data['MACD'] < current_data['Signal'] and \
                current_data['Close'] < current_data['200d_SMA'] and \
                current_data['Close'] >= current_data['Resistance'] * 0.99:
            # Place sell order
            self.placeSellOrder(reqId, contractDetails.contract)

        else:
            print("No trading signal")

    def placeBuyOrder(self, orderId, contract):
        # Create a buy order
        myorder = Order()
        myorder.orderId = orderId
        myorder.action = "BUY"
        myorder.orderType = "MKT"
        myorder.totalQuantity = 10  # Buy 10 shares of AAPL stock

        # Place the buy order
        self.placeOrder(orderId, contract, myorder)

    def placeSellOrder(self, orderId, contract):
        # Create a sell order
        myorder = Order()
        myorder.orderId = orderId
        myorder.action = "SELL"
        myorder.orderType = "MKT"
        myorder.totalQuantity = 10  # Sell 10 shares of AAPL stock

        # Place the sell order
        self.placeOrder(orderId, contract, myorder)

# Create an instance of TestApp
app = TestApp()
app.connect("127.0.0.1", 7496, 1000)
app.run()
