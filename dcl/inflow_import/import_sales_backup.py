import frappe
from datetime import datetime
from datetime import timedelta
from erpnext.stock.utils import get_stock_value_from_bin
from dateutil import parser
from dcl.inflow_import.stock import make_stock_entry
from frappe.model.rename_doc import rename_doc
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice


def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '%.12f' % f
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))


def add_stocks(items,file):
    for item in items:

        # if item["Location"] == "DCL House, Plot 1299 Fumilayo Ransome Kuti Way, Area 3, PMB 690 Garki, Abuja":
        #     to_warehouse = "DCLWarehouse - Abuja - DCL"
        # elif item[
        #     "Location"] == "DCL Laboratory Products Ltd, Plot 5 Block 4 Etal Avenue off Kudirat Abiola Way by NNPC Lagos NG - DCL":
        #     to_warehouse = "Lagos Warehouse - DCL"
        # else:
        to_warehouse = item["Location"]


        # def get_stock_value_from_bin(warehouse="DCLWarehouse - Abuja - DCL", item_code=item["item_code"]):
        bal = get_stock_value_from_bin(warehouse=to_warehouse, item_code=item["item_code"])
        print "          * * * * Check Bin * * * *"
        print "          " + str(bal[0][0]), item['qty']
        print "          " + item['item_code']
        date = None
        time = None
        if item["DatePaid"]:
            print "          ", item["DatePaid"].date(), item["DatePaid"].time()
            date = item["DatePaid"].date()
            time = item["DatePaid"].time()
        elif item["OrderDate"]:
            date = item["OrderDate"].date()
            time = item["OrderDate"].time()


        if bal[0][0] < item['qty'] or bal[0][0] == None or bal[0][0] == 0:
            diff = 0
            if bal[0][0] != None:
                diff = bal[0][0]
            make_stock_entry(item_code=item["item_code"], qty=abs(float(item["qty"]) - diff),
                             to_warehouse=to_warehouse,
                             valuation_rate=1, remarks="This is affected by data import. "+file,
                             posting_date=date,
                             posting_time=time,
                             set_posting_time=1,inflow_file = file)
            frappe.db.commit()
            print "Stock entry created."


#dcl.inflow_import.import_buy.start_import
def start_import(file):
    import csv
    import os
    current_customer = ""
    current_order = ""
    SI_dict = {}
    SI_items = []
    paid_and_fulfilled_items = []
    fulfilled_items = []
    paid_items = []
    # input_file = csv.DictReader(open(os.path.dirname(os.path.abspath(__file__))+'/data/inFlow_SalesOrder_test.csv'))
    input_file = csv.DictReader(open(os.path.dirname(os.path.abspath(__file__))+'/data/'+file))

    # current_customer = input_file[0]["Customer"]

    income_accounts = "5111 - Cost of Goods Sold - DCL"
    # income_accounts = "Sales - J"
    cost_centers = "Main - DCL"
    # cost_centers = "Main - J"

    rows = list(input_file)
    total_paid = 0.0
    # print rows
    totalrows = len(rows)
    for i,row in enumerate(rows):
        # print row

        if row["InventoryStatus"] == "Quote":
            pass

        if row["Location"].strip():
            if row[
                "Location"].strip() == "DCL House, Plot 1299 Fumilayo Ransome Kuti Way, Area 3, PMB 690 Garki, Abuja":
                to_warehouse = "DCLWarehouse - Abuja - DCL"
            elif row[
                "Location"].strip() == "DCL Laboratory Products Ltd, Plot 5 Block 4 Etal Avenue off Kudirat Abiola Way by NNPC Lagos NG - DCL":
                to_warehouse = "Lagos Warehouse - DCL"
            else:
                to_warehouse = row["Location"].strip() + " - DCL"
        else:
            to_warehouse = ""
            # make item non stock
            item_code1 = row["ItemName"].strip()
            frappe.db.sql("""UPDATE `tabItem` SET is_stock_item=1 WHERE item_code=%s""", (item_code1))
            frappe.db.commit()
            to_warehouse = "DCLWarehouse - Abuja - DCL"


        exists_cat = frappe.db.sql("""SELECT Count(*) FROM `tabWarehouse` WHERE warehouse_name=%s""", (row["Location"].strip()))
        # print exists_cat, row["Location"]
        if exists_cat[0][0] == 0:
            item_code = row["Location"]
            warehouse_dict = {"doctype": "Warehouse",
                       "warehouse_name": item_code.strip()
                       }
            SI = frappe.get_doc(warehouse_dict)
            SI.insert(ignore_permissions=True)
            frappe.db.commit()


        exists_cat = frappe.db.sql("""SELECT Count(*) FROM `tabItem` WHERE item_code=%s""", (row["ItemName"].strip()))
        # print exists_cat
        if exists_cat[0][0] == 0:
            item_code = row["ItemName"]
            if row["ItemName"] == "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser.\nSupplied specifically without top plate (ring) for use only with the autoclave / steam sterilizer.":
                item_code = "Kerosene Stove"
            item_dict = {"doctype": "Item",
                       "item_code": item_code.strip(),
                       "description": row["ItemDescription"],
                       # "item_group": row["Category"].strip() + " Category"
                       "item_group": "All Item Groups"
                       }
            SI = frappe.get_doc(item_dict)
            SI.insert(ignore_permissions=True)
            frappe.db.commit()


        #CREATE SUPPLIER IF NOT EXISTS
        exists_supplier = frappe.db.sql("""SELECT Count(*) FROM `tabCustomer` WHERE name=%s""",(row["Customer"]))
        if exists_supplier[0][0] == 0:
            frappe.get_doc({"doctype":"Customer","customer_name":row["Customer"],
                            "customer_group":"All Customer Groups","customer_type":"Company"}).insert()
            frappe.db.commit()









        if i==0:
            current_customer = row["Customer"]
            current_order = row["OrderNumber"]

            dt = parser.parse(row["OrderDate"])
            dt2 = parser.parse(row["OrderDate"])

            dt4 = parser.parse(row["DatePaid"])

            SI_dict = {"doctype": "Sales Order",
                       "title": current_customer,
                       "customer": current_customer,
                       "posting_date": dt.date(),
                       "delivery_date": dt2.date(),
                       "transaction_date": (dt).date(),
                       "due_date": dt2.date(),
                       "OrderDate": dt,
                       "DueDate": dt2.date(),
                       "DatePaid": dt4,
                       "items": SI_items,
                       "docstatus": 1,
                       # "outstanding_amount": total_paid,
                       "name": current_order,
                       "inflow_remarks": row["OrderRemarks"],
                       "currency":row["CurrencyCode"],
                       "conversion_rate": row["ExchangeRate"],
                       "inflow_file": file
                       }


        # print(current_customer,row["Vendor"],totalrows)
        if current_customer != row["Customer"] or current_customer != row["Customer"] or \
                                current_order != row["OrderNumber"] or totalrows-1 == i:


            if totalrows-1 == i:

                if row["OrderDate"]:
                    dt = parser.parse(row["OrderDate"])
                else:
                    dt = None
                delivery_date = None
                if row["OrderDate"]:
                    dt2 = parser.parse(row["OrderDate"])
                    delivery_date = dt2.date()
                else:
                    dt2 = None
                if row["InvoicedDate"]:
                    dt3 = parser.parse(row["InvoicedDate"])
                else:
                    dt3 = None
                # print "-------------", (row["DatePaid"])
                if row["DatePaid"]:
                    dt4 = parser.parse(row["DatePaid"])
                else:
                    dt4 = None

                if row["PaymentStatus"] == "Paid" and row["InventoryStatus"] == "Fulfilled":
                    paid_and_fulfilled_items.append({
                        # "item_code": installment.item,  # test
                        "description": row["ItemDescription"] or row["ItemName"],
                        "item_name": row["ItemName"],
                        "item_code": row["ItemName"],
                        "DatePaid": dt4,
                        "OrderDate": dt,
                        "InvoicedDate": dt3,
                        # "rate": truncate(float(row["ItemSubtotal"]),2),
                        "rate": truncate(float(row["ItemUnitPrice"]), 2),
                        "conversion_factor": 1,
                        "uom": "Nos",
                        "expense_account": income_accounts,
                        "cost_center": cost_centers,
                        "qty": row["ItemQuantity"],
                        # "warehouse": row["Location"].strip() + " - DCL",
                        "warehouse": to_warehouse,
                        "InventoryStatus": row["InventoryStatus"],
                        "PaymentStatus": row["PaymentStatus"]
                    })

                if row["PaymentStatus"] == "Paid" and row["InventoryStatus"] != "Fulfilled":
                    paid_items.append({
                        # "item_code": installment.item,  # test
                        "description": row["ItemDescription"] or row["ItemName"],
                        "item_name": row["ItemName"],
                        "item_code": row["ItemName"],
                        "DatePaid": dt4,
                        "OrderDate": dt,
                        "InvoicedDate": dt3,
                        # "rate": truncate(float(row["ItemSubtotal"]),2),
                        "rate": truncate(float(row["ItemUnitPrice"]), 2),
                        "conversion_factor": 1,
                        "uom": "Nos",
                        "expense_account": income_accounts,
                        "cost_center": cost_centers,
                        "qty": row["ItemQuantity"],
                        # "warehouse": row["Location"].strip() + " - DCL",
                        "warehouse": to_warehouse,
                        "InventoryStatus": row["InventoryStatus"],
                        "PaymentStatus": row["PaymentStatus"]
                    })

                if row["PaymentStatus"] != "Paid" and row["InventoryStatus"] == "Fulfilled":
                    fulfilled_items.append({
                        "description": row["ItemDescription"] or row["ItemName"],
                        "item_name": row["ItemName"],
                        "item_code": row["ItemName"],
                        "DatePaid": dt4,
                        "OrderDate": dt,
                        "InvoicedDate": dt3,
                        "rate": truncate(float(row["ItemUnitPrice"]), 2),
                        "conversion_factor": 1,
                        "uom": "Nos",
                        "expense_account": income_accounts,
                        "cost_center": cost_centers,
                        "qty": row["ItemQuantity"],
                        # "warehouse": row["Location"].strip() + " - DCL",
                        "warehouse": to_warehouse,
                        "InventoryStatus": row["InventoryStatus"],
                        "PaymentStatus": row["PaymentStatus"]
                    })

                if row["OrderDate"]:
                    dt2 = parser.parse(row["OrderDate"])
                    dt2 = dt2.date()
                else:
                    dt2 = None


                SI_item = {
                    # "item_code": installment.item,  # test
                    "description": row["ItemDescription"] or row["ItemName"],
                    "item_name": row["ItemName"],
                    "item_code": row["ItemName"],
                    # "warehouse": row["Location"].strip() + " - DCL",
                    "warehouse": to_warehouse,
                    "due_date": dt2,
                    "delivery_date": dt2,
                    "rate": float(row["ItemUnitPrice"]),
                    "conversion_factor": 1,
                    "uom": "Nos",
                    "expense_account": income_accounts,
                    "cost_center": cost_centers,
                    "qty": float(row["ItemQuantity"]),
                    "InventoryStatus": row["InventoryStatus"],
                    "PaymentStatus": row["PaymentStatus"]
                }
                SI_items.append(SI_item)

                total_paid += float(row["AmountPaid"])


            # print SI_items
            dt = parser.parse(row["OrderDate"])

            # SI_dict.update({"outstanding_amount":total_paid})


            # print(row["OrderDate"])
            # print SI_dict['items']
            SI = frappe.get_doc(SI_dict)
            # print SI_dict

            # print SI_dict
            # print "current order", current_order
            SI_created = SI.insert(ignore_permissions=True)
            frappe.db.commit()

            #/home/jvfiel/frappe-v11/apps/frappe/frappe/model/rename_doc.py
            rename_doc("Sales Order",SI_created.name,current_order,force=True)




            frappe.db.commit()
            if paid_and_fulfilled_items:
                # from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_invoice
                #/home/jvfiel/frappe-v11/apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.py
                pi = make_sales_invoice(current_order)
                pi.update_stock = 1
                # pi.is_paid = 1
                pi.is_pos = 1
                pi.items = []
                add_stocks(paid_and_fulfilled_items,file)
                for item in paid_and_fulfilled_items:
                    nl = pi.append('items', {})
                    nl.description = item["description"]
                    nl.item_name = item["item_name"]
                    nl.item_code = item["item_name"]
                    nl.rate = item["rate"]
                    nl.conversion_factor = item["conversion_factor"]
                    nl.uom = item["uom"]
                    nl.expense_account = item["expense_account"]
                    nl.cost_center = item["cost_center"]
                    nl.qty = item["qty"]
                    # nl.warehouse = item["warehouse"]
                    # nl.warehouse = "DCLWarehouse - Abuja - DCL"
                    nl.sales_order = current_order
                    pi.append("payments", {
                        "mode_of_payment": "Cash",
                        "amount": item["rate"] * float(item["qty"])
                    })
                # if pi.items:
                pi.cash_bank_account = "Access Bank - DCL"
                pi.taxes_and_charges = ""
                pi.taxes = []

                posting_date = None
                if SI_dict["DatePaid"]:
                    posting_date = SI_dict["DatePaid"]
                # elif SI_dict["OrderDate"]:
                #     posting_date = SI_dict["OrderDate"]
                else:
                    posting_date = SI_dict["OrderDate"]
                pi.posting_date = posting_date.date()

                pi.posting_time = str(posting_date.time())

                print "                  * * * Paid and Fulfilled * * *"
                print paid_and_fulfilled_items
                print "                  >>> ", current_order, pi.posting_date, pi.posting_time

                pi.set_posting_time = 1
                # pi.due_date = SI_dict["DueDate"]
                pi.due_date = posting_date.date()
                print "                 ",to_warehouse
                pi.insert()
                pi.inflow_file = file
                pi.submit()
                frappe.db.commit()
                #paid_and_fulfilled_items

            if paid_items:
                # from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_invoice
                pi = make_sales_invoice(current_order)
                # pi.update_stock = 1
                pi.is_paid = 1
                pi.is_pos = 1
                pi.items = []
                # add_stocks(paid_items)
                for item in paid_items:
                    nl = pi.append('items', {})
                    nl.description = item["description"]
                    nl.item_name = item["item_name"]
                    nl.item_code = item["item_name"]
                    nl.rate = item["rate"]
                    nl.conversion_factor = item["conversion_factor"]
                    nl.uom = item["uom"]
                    nl.expense_account = item["expense_account"]
                    nl.cost_center = item["cost_center"]
                    nl.qty = item["qty"]
                    # nl.warehouse = item["warehouse"]
                    # nl.warehouse = "DCLWarehouse - Abuja - DCL"
                    nl.sales_order = current_order
                    pi.append("payments", {
                        "mode_of_payment": "Cash",
                        "amount": item["rate"] *float(item["qty"])
                    })
                # if pi.items:
                pi.cash_bank_account = "Access Bank - DCL"
                pi.taxes_and_charges = ""
                pi.taxes = []

                pi.posting_date = SI_dict["DatePaid"]
                pi.set_posting_time = 1
                # pi.transaction_date = SI_dict["DatePaid"]
                pi.due_date = SI_dict["DatePaid"]
                # pi.po_date = SI_dict["DatePaid"]
                pi.inflow_file = file
                pi.insert()
                pi.submit()
                frappe.db.commit()


            if fulfilled_items:
                # from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_invoice
                pi = make_sales_invoice(current_order)
                pi.update_stock = 1
                # pi.is_paid = 1
                add_stocks(fulfilled_items,file)
                pi.items = []
                for item in fulfilled_items:
                    nl = pi.append('items', {})
                    nl.description = item["description"]
                    nl.item_name = item["item_name"]
                    nl.item_code = item["item_name"]
                    nl.rate = item["rate"]
                    nl.conversion_factor = item["conversion_factor"]
                    nl.uom = item["uom"]
                    nl.expense_account = item["expense_account"]
                    nl.cost_center = item["cost_center"]
                    nl.qty = item["qty"]
                    # nl.warehouse = item["warehouse"]
                    # nl.warehouse = "DCLWarehouse - Abuja - DCL"
                    nl.sales_order = current_order
                # if pi.items:
                pi.cash_bank_account = "Access Bank - DCL"
                pi.taxes_and_charges = ""
                pi.taxes = []

                # dt = parser.parse(row["OrderDate"])
                # dt2 = parser.parse(row["InvoicedDate"])
                # dt3 = parser.parse(row["DueDate"])
                # dt4 = parser.parse(row["DatePaid"])
                # pi.delivery_date = SI_dict["DatePaid"]
                pi.set_posting_time = 1
                pi.posting_date = SI_dict["DatePaid"]
                pi.set_posting_time = 1
                # pi.transaction_date = SI_dict["DatePaid"]
                pi.due_date = SI_dict["DatePaid"]
                # pi.po_date = SI_dict["DatePaid"]
                pi.inflow_file = file
                pi.insert()
                pi.submit()
                frappe.db.commit()



            current_customer = row["Customer"]
            current_order = row["OrderNumber"]


            dt = parser.parse(row["OrderDate"])
            delivery_date = None
            if row["OrderDate"]:
                dt2 = parser.parse(row["OrderDate"])
                delivery_date = dt2.date()
            else:
                dt2 = None
            # print "-------------",(row["DatePaid"])
            if row["DatePaid"]:
                dt4 = parser.parse(row["DatePaid"])
            else:
                dt4 = None
            #TODO: due date should be DueDate if no DueDate then use OrderDate
            # pi.delivery_date = dt4.date()
            # pi.posting_date = dt4.date()
            # pi.transaction_date = dt4.date()
            # pi.due_date = dt4.date()

            SI_dict = {"doctype": "Sales Order",
                       "title": current_customer,
                       "customer": current_customer,
                       "posting_date": dt.date(),
                       # "delivery_date": dt2.date(),
                       "transaction_date": (dt).date(),
                       "due_date": delivery_date,
                       "DueDate": delivery_date,
                       "OrderDate": dt,
                       "DatePaid": dt4,
                       "items": SI_items,
                       "docstatus": 1,
                       # "outstanding_amount": total_paid,
                       "name": current_order,
                       "inflow_remarks":row["OrderRemarks"],
                       "inflow_file":file,
                       "currency": row["CurrencyCode"],
                       "conversion_rate": row["ExchangeRate"]
                       }

            paid_items = []
            fulfilled_items = []
            paid_and_fulfilled_items = []
            SI_items = []
            total_paid = 0.0


        # else:
        if row["OrderDate"]:
            dt = parser.parse(row["OrderDate"])
        else:
            dt = None
        delivery_date = None
        if row["OrderDate"]:
            dt2 = parser.parse(row["OrderDate"])
            delivery_date = dt2.date()
        else:
            dt2 = None
        if row["InvoicedDate"]:
            dt3 = parser.parse(row["InvoicedDate"])
        else:
            dt3 = None
        # print "-------------", (row["DatePaid"])
        if row["DatePaid"]:
            dt4 = parser.parse(row["DatePaid"])
        else:
            dt4 = None
        SI_items.append({
            # "item_code": installment.item,  # test
            "description": row["ItemDescription"] or row["ItemName"],
            "item_name": row["ItemName"],
            "item_code": row["ItemName"],
            # "warehouse": row["Location"].strip() +" - DCL",
            "warehouse": to_warehouse,
            "due_date": delivery_date,
            "delivery_date": delivery_date,
            "DatePaid": dt4,
            "OrderDate": dt,
            "InvoicedDate": dt3,
            "rate": float(row["ItemUnitPrice"]),
            "conversion_factor":1,
            "uom":"Nos",
            "expense_account": income_accounts,
            "cost_center": cost_centers,
            "qty": float(row["ItemQuantity"]),
            "InventoryStatus": row["InventoryStatus"],
            "PaymentStatus": row["PaymentStatus"]
        })

        if row["PaymentStatus"] == "Paid" and row["InventoryStatus"] == "Fulfilled":
            paid_and_fulfilled_items.append({
                # "item_code": installment.item,  # test
                "description": row["ItemDescription"] or row["ItemName"],
                "item_name": row["ItemName"],
                "item_code": row["ItemName"],
                "DatePaid": dt4,
                "OrderDate": dt,
                "InvoicedDate": dt3,
                # "rate": truncate(float(row["ItemSubtotal"]),2),
                "rate": truncate(float(row["ItemUnitPrice"]), 2),
                "conversion_factor": 1,
                "uom": "Nos",
                "expense_account": income_accounts,
                "cost_center": cost_centers,
                "qty": row["ItemQuantity"],
                # "warehouse": row["Location"].strip() + " - DCL",
                "warehouse": to_warehouse,
                "Location":to_warehouse,
                "InventoryStatus": row["InventoryStatus"],
                "PaymentStatus": row["PaymentStatus"]
            })

        if row["PaymentStatus"] == "Paid" and row["InventoryStatus"] != "Fulfilled":
            paid_items.append({
                # "item_code": installment.item,  # test
                "description": row["ItemDescription"] or row["ItemName"],
                "item_name": row["ItemName"],
                "item_code": row["ItemName"],
                "DatePaid": dt4,
                "OrderDate": dt,
                "InvoicedDate": dt3,
                # "rate": truncate(float(row["ItemSubtotal"]),2),
                "rate": truncate(float(row["ItemUnitPrice"]), 2),
                "conversion_factor": 1,
                "uom": "Nos",
                "expense_account": income_accounts,
                "cost_center": cost_centers,
                "qty": row["ItemQuantity"],
                # "warehouse": row["Location"].strip() + " - DCL",
                "warehouse": to_warehouse,
                "InventoryStatus": row["InventoryStatus"],
                "PaymentStatus": row["PaymentStatus"]
            })

        if row["PaymentStatus"] != "Paid" and row["InventoryStatus"] == "Fulfilled":
            fulfilled_items.append({
                "description": row["ItemDescription"] or row["ItemName"],
                "item_name": row["ItemName"],
                "item_code": row["ItemName"],
                "DatePaid": dt4,
                "OrderDate": dt,
                "InvoicedDate": dt3,
                "rate": truncate(float(row["ItemUnitPrice"]), 2),
                "conversion_factor": 1,
                "uom": "Nos",
                "expense_account": income_accounts,
                "cost_center": cost_centers,
                "qty": row["ItemQuantity"],
                # "warehouse": row["Location"].strip() + " - DCL",
                "warehouse": to_warehouse,
                "InventoryStatus": row["InventoryStatus"],
                "PaymentStatus": row["PaymentStatus"]
            })

        total_paid +=float(row["AmountPaid"])

    None

# def remove_imported_data(file):
#     SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Invoice` WHERE inflow_file=%s""",(file))
#
#     for si in SIs:
#         si_doc = frappe.get_doc("Purchase Invoice",si[0])
#         if si_doc.docstatus == 1:
#             si_doc.cancel()
#         si_doc.delete()
#
#     SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Order` WHERE inflow_file=%s""",(file))
#
#     for si in SIs:
#         si_doc = frappe.get_doc("Purchase Order", si[0])
#         if si_doc.docstatus == 1:
#             si_doc.cancel()
#         si_doc.delete()


def remove_imported_data(file):
    SIs = frappe.db.sql("""SELECT name FROM `tabSales Invoice` WHERE docstatus=1 and inflow_file=%s""",(file))

    for si in SIs:
        si_doc = frappe.get_doc("Sales Invoice",si[0])
        si_doc.cancel()
        si_doc.delete()

    SIs = frappe.db.sql("""SELECT name FROM `tabStock Entry` WHERE docstatus=1 and inflow_file=%s""",(file))

    for si in SIs:
        si_doc = frappe.get_doc("Stock Entry", si[0])
        si_doc.cancel()
        si_doc.delete()

    SIs = frappe.db.sql("""SELECT name FROM `tabSales Order` WHERE docstatus=1 and inflow_file=%s""",(file))

    for si in SIs:
        si_doc = frappe.get_doc("Sales Order", si[0])
        si_doc.cancel()
        si_doc.delete()