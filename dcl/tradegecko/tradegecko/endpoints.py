from api import ApiEndpoint


class Composition(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(Composition, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'variants/%s/composition'
        self._data_name = 'variants'


class Company(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(Company, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'companies/%s'
        self.required_fields = ['name', 'company_type']
        self._data_name = 'company'

class User(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(User, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'users/%s'
        # self.required_fields = ['name', 'company_type']
        self._data_name = 'users'


class Address(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(Address, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'addresses/%s'
        self.required_fields = ['company_id', 'label']
        self._data_name = 'address'


class Location(ApiEndpoint):
    def __init__(self, base_data, access_token):
        super(Location, self).__init__(base_data, access_token)
        self.uri = self.base_uri + 'locations/%s'
        self.required_fields = ['label']
        self._data_name = 'location'


class PurchaseOrder(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(PurchaseOrder, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'purchase_orders/%s'
        self.required_fields = ['company_id', 'stock_location_id']
        self._data_name = 'purchase_order'


class PurchaseOrderLineItem(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(PurchaseOrderLineItem, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'purchase_order_line_items/%s'
        self.required_fields = ['variant_id', 'quantity', 'price', 'purchase_order_id']
        self._data_name = 'purchase_order_line_item'

class OrderLineItem(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(OrderLineItem, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'order_line_items/%s'
        # self.required_fields = ['variant_id', 'quantity', 'price', 'purchase_order_id']
        self._data_name = 'order_line_item'

class Invoice(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(Invoice, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'invoices/%s'
        # self.required_fields = ['variant_id', 'quantity', 'price', 'purchase_order_id']
        self._data_name = 'invoice'

class InvoiceLineItem(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(InvoiceLineItem, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'invoice_line_items/%s'
        # self.required_fields = ['variant_id', 'quantity', 'price', 'purchase_order_id']
        self._data_name = 'invoice_line_item'

class Fulfillment(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(Fulfillment, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'fulfillments/%s'
        # self.required_fields = ['variant_id', 'quantity', 'price', 'purchase_order_id']
        self._data_name = 'fulfillment'

class FulfillmentLineItem(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(FulfillmentLineItem, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'fulfillment_line_items/%s'
        # self.required_fields = ['variant_id', 'quantity', 'price', 'purchase_order_id']
        self._data_name = 'fulfillment_line_item'

class Variant(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(Variant, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'variants/%s'
        self._data_name = 'variants'

class Currency(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(Currency, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'currencies/%s'
        self._data_name = 'currencies'

class Product(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(Product, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'products/%s'
        self._data_name = 'products'


class Order(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(Order, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'orders/%s'
        self._data_name = 'order'


class StockTransfer(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(StockTransfer, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'stock_transfer/%s'
        # self.required_fields = ['company_id', 'stock_location_id']
        self._data_name = 'stock_transfer'

class StockTransferLineItem(ApiEndpoint):
    def __init__(self, base_uri, access_token):
        super(StockTransferLineItem, self).__init__(base_uri, access_token)
        self.uri = self.base_uri + 'stock_transfer_line_item/%s'
        # self.required_fields = ['variant_id', 'quantity', 'price', 'purchase_order_id']
        self._data_name = 'stock_transfer_line_item'