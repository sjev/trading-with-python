"""
@author: jev kuznetsov
 
Demonstrate submitting an combo order
 
As an example a three legged order of SPY,XLE and APPL is being submitted.
 
taken from IB Api example at 
https://www.interactivebrokers.com/en/software/api/apiguide/java/placing_a_combination_order.htm
 
"""

from time import sleep

from ib.ext.ComboLeg import ComboLeg
from ib.ext.Contract import Contract
from ib.opt import ibConnection
from ib.ext.Order import Order

# sign function
sign = lambda a: (a > 0) - (a < 0)


def createContract(symbol):
    """create contract object"""
    c = Contract()
    c.m_symbol = symbol
    c.m_secType = "STK"
    c.m_exchange = "SMART"
    c.m_currency = "USD"

    return c


def createOrder(orderId, shares, limit=None, transmit=0):
    """
    create order object

    Parameters
    -----------
    orderId : The order Id. You must specify a unique value.
              When the order status returns, it will be identified by this tag.
              This tag is also used when canceling the order.

    shares: number of shares to buy or sell. Negative for sell order.
    limit : price limit, None for MKT order
    transmit: transmit immideatelly from tws
    """

    action = {-1: "SELL", 1: "BUY"}

    o = Order()

    o.m_orderId = orderId
    o.m_action = action[sign(shares)]
    o.m_totalQuantity = abs(shares)
    o.m_transmit = transmit

    if limit is not None:
        o.m_orderType = "LMT"
        o.m_lmtPrice = limit
    else:
        o.m_orderType = "MKT"

    return o


class MessageHandler(object):
    """class for handling incoming messages"""

    def __init__(self, tws):
        """create class, provide ibConnection object as parameter"""
        self.nextValidOrderId = None

        tws.registerAll(self.debugHandler)
        tws.register(self.nextValidIdHandler, "NextValidId")
        tws.register(self.contractDetails, "ContractDetails")

        self.reqId = -1  # last request Id
        self.conId = None  # container for received contract details

    def contractDetails(self, msg):
        print("got cotract details:")

        self.reqId = msg.reqId
        self.conId = msg.contractDetails.m_summary.m_conId
        printFull(msg.contractDetails.m_summary)

    def nextValidIdHandler(self, msg):
        """handles NextValidId messages"""
        self.nextValidOrderId = msg.orderId

    def debugHandler(self, msg):
        """function to print messages"""
        print(msg)


def printFull(c):
    """prints full details of a conttract"""
    keys = [k for k in dir(c) if k[0] != "_"]

    for key in keys:
        print((key, getattr(c, key)))


# -----------Main script-----------------

if "tws" not in locals():  #
    tws = ibConnection()  # create connection object
    handler = MessageHandler(tws)  # message handling class

    tws.connect()  # connect to API

sleep(1)  # wait for nextOrderId to come in

orderId = handler.nextValidOrderId  # numeric order id, must be unique.
print(("Next valid order id: ", orderId))

# ----------------- create contracts
symbols = ["SPY", "XLE"]
contracts = [createContract(symbol) for symbol in symbols]


# ----------------- get contract data
contractIds = []
for requestId, contract in enumerate(contracts):
    print(("Requesting ", contract.m_symbol))
    tws.reqContractDetails(requestId, contract)
    sleep(1)  # wait for data to come in
    # safety check that request ids match
    assert handler.reqId == requestId, "Request and data do not match"
    contractIds.append(handler.conId)

# ------------create contract legs
# for simplicity, I just set each leg to buy 1 share
legs = []

for conId in contractIds:
    leg = ComboLeg()
    leg.m_conId = conId
    leg.m_ratio = 1
    leg.m_action = "BUY"
    leg.m_exchange = "SMART"

    legs.append(leg)

# -------- create a contract with required legs
contract = Contract()

contract.m_symbol = "USD"
contract.m_secType = "BAG"
contract.m_exchange = "SMART"
contract.m_currency = "USD"
contract.m_comboLegs = legs

# ----- create and place order
print("Placing order")
order = createOrder(orderId, shares=1)  # create order

tws.placeOrder(orderId, contract, order)  # place order


sleep(1)  # wait before disconnecting

print("All done")

tws.disconnect()
