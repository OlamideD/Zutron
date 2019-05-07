import os

from endpoints import Company, Address, Variant, Product, \
    Order, Composition, Location, PurchaseOrder, PurchaseOrderLineItem, \
    StockTransfer, StockTransferLineItem,OrderLineItem, Invoice, InvoiceLineItem, \
    Fulfillment,FulfillmentLineItem, Currency,User

import logging
logger = logging.getLogger(__name__)


class TradeGeckoRestClient(object):

    def __init__(self, access_token=None):
        self.access_token = access_token or os.environ.get("TRADEGECKO_ACCESS_TOKEN", None)
        self.base_uri = os.environ.get("TRADEGECKO_API_URI", 'https://api.tradegecko.com/')

        if not access_token:
            raise Exception("No TG access token. Pass into client constructor or set env var TRADEGECKO_ACCESS_TOKEN")

        # Endpoints
        self.company = Company(self.base_uri, self.access_token)
        self.user = User(self.base_uri, self.access_token)
        self.address = Address(self.base_uri, self.access_token)
        self.location = Location(self.base_uri, self.access_token)
        self.variant = Variant(self.base_uri, self.access_token)
        self.product = Product(self.base_uri, self.access_token)
        self.currency = Currency(self.base_uri, self.access_token)
        self.order = Order(self.base_uri, self.access_token)
        self.order_line_item = OrderLineItem(self.base_uri, self.access_token)
        self.invoice = Invoice(self.base_uri, self.access_token)
        self.invoice_line_item = InvoiceLineItem(self.base_uri, self.access_token)
        self.fulfillment = Fulfillment(self.base_uri, self.access_token)
        self.fulfillment_line_item = FulfillmentLineItem(self.base_uri, self.access_token)
        self.purchase_order = PurchaseOrder(self.base_uri, self.access_token)
        self.purchase_order_line_item = PurchaseOrderLineItem(self.base_uri, self.access_token)
        self.composition = Composition(self.base_uri, self.access_token)
        self.stocktransfer = StockTransfer(self.base_uri, self.access_token)
        self.stocktransferlineitem = StockTransferLineItem(self.base_uri, self.access_token)