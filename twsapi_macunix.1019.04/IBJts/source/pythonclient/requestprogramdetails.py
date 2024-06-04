from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import *


class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId: int):
        # Define the Ethereum (ETH) contract
        contract = Contract()
        contract.symbol = "ETH"
        contract.secType = "CRYPTO"
        contract.exchange = "PAXOS"
        contract.currency = "USD"

        # Request market data for Ethereum (ETH)
        self.reqMarketDataType(4)
        self.reqMktData(orderId, contract, "", 0, 0, [])

    def tickPrice(self, reqId, tickType, price, attrib):
        # Handle price updates
        print(
            f"tickPrice. reqId: {reqId}, tickType: {tickType}, price: {price}, attribs: {attrib}")

        # Place a buy order for Ethereum (ETH) when the price is received
        if tickType == 4:  # Last price
            self.placeBuyOrder(reqId, price)

    def placeBuyOrder(self, orderId, price):
        # Create a buy order for Ethereum (ETH) based on the current price
        buy_order = Order("BUY", 1)
        # buy_order.action = "BUY"
        # buy_order.orderType = "MKT"
        # buy_order.totalQuantity = 1  # You can adjust the quantity as needed
        # buy_order.transmit = True
        # # buy_order.exchange = ""  # Set exchange to an empty string for cryptocurrencies

        # Place the buy order
        self.placeOrder(orderId, Contract(), buy_order)


# Create an instance of TestApp
app = TestApp()

# Connect to TWS or IB Gateway
app.connect("127.0.0.1", 7496, 1000)

# Start the message loop
app.run()
