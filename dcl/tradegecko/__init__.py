import frappe
from dcl.tradegecko.tradegecko import TradeGeckoRestClient
from frappe.model.rename_doc import rename_doc
from erpnext.buying.doctype.purchase_order.purchase_order \
    import make_purchase_invoice,make_purchase_receipt as make_delivery_note
from dcl.inflow_import import make_payment_request
from erpnext.accounts.doctype.payment_request.payment_request import make_payment_entry
from datetime import timedelta


def test_currency():
    # from openexchangerates import OpenExchangeRatesClient
    # client = OpenExchangeRatesClient('f6a4266347d544f59348bdf1f1a04a05')
    # print client.historical(frappe.utils.get_datetime().date(),'GHS')
    # import PyCurrency_Converter
    # PyCurrency_Converter.convert(1,'USD', 'GHS')
    # from fixerio import Fixerio

    from dcl.tradegecko.fixerio import Fixerio
    fxrio = Fixerio(access_key='88581fe5b1c9f21dbb6f90ba6722d11c', base='GHS')
    currency_rate = fxrio.historical_rates(frappe.utils.get_datetime().date())  # ['rates'][currency['iso']]
    print currency_rate

def make_delivery(fulfilled_items,current_order,datepaid):
    #against_sales_order

    exists_si = frappe.db.sql("""SELECT Count(*) FROM `tabDelivery Note` INNER JOIN
                                              `tabDelivery Note Item`
                                              ON `tabDelivery Note`.name=`tabDelivery Note Item`.parent
                                              WHERE `tabDelivery Note`.docstatus =1
                                              AND `tabDelivery Note Item`.against_sales_order=%s""", (current_order))

    # print "exists dn", exists_si, current_order
    if exists_si[0][0] > 0:
        return None

    dn = make_delivery_note(current_order)
    dn.set_posting_time = 1
    dn.inflow_file = current_order
    # datepaid = SI_dict['DatePaid']
    # if not datepaid:
    #     datepaid = SI_dict["OrderDate"]
    # else:
    #     datepaid = parser.parse(datepaid)
    # print " ========================== SALES RETURN ============================"
    # print fulfilled_items
    remove_rows = []
    for dnr_item in dn.items:
        found = 0
        for i, item in enumerate(fulfilled_items):
            # print "                      ", dnr_item.item_code, item['item_code']
            if dnr_item.item_code == item['item_code']:
                found = 1
                del fulfilled_items[i]
                dnr_item.qty = round(float(item['quantity']))
        if found == 0:
            remove_rows.append(dnr_item)

    # print remove_rows
    for i, r in enumerate(remove_rows):
        # print "removing,", r.item_code
        dn.remove(r)
    dn.posting_date = datepaid.date()
    dn.posting_time = str(datepaid.time())
    if dn.items:
        dn.save()
        dn.submit()
    else:
        print "no items."

# bench --site dcl2 execute dcl.tradegecko.currencies
def currencies():
    access_token = "6daee46c0b4dbca8baac12dbb0e8b68e93934608c510bb41a770bbbd8c8a7ca5"
    refresh_token = "76098f0a7f66233fe97f160980eae15a9a7007a5f5b7b641f211748d58e583ea"
    # tg = TradeGeckoRestClient(access_token, refresh_token)
    tg = TradeGeckoRestClient(access_token)
    # print tg.company.all()['companies'][0]
    orders = tg.currency.all()['currencies']
    print orders

# status_map = {"draft":"Pending Approval","received":"Completed","active":"Completed"}
status_map = {"draft":0,"received":1,"active":1}

# bench --site dcl2 execute dcl.tradegecko.test_gecko
def gecko_po(page=1):


    # import currencylayer
    # exchange_rate = currencylayer.Client(access_key='dee20c4b0dde59d26379e22a82986cb3')
    # rates = exchange_rate.live_rates(base_currency="GHS")
    # print rates


    access_token = "6daee46c0b4dbca8baac12dbb0e8b68e93934608c510bb41a770bbbd8c8a7ca5"
    refresh_token = "76098f0a7f66233fe97f160980eae15a9a7007a5f5b7b641f211748d58e583ea"
    # tg = TradeGeckoRestClient(access_token, refresh_token)
    tg = TradeGeckoRestClient(access_token)
    # print tg.company.all()['companies'][0]
    orders = tg.purchase_order.all(page=page,limit=250)['purchase_orders']
    # orders = tg.purchase_order.filter(order_number="PO0002")['purchase_orders']

    # print orders
    income_accounts = "5111 - Cost of Goods Sold - DCL"
    # income_accounts = "Sales - J"
    cost_centers = "Main - DCL"
    # cost_centers = "Main - J"

    for o in orders:
        # if o["status"] == "draft" or o["status"] == "received": #draft,received
        # if o["status"] == "draft" or o["status"] == "active": #draft,received, active
        #     continue


        exists_po = frappe.db.sql("""SELECT Count(*) FROM `tabPurchase Order` WHERE name=%s""",(o['order_number']))
        if exists_po[0][0] > 0:
            continue

        print o

        remove_imported_data(o["order_number"])

        SI_items = []
        to_warehouse = tg.location.get(o['stock_location_id'])['location']
        currency = tg.currency.get(o['currency_id'])['currency']
        print currency
        exists_warehouse = frappe.db.sql("""SELECT Count(*) FROM `tabWarehouse` WHERE warehouse_name=%s""",
                                         (to_warehouse['label']))
        # print exists_cat, row["Location"]
        if exists_warehouse[0][0] == 0:
            # print "CREATE WAREHOUSE"
            # break
            frappe.get_doc({"doctype": "Warehouse",
                            "warehouse_name": to_warehouse['label']
                            }).insert(ignore_permissions=True)
            frappe.db.commit()

        from dateutil import parser
        created_at = parser.parse(o["created_at"])
        if o["received_at"]:
            received_at = parser.parse(o["received_at"])
        else:
            received_at = ""
        due_at = parser.parse(o["due_at"])


        procured_items = []
        # print o['purchase_order_line_item_ids']
        # print o['order_number']
        # line_items = tg.purchase_order_line_item.filter(purchase_order_id=o['order_number'])['purchase_order_line_items']
        line_items = tg.purchase_order_line_item.filter(purchase_order_id=o['id'])
        # print line_items
        line_items = line_items['purchase_order_line_items']
        for line_item in line_items:
            # line_item = tg.purchase_order_line_item.get(i)['purchase_order_line_item']
            # print line_item

            exists_cat = frappe.db.sql("""SELECT Count(*),item_code,item_name,description FROM `tabItem`
                        WHERE variant_id=%s""",
                                       (line_item['variant_id']))
            item_code = ""
            item_name = ""
            item_description = ""
            if exists_cat[0][0] == 0:
                variant = tg.variant.get(line_item['variant_id'])
                # print variant,line_item['variant_id']
                # print line_item
                if not variant:
                    variant = {'product_name':line_item['label'],'sku':line_item['label'],'description':line_item['label']}
                else:
                    variant = variant["variant"]
                # print variant
                import re
                clean_name = re.sub(r"[^a-zA-Z0-9]+", ' ', variant["product_name"])
                item_code = re.sub(r"[^a-zA-Z0-9]+", ' ', variant["sku"]) or clean_name
                item_name = clean_name
                if "X960 Pipettor tip Thermo Scientific Finntip Flex  Filter sterile, free from DNA, " \
                   "DNase and RNasein vacuum sealed sterilized tip racks polypropylene tip," in item_code:
                    item_code = "X960 Pipettor tip Thermo Scientific Finntip Flex Filter"
                if "X960 Pipettor tip Thermo Scientific Finntip Flex  Filter sterile, free from DNA, " \
                   "DNase and RNasein vacuum sealed sterilized tip racks polypropylene tip," in item_name:
                    item_name = "X960 Pipettor tip Thermo Scientific Finntip Flex Filter"

                if "Stericup-GV, 0.22 " in item_code:
                    item_code = "Stericup-GV"
                if "Stericup-GV, 0.22 " in item_name:
                    item_name = "Stericup-GV"

                item_description = variant["description"]

                find_item = frappe.db.sql("""SELECT Count(*),item_code,item_name,description FROM `tabItem`
                                       WHERE item_code=%s""",
                                           (item_code))
                if find_item[0][0] == 0:
                    item_dict = {"doctype": "Item",
                                                  "item_code": item_code,
                                                  "item_name": item_name,
                                                  "description": variant["description"] or variant["product_name"],
                                                  "item_group": "All Item Groups",
                                                  "variant_id":line_item['variant_id']
                                                  }
                    # print item_dict
                    create_item = frappe.get_doc(item_dict)
                    create_item.insert(ignore_permissions=True)
                    frappe.db.commit()
                else:
                    item_code = find_item[0][1]
                    item_name = find_item[0][2]
                    item_description = find_item[0][3]

            else:
                item_code = exists_cat[0][1]
                item_name = exists_cat[0][2]
                item_description = exists_cat[0][3]

            if line_item['procurement_id']:
                line_item.update({"item_code":item_code})
                procured_items.append(line_item)

            found_line = 0
            for exist_line_item in SI_items:
                if exist_line_item['item_code'] == item_code or \
                                exist_line_item['item_code'] == item_name:
                    found_line = 1
                    exist_line_item.update({"qty":round(float(exist_line_item["qty"])+float(line_item["quantity"]))})

            if not found_line:
                SI_item = {
                    "description": item_description,
                    "item_name": item_name,
                    "item_code": item_code,
                    "rate": line_item["price"],
                    "conversion_factor": 1,
                    "uom": "Nos",
                    "expense_account": income_accounts,
                    "cost_center": cost_centers,
                    "qty": round(float(line_item["quantity"])),
                    "warehouse": to_warehouse['label'] + " - DCL",  # Location
                    "OrderDate": o["created_at"]
                }
                # print SI_item
                SI_items.append(SI_item)
            else:
                if not SI_items:
                    SI_item = {
                        "description": item_description,
                        "item_name": item_name,
                        "item_code": item_code,
                        "rate": line_item["price"],
                        "conversion_factor": 1,
                        "uom": "Nos",
                        "expense_account": income_accounts,
                        "cost_center": cost_centers,
                        "qty": round(float(line_item["quantity"])),
                        "warehouse": to_warehouse['label'] + " - DCL",  # Location
                        "OrderDate": o["created_at"]
                    }
                    # print SI_item
                    SI_items.append(SI_item)
            # print SI_items


        supplier_company = tg.company.get(o['company_id'])['company']
        # print supplier_company

        # CREATE SUPPLIER IF NOT EXISTS
        exists_supplier = frappe.db.sql("""SELECT Count(*) FROM `tabSupplier` WHERE name=%s""", (supplier_company['name']))
        if exists_supplier[0][0] == 0:
            frappe.get_doc({"doctype": "Supplier", "supplier_name": supplier_company['name'],
                            "supplier_group": "All Supplier Groups", "supplier_type": "Company"}).insert()
            frappe.db.commit()

        # from forex_python.converter import CurrencyRates
        # import PyCurrency_Converter
        # c = CurrencyRates()
        # print currency['iso']
        # # currency_rate = c.get_rate(currency['iso'], 'GHC')
        # currency_rate = PyCurrency_Converter.convert(1, currency['iso'], 'GHC')

        # from xecd_rates_client import XecdClient
        # xecd = XecdClient('dcllaboratoryproductsltd694148295', '606sp0hi0kespeghmd41b3vus9')
        # currency_rate = xecd.historic_rate(str(created_at.date()), str(created_at.time()),currency['iso'], "GHS",1)
        # print currency_rate,str(created_at.date()),status_map[o["status"]]
        # try:
        # currency_rate = currency_rate['to']['GHS'][0]['mid']
        # except:
        #     print str((created_at-timedelta(days=1)).date())
        #     currency_rate = xecd.historic_rate(str((created_at-timedelta(days=1)).date()), str(created_at.time()), currency['iso'], "GHS", 1)
        #     print currency_rate
        #     currency_rate = currency_rate['to']['GHS'][0]['mid']
        from dcl.tradegecko.fixerio import Fixerio
        fxrio = Fixerio(access_key='88581fe5b1c9f21dbb6f90ba6722d11c',base=currency['iso'])
        currency_rate = fxrio.historical_rates(created_at.date())['rates']
        # print currency_rate['EUR'],currency['iso']
        # currency_rate = currency_rate[currency['iso']]
        currency_rate = currency_rate['GHS']

        SI_dict = {"doctype": "Purchase Order",
                   "title": supplier_company['name'],
                   "supplier": supplier_company['name'],
                   "posting_date": created_at.date(),
                   "schedule_date": created_at.date(),  # TODO + 30 days
                   "transaction_date": created_at.date(),
                   "items": SI_items,
                   "docstatus": status_map[o["status"]],
                   # "name": o["order_number"],
                   "due_date": due_at.date(),
                   "delivery_date": created_at.date(),
                   "inflow_file":o["order_number"],
                   "currency": currency['iso'],
                   "conversion_rate":currency_rate,
                   # "workflow_state":status_map[o["status"]]
                   }
        print "****************** Sales Invoice ******************"
        print o['order_number']
        # print SI_dict
        SI_created = frappe.get_doc(SI_dict).insert()
        rename_doc("Purchase Order", SI_created.name, o['order_number'], force=True)
        frappe.db.commit()
        # print procured_items
        # frappe.db.sql("""UPDATE `tabPurchase Order` SET workflow_state=%s WHERE name=%s""",(status_map[o["status"]],o['order_number']))
        # frappe.db.commit()
        if o['status'] != "draft":
            if procured_items:
                make_delivery(procured_items,o['order_number'],received_at)
            paid = 0
            if o['status'] == "received":
                paid = 1
                print "paid"
            else:
                print "unpaid"
            print o["order_number"]


            make_invoice(o["order_number"],created_at,paid)
        # break
            frappe.db.commit()

"""
Consumer Key: 6QFRVEGFH8ODSCDVPVSASMJ0JUWYLG
Consumer Secret: ONCAAWFW2ZWP6KHLXVAWPTNXSJXHAW
"""


# bench --site dcl2 execute dcl.tradegecko.test_xero
def test_xero():
    # from xero import Xero
    # from xero.auth import PublicCredentials
    consumer_key = "06RRGPYM4SJXFEMRODT6F0GYJ42UKA"
    # consumer_secret = "COMNDKTM2AU54WADYU1I1YVBBRE4ZL"
    # credentials = PublicCredentials(consumer_key, consumer_secret)
    # print credentials.url
    from xero import Xero
    from xero.auth import PrivateCredentials
    import os
    file = "privatekey.pem"
    with open(os.path.dirname(os.path.abspath(__file__)) + '/data/' + file) as keyfile:
        rsa_key = keyfile.read()
    # print rsa_key
    credentials = PrivateCredentials(consumer_key, rsa_key)
    xero = Xero(credentials)
    # print xero.invoices.all()
    print xero.contacts.all()

def remove_imported_data(file, force=0):


    stop = 10

    if force == 1:
        SIs = frappe.db.sql("""SELECT name,reference_no FROM `tabPayment Entry`""")
    else:
        SIs = frappe.db.sql("""SELECT name,reference_no FROM `tabPayment Entry` WHERE inflow_file=%s""", (file))

    counter = 0
    for i,si in enumerate(SIs):
        si_doc = frappe.get_doc("Payment Entry", si[0])
        print "removing: ", si_doc.name
        if si_doc.docstatus == 1:
            si_doc.cancel()
        si_doc.delete()

        si_doc = frappe.get_doc("Payment Request", si[1])
        if si_doc.docstatus == 1:
            si_doc.cancel()
        si_doc.delete()
        if counter == stop:
            print "commit!"
            frappe.db.commit()
            counter = 0
        counter += 1
        print counter

    if force == 1:
        SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Receipt`""")
    else:
        SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Receipt` WHERE inflow_file=%s""", (file))

    for i,si in enumerate(SIs):
        si_doc = frappe.get_doc("Purchase Receipt", si[0])
        print "removing: ", si_doc.name
        if si_doc.docstatus == 1:
            si_doc.cancel()
        si_doc.delete()
        if counter >= stop:
            print "Commit"
            frappe.db.commit()
            counter = 0
        counter += 1
        print counter

    if force == 1:
        SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Invoice`""")
    else:
        SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Invoice` WHERE inflow_file=%s""",(file))

    for i,si in enumerate(SIs):
        si_doc = frappe.get_doc("Purchase Invoice",si[0])
        print "removing: ", si_doc.name
        if si_doc.docstatus == 1:
            si_doc.cancel()
        si_doc.delete()
        if counter >= stop:
            print "Commit"
            frappe.db.commit()
            counter = 0
        counter += 1
        print counter

    if force == 1:
        SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Order`""")
    else:
        SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Order` WHERE inflow_file=%s""",(file))

    for i,si in enumerate(SIs):
        si_doc = frappe.get_doc("Purchase Order", si[0])
        print "removing: ", si_doc.name
        if si_doc.docstatus == 1:
            si_doc.cancel()
        si_doc.delete()
        if counter >= stop:
            print "Commit"
            frappe.db.commit()
            counter = 0
        counter += 1
        print counter

def make_invoice(sales_order_name,datepaid,paid=0):
    # print SI_dict["inflow_file"]

    pi = make_purchase_invoice(sales_order_name)
    pi.inflow_file = sales_order_name
    pi.set_posting_time = 1
    # datepaid = SI_dict['DatePaid']
    # if not datepaid:
    #     datepaid = SI_dict["OrderDate"]
    # else:
    #     datepaid = parser.parse(datepaid)
    pi.posting_date = datepaid.date()
    pi.posting_time = str(datepaid.time())
    pi.save()

    # if sales_order_name:

    if paid == 1:
        so = frappe.get_doc("Purchase Order", sales_order_name)
        # print "             Making Payment request. Per billed",so.per_billed
        # if flt(so.per_billed) != 100:
        payment_request = make_payment_request(dt="Purchase Order", dn=so.name, recipient_id="",
                                               submit_doc=True, mute_email=True, use_dummy_message=True,
                                               inflow_file=sales_order_name,
                                               posting_date=datepaid.date(),posting_time=str(datepaid.time()))

        payment_entry = frappe.get_doc(make_payment_entry(payment_request.name))
        # payment_entry.posting_date = frappe.flags.current_date
        payment_entry.posting_date = datepaid.date()
        payment_entry.posting_time = str(datepaid.time())
        payment_entry.set_posting_time = 1
        payment_entry.inflow_file = sales_order_name
        payment_entry.submit()

    pi.submit()
    frappe.db.commit()
