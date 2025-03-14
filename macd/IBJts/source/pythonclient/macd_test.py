from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pandas as pd

class TestApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []

    def nextValidId(self, orderId: int):
        # Define the Apple (AAPL) contract
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        # Request contract details for Apple (AAPL)
        self.reqContractDetails(orderId, contract)

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        # Print the contract details received
        print(contractDetails.contract)

        # Request historical data for Apple (AAPL)
        self.reqHistoricalData(reqId, contractDetails.contract, "", "6 M", "1 day", "MIDPOINT", 0, 2, False, [])

    def historicalData(self, reqId, bar):
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])

    def historicalDataEnd(self, reqId, start, end):
        # Convert data to pandas DataFrame
        df = pd.DataFrame(self.data, columns=["date", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["date"], unit="s")
        df.set_index("date", inplace=True)

        # Calculate technical indicators
        df['12d_EMA'] = df['close'].ewm(span=12, adjust=False).mean()
        df['26d_EMA'] = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['12d_EMA'] - df['26d_EMA']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        current_data = df.iloc[-1]

        if current_data['MACD'] > current_data['Signal']:
            print("Buying")
            self.placeBuyOrder(reqId, Contract())
        elif current_data['MACD'] < current_data['Signal']:
            print("Selling")
            self.placeSellOrder(reqId, Contract())
        else:
            print("No trading signal")

    def placeBuyOrder(self, orderId, contract):
        # Create a buy order
        myorder = Order()
        myorder.orderId = orderId
        myorder.action = "BUY"
        myorder.orderType = "MKT"
        myorder.totalQuantity = 1

        # Place the buy order
        self.placeOrder(orderId, contract, myorder)

    def placeSellOrder(self, orderId, contract):
        myorder = Order()
        myorder.orderId = orderId
        myorder.action = "SELL"
        myorder.orderType = "MKT"
        myorder.totalQuantity = 1

        self.placeOrder(orderId, contract, myorder)

app = TestApp()
app.connect("127.0.0.1", 7496, 1)
app.nextValidId(1)
app.run()