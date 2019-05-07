import frappe
from dateutil import parser
from frappe.model.rename_doc import rename_doc
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice as make_purchase_invoice,make_delivery_note
from dcl.inflow_import.stock import make_stock_entry
# from dcl.inflow_import import add_stocks
from dcl.inflow_import.buy import make_payment_request
from erpnext.accounts.doctype.payment_request.payment_request import make_payment_entry


def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '%.12f' % f
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))


def make_invoice(paid_items,sales_order_name,SI_dict):
    datepaid = SI_dict['DatePaid']
    if not datepaid:
        datepaid = SI_dict["OrderDate"]
    else:
        datepaid = parser.parse(datepaid)
    # print SI_dict["inflow_file"]
    pi = make_purchase_invoice(sales_order_name)
    pi.inflow_file = SI_dict["inflow_file"]
    pi.posting_date = datepaid.date()
    pi.posting_time = str(datepaid.time())
    pi.save()
    pi.submit()
    frappe.db.commit()
    # if status == "Paid":
    #     if sales_order_name:
    if pi.grand_total > 0.0:
        so = frappe.get_doc("Sales Order", sales_order_name)
        print "             Making Payment request. Per billed",so.per_billed
        # if flt(so.per_billed) != 100:
        payment_request = make_payment_request(dt="Sales Invoice", dn=pi.name, recipient_id="",
                                               submit_doc=True, mute_email=True, use_dummy_message=True,
                                               inflow_file=SI_dict["inflow_file"],grand_total=pi.rounded_total,
                                               posting_date=datepaid.date(), posting_time=str(datepaid.time()))

        if SI_dict["PaymentStatus"] != "Invoiced":
            payment_entry = frappe.get_doc(make_payment_entry(payment_request.name))
            payment_entry.posting_date = datepaid.date()
            payment_entry.posting_time = str(datepaid.time())
            payment_entry.set_posting_time = 1
            # print "             ",pi.rounded_total,payment_entry.paid_amount
            if SI_dict["PaymentStatus"] == "Paid":
                payment_entry.paid_amount = pi.rounded_total

            else:
                payment_entry.paid_amount = float(SI_dict["AmountPaid"])
            payment_entry.inflow_file = SI_dict["inflow_file"]
            payment_entry.submit()
            frappe.db.commit()


def make_delivery(fulfilled_items,current_order,SI_dict):
    dn = make_delivery_note(current_order)
    dn.set_posting_time = 1
    dn.inflow_file = SI_dict["inflow_file"]
    datepaid = SI_dict['DatePaid']
    if not datepaid:
        datepaid = SI_dict["OrderDate"]
    else:
        datepaid = parser.parse(datepaid)
    dn.posting_date = datepaid.date()
    dn.posting_time = str(datepaid.time())
    dn.save()
    dn.submit()

#dcl.inflow_import.import_buy.start_import
def start_import(file):
    import csv
    import os
    current_customer = ""
    current_order = ""
    SI_dict = {}
    last_single_SI_dict = {}
    SI_items = []
    last_single_SI_items = []
    paid_and_fulfilled_items = []
    last_single_paid_and_fulfilled_items = []
    fulfilled_items = []
    last_single_fulfilled_items = []
    paid_items = []
    unpaid_items = []
    last_single_paid_items = []
    paid_pi = {}
    # input_file = csv.DictReader(open(os.path.dirname(os.path.abspath(__file__))+'/data/inFlow_PurchaseOrder_test.csv'))
    input_file = csv.DictReader(open(os.path.dirname(os.path.abspath(__file__))+'/data/'+file))

    # current_customer = input_file[0]["Customer"]

    income_accounts = "5111 - Cost of Goods Sold - DCL"
    # income_accounts = "Sales - J"
    cost_centers = "Main - DCL"
    # cost_centers = "Main - J"

    rows = list(input_file)
    total_paid = 0.0
    last_single_total_paid = 0.0
    # print rows
    totalrows = len(rows) - 1
    for i,row in enumerate(rows):
        # print row

        if row["InventoryStatus"] == "Quote":
            continue

        if row["InventoryStatus"] == "Unfulfilled" and row["PaymentStatus"] == "Uninvoiced":
            continue

        skip_rows = ["SO-002811","SO-002812","SO-001720","SO-001721",
                     "SO-002106","SO-002439","SO-002933","SO-002823","SO-002917"]
        if row["OrderNumber"] in skip_rows:
            continue

        if row["Location"].strip():
            if row["Location"].strip() == "DCL House, Plot 1299 Fumilayo Ransome Kuti Way, Area 3, PMB 690 Garki, Abuja":
                to_warehouse = "DCLWarehouse - Abuja - DCL"
            elif row[
                "Location"].strip() == "DCL Laboratory Products Ltd, Plot 5 Block 4 Etal Avenue off Kudirat Abiola Way by NNPC Lagos NG":
                to_warehouse = "Lagos Warehouse - DCL"
            else:
                to_warehouse = row["Location"].strip() + " - DCL"
        else:
            to_warehouse = ""
            #make item non stock
            item_code1 = row["ItemName"].strip()
            if "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser." in item_code1:
                item_code1 = "Kerosene Stove"
                # elif "X-Annual comprehensive maintenance service of selectra analyzer located at St Mary's Catholic Hospital Gwagwalada.FCT Abuja" in item_code1:
                #     item_code1 = "X-Annual comprehensive maintenance service"
            elif "X-Annual comprehensive maintenance service" in item_code1:
                item_code1 = "X-Annual comprehensive maintenance service"
            frappe.db.sql("""UPDATE `tabItem` SET is_stock_item=1 WHERE item_code=%s""", (item_code1))
            frappe.db.commit()
            to_warehouse = "DCLWarehouse - Abuja - DCL"


        if row["Location"].strip():
            exists_cat = frappe.db.sql("""SELECT Count(*) FROM `tabWarehouse` WHERE warehouse_name=%s""", (row["Location"].strip()))
            # print exists_cat, row["Location"]
            if exists_cat[0][0] == 0:
                item_code = row["Location"]
                SI = frappe.get_doc({"doctype": "Warehouse",
                           "warehouse_name": item_code.strip()
                           })
                SI_created = SI.insert(ignore_permissions=True)
                frappe.db.commit()


        item_code1 = row["ItemName"].strip()
        # if row[
        #     "ItemName"] == "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser.\nSupplied specifically without top plate (ring) for use only with the autoclave / steam sterilizer.":
        if "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser." in item_code1:
            item_code1 = "Kerosene Stove"
        # elif "X-Annual comprehensive maintenance service of selectra analyzer located at St Mary's Catholic Hospital Gwagwalada.FCT Abuja" in item_code1:
        #     item_code1 = "X-Annual comprehensive maintenance service"
        elif "X-Annual comprehensive maintenance service" in item_code1:
            item_code1 = "X-Annual comprehensive maintenance service"
        exists_cat = frappe.db.sql("""SELECT Count(*) FROM `tabItem`
              WHERE item_code=%s or item_code=%s""", (item_code1,row["ItemDescription"].strip()))
        # print "                --------------------------------              "
        # print row
        # print exists_cat, item_code1, row["ItemDescription"]
        if exists_cat[0][0] == 0:
            SI = frappe.get_doc({"doctype": "Item",
                       "item_code": item_code1 or row["ItemDescription"].strip(),
                       "description": row["ItemDescription"].strip() or item_code1,
                       # "item_group": row["Category"].strip() + " Category"
                       "item_group": "All Item Groups"
                       })
            SI_created = SI.insert(ignore_permissions=True)
            frappe.db.commit()


        #CREATE SUPPLIER IF NOT EXISTS
        exists_supplier = frappe.db.sql("""SELECT Count(*) FROM `tabCustomer` WHERE name=%s""",(row["Customer"].strip()))
        if exists_supplier[0][0] == 0:
            frappe.get_doc({"doctype":"Customer","customer_name":row["Customer"].strip(),
                            "customer_group":"All Customer Groups","customer_type":"Company"}).insert()
            frappe.db.commit()





        if i==0:
            current_customer = row["Customer"].strip()
            current_order = row["OrderNumber"]
            dt = parser.parse(row["OrderDate"])
            currency = ""
            conversion_rate = 0.0
            if float(row["ExchangeRate"]) != 0.0 and float(row["ExchangeRate"]) != 1.0:
                currency = row["CurrencyCode"]
                conversion_rate = float(row["ExchangeRate"]) * 100000.00
            elif float(row["ExchangeRate"]) == 0.0 or float(row["ExchangeRate"]) == 1.0:
                currency = "NGN"
                conversion_rate = 0.0

            delivery_date = None
            if row["OrderDate"]:
                dt2 = parser.parse(row["OrderDate"])
                delivery_date = dt2.date()
            else:
                dt2 = None

            SI_dict = {"doctype": "Sales Order",
                       "title": current_customer,
                       "customer": current_customer,
                       "posting_date": dt.date(),
                       "schedule_date": dt.date(),  # TODO + 30 days
                       "transaction_date": dt.date(),
                       "due_date": delivery_date,
                       "delivery_date": delivery_date,
                       "items": SI_items,
                       "docstatus": 1,
                       "outstanding_amount": total_paid,
                       "name": row["OrderNumber"],
                       "OrderDate":dt,
                       "DatePaid":row["DatePaid"],
                       "inflow_remarks":row["OrderRemarks"],
                       "inflow_file":file,
                       "currency": currency,
                       "conversion_rate":conversion_rate,
                       "inflow_salesrep": row["SalesRep"],
                       "inflow_sales_person": row["Sales Person"],
                       "disable_rounded_total": 1,
                       "AmountPaid": row["AmountPaid"],
                       "PaymentStatus":row["PaymentStatus"]
                       }
        # print(current_customer,row["Vendor"],totalrows)
        print "                                  ",totalrows,i
        if current_customer != row["Customer"].strip() or current_customer != row["Customer"].strip() \
                or current_order!= row["OrderNumber"] or totalrows == i:


            if totalrows == i and current_customer == row["Customer"]:
                # print "LAST ROW!"
                item_code1 = row["ItemName"].strip()
                # if row[
                #     "ItemName"] == "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser.\nSupplied specifically without top plate (ring) for use only with the autoclave / steam sterilizer.":
                if "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser." in item_code1:
                    item_code1 = "Kerosene Stove"
                    # elif "X-Annual comprehensive maintenance service of selectra analyzer located at St Mary's Catholic Hospital Gwagwalada.FCT Abuja" in item_code1:
                    #     item_code1 = "X-Annual comprehensive maintenance service"
                elif "X-Annual comprehensive maintenance service" in item_code1:
                    item_code1 = "X-Annual comprehensive maintenance service"

                # print row["ItemName"]
                SI_item = {
                    # "item_code": installment.item,  # test
                    "description": row["ItemDescription"].strip() or row["ItemName"],
                    "item_name": item_code1,
                    "item_code": item_code1,
                    # "rate": truncate(float(row["ItemSubtotal"]),2),
                    "rate": truncate(float(row["ItemUnitPrice"]),2),
                    "price_list_rate": truncate(float(row["ItemUnitPrice"]),2),
                    "conversion_factor": 1,
                    "uom": "Nos",
                    "expense_account": income_accounts,
                    "cost_center": cost_centers,
                    "qty": row["ItemQuantity"],
                    # "warehouse":row["Location"].strip() +" - DCL",
                    "warehouse":to_warehouse,
                    "InventoryStatus":row["InventoryStatus"],
                    "PaymentStatus":row["PaymentStatus"],
                    "OrderDate":row["OrderDate"]
                }
                SI_items.append(SI_item)

                if row["PaymentStatus"] not in ["Quote", "Uninvoiced"]:
                    paid_items.append({
                        # "item_code": installment.item,  # test
                        "description": row["ItemDescription"].strip() or row["ItemName"],
                        "item_name": item_code1,
                        "item_code": item_code1,
                        # "rate": truncate(float(row["ItemSubtotal"]),2),
                        "rate": truncate(float(row["ItemUnitPrice"]), 2),
                        "conversion_factor": 1,
                        "uom": "Nos",
                        "expense_account": income_accounts,
                        "cost_center": cost_centers,
                        "qty": abs(float(row["ItemQuantity"])),
                        # "warehouse": row["Location"].strip() + " - DCL",
                        "warehouse": to_warehouse,
                        "Location": to_warehouse,
                        "OrderDate": row["OrderDate"],
                        "DatePaid": row["DatePaid"],
                        "InventoryStatus": row["InventoryStatus"],
                        "PaymentStatus": row["PaymentStatus"]
                    })


                if row["InventoryStatus"] == "Fulfilled":
                    fulfilled_items.append({
                        "description": row["ItemDescription"].strip() or row["ItemName"],
                        "item_name": item_code1,
                        "item_code": item_code1,
                        "rate": truncate(float(row["ItemUnitPrice"]), 2),
                        "conversion_factor": 1,
                        "uom": "Nos",
                        "expense_account": income_accounts,
                        "cost_center": cost_centers,
                        "qty": abs(float(row["ItemQuantity"])),
                        # "warehouse": row["Location"].strip() + " - DCL",
                        "warehouse": to_warehouse,
                        "Location": to_warehouse,
                        "OrderDate": row["OrderDate"],
                        "DatePaid": row["DatePaid"],
                        "InventoryStatus": row["InventoryStatus"],
                        "PaymentStatus": row["PaymentStatus"]
                    })

                total_paid += float(row["ItemSubtotal"])

            elif totalrows == i:




                # print "LAST SINGLE ROW!"
                item_code1 = row["ItemName"].strip()
                # if row[
                #     "ItemName"] == "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser.\nSupplied specifically without top plate (ring) for use only with the autoclave / steam sterilizer.":
                if "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser." in item_code1:
                    item_code1 = "Kerosene Stove"
                    # elif "X-Annual comprehensive maintenance service of selectra analyzer located at St Mary's Catholic Hospital Gwagwalada.FCT Abuja" in item_code1:
                    #     item_code1 = "X-Annual comprehensive maintenance service"
                elif "X-Annual comprehensive maintenance service" in item_code1:
                    item_code1 = "X-Annual comprehensive maintenance service"
                last_single_SI_items.append({
                    # "item_code": installment.item,  # test
                    "description": row["ItemDescription"].strip() or row["ItemName"],
                    "item_name": item_code1,
                    "item_code": item_code1,
                    # "rate": truncate(float(row["ItemSubtotal"]),2),
                    "rate": truncate(float(row["ItemUnitPrice"]), 2),
                    "price_list_rate": truncate(float(row["ItemUnitPrice"]), 2),
                    "conversion_factor": 1,
                    "uom": "Nos",
                    "expense_account": income_accounts,
                    "cost_center": cost_centers,
                    "qty": abs(float(row["ItemQuantity"])),
                    # "warehouse":row["Location"].strip() +" - DCL",
                    "warehouse": to_warehouse,
                    "Location": to_warehouse,
                    "InventoryStatus": row["InventoryStatus"],
                    "PaymentStatus": row["PaymentStatus"],
                    "OrderDate": row["OrderDate"]
                })
                # print last_single_SI_items
                delivery_date = None
                if row["OrderDate"]:
                    dt2 = parser.parse(row["OrderDate"])
                    delivery_date = dt2.date()
                else:
                    dt2 = None
                dt = parser.parse(row["OrderDate"])
                if delivery_date < dt.date(): #Issue on Inflow SO-001000
                    # print "                          Issue SO-001000:", dt.date(), delivery_date
                    delivery_date = dt.date()
                last_single_SI_dict = {"doctype": "Sales Order",
                           "title": current_customer,
                           "customer": current_customer,
                           "posting_date": dt.date(),
                           "schedule_date": dt.date(),  # TODO + 30 days
                           "transaction_date": dt.date(),
                           "due_date": delivery_date,
                           "delivery_date": delivery_date,
                           "items": last_single_SI_items,
                           "docstatus": 1,
                           "outstanding_amount": total_paid,
                           "name": row["OrderNumber"],
                           "OrderDate": dt,
                           "DatePaid": row["DatePaid"],
                           "inflow_remarks": row["OrderRemarks"],
                           "inflow_file": file,
                           "currency": currency,
                           "conversion_rate": conversion_rate,
                           "inflow_salesrep": row["SalesRep"],
                            "inflow_sales_person": row["Sales Person"],
                           "disable_rounded_total": 1,
                           "AmountPaid": row["AmountPaid"],
                           "PaymentStatus": row["PaymentStatus"]
                           }

                if row["PaymentStatus"] not in ["Quote", "Uninvoiced"]:
                    last_single_paid_items.append({
                        # "item_code": installment.item,  # test
                        "description": row["ItemDescription"].strip() or row["ItemName"],
                        "item_name": item_code1,
                        "item_code": item_code1,
                        # "rate": truncate(float(row["ItemSubtotal"]),2),
                        "rate": truncate(float(row["ItemUnitPrice"]), 2),
                        "conversion_factor": 1,
                        "uom": "Nos",
                        "expense_account": income_accounts,
                        "cost_center": cost_centers,
                        "qty": abs(float(row["ItemQuantity"])),
                        # "warehouse": row["Location"].strip() + " - DCL",
                        "warehouse": to_warehouse,
                        "Location": to_warehouse,
                        "InventoryStatus": row["InventoryStatus"],
                        "PaymentStatus": row["PaymentStatus"]
                    })


                if row["InventoryStatus"] == "Fulfilled":
                    last_single_fulfilled_items.append({
                        "description": row["ItemDescription"].strip() or row["ItemName"],
                        "item_name": item_code1,
                        "item_code": item_code1,
                        "rate": truncate(float(row["ItemUnitPrice"]), 2),
                        "conversion_factor": 1,
                        "uom": "Nos",
                        "expense_account": income_accounts,
                        "cost_center": cost_centers,
                        "qty": abs(float(row["ItemQuantity"])),
                        # "warehouse": row["Location"].strip() + " - DCL",
                        "warehouse": to_warehouse,
                        "Location": to_warehouse,
                        "OrderDate": row["OrderDate"],
                        "DatePaid": row["DatePaid"],
                        "InventoryStatus": row["InventoryStatus"],
                        "PaymentStatus": row["PaymentStatus"]
                    })

                last_single_total_paid += float(row["ItemSubtotal"])


            SI_dict.update({"outstanding_amount":total_paid,
                            "inflow_file":file})


            SI = frappe.get_doc(SI_dict)
            # print SI_dict
            print("                     CURRENT:",current_order,SI_dict["inflow_salesrep"],SI_dict["inflow_sales_person"])
            SI_created = SI.insert(ignore_permissions=True)


            for item in SI_dict["items"]:
                datepaid = SI_dict['DatePaid']
                if not datepaid:
                    datepaid = SI_dict["OrderDate"]
                else:
                    datepaid = parser.parse(datepaid)
                # pi.posting_date = datepaid.date()
                # pi.posting_time = str(datepaid.time())
                make_stock_entry(item_code=item["item_code"], qty=item['qty'],
                                 to_warehouse=item["warehouse"],
                                 valuation_rate=1, remarks="This is affected by data import. " + file,
                                 posting_date=datepaid.date(),
                                 posting_time=str(datepaid.time()),
                                 set_posting_time=1, inflow_file=file)
                frappe.db.commit()




            frappe.db.commit()
            #/home/jvfiel/frappe-v11/apps/frappe/frappe/model/rename_doc.py
            rename_doc("Sales Order",SI_created.name,current_order,force=True)
            frappe.db.commit()

            if paid_items:
               make_invoice(paid_items,current_order,SI_dict)

            if fulfilled_items:
                make_delivery(fulfilled_items, current_order, SI_dict)



            current_customer = row["Customer"].strip()
            current_order = row["OrderNumber"]
            dt = parser.parse(row["OrderDate"])
            SI_items = []

            currency = ""
            conversion_rate = 0.0
            if float(row["ExchangeRate"]) != 0.0 and float(row["ExchangeRate"]) != 1.0:
                currency = row["CurrencyCode"]
                conversion_rate = float(row["ExchangeRate"]) * 100000.00
            elif float(row["ExchangeRate"]) == 0.0 or float(row["ExchangeRate"]) == 1.0:
                currency = "NGN"
                conversion_rate = 0.0

            delivery_date = None
            if row["OrderDate"]:
                dt2 = parser.parse(row["OrderDate"])
                delivery_date = dt2.date()
            else:
                dt2 = None
            SI_dict = {"doctype": "Sales Order",
                       "title": current_customer,
                       "customer": current_customer,
                       "posting_date": dt.date(),
                       "schedule_date": dt.date(),  # TODO + 30 days
                       "transaction_date": dt.date(),
                       # "due_date": row["DueDate"],
                       "items": SI_items,
                       "docstatus": 1,
                       "outstanding_amount": total_paid,
                       "name": row["OrderNumber"],
                       "OrderDate":dt,
                       "DatePaid": row["DatePaid"],
                       "inflow_remarks": row["OrderRemarks"],
                       "inflow_file":file,
                       "currency": currency,
                       "conversion_rate": conversion_rate,
                       "due_date": delivery_date,
                       "delivery_date": delivery_date,
                       "inflow_salesrep": row["SalesRep"],
                       "inflow_sales_person": row["Sales Person"],
                       "disable_rounded_total": 1,
                       "AmountPaid": row["AmountPaid"],
                       "PaymentStatus": row["PaymentStatus"]
                       }
            paid_items = []
            fulfilled_items = []
            paid_and_fulfilled_items = []


        # else:
        item_code1 = row["ItemName"].strip()
        # if row[
        #     "ItemName"] == "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser.\nSupplied specifically without top plate (ring) for use only with the autoclave / steam sterilizer.":
        if "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser." in item_code1:
            item_code1 = "Kerosene Stove"
            # elif "X-Annual comprehensive maintenance service of selectra analyzer located at St Mary's Catholic Hospital Gwagwalada.FCT Abuja" in item_code1:
            #     item_code1 = "X-Annual comprehensive maintenance service"
        elif "X-Annual comprehensive maintenance service" in item_code1:
            item_code1 = "X-Annual comprehensive maintenance service"

        unitprice = 0.0
        if row["ItemUnitPrice"]:
            unitprice = float(row["ItemUnitPrice"])
        SI_item = {
            # "item_code": installment.item,  # test
            "description": row["ItemDescription"].strip() or row["ItemName"],
            "item_name": item_code1,
            "item_code": item_code1,
            # "warehouse": row["Location"].strip() +" - DCL",
            "warehouse": to_warehouse,
            # "rate": float(row["ItemUnitPrice"]),
            "rate": unitprice,
            "price_list_rate":unitprice,
            "conversion_factor":1,
            "uom":"Nos",
            "expense_account": income_accounts,
            "cost_center": cost_centers,
            "qty": abs(float(row["ItemQuantity"])),
            "InventoryStatus": row["InventoryStatus"],
            "PaymentStatus": row["PaymentStatus"],
            "OrderDate":row["OrderDate"]
        }
        SI_items.append(SI_item)


        if row["PaymentStatus"] not in ["Quote","Uninvoiced"]:
            paid_items.append({
                "description": row["ItemDescription"].strip() or row["ItemName"],
                "item_name": item_code1,
                "item_code": item_code1,
                "rate": truncate(unitprice, 2),
                "price_list_rate": truncate(unitprice, 2),
                "conversion_factor": 1,
                "uom": "Nos",
                "expense_account": income_accounts,
                "cost_center": cost_centers,
                "qty": abs(float(row["ItemQuantity"])),
                "warehouse": to_warehouse,
                "Location": to_warehouse,
                "InventoryStatus": row["InventoryStatus"],
                "PaymentStatus": row["PaymentStatus"]
            })



        if row["InventoryStatus"] == "Fulfilled":
            fulfilled_items.append({
                "description": row["ItemDescription"].strip() or row["ItemName"],
                "item_name": item_code1,
                "item_code": item_code1,
                # "rate": truncate(float(row["ItemUnitPrice"]), 2),
                "rate": truncate(unitprice, 2),
                "price_list_rate": truncate(unitprice, 2),
                "conversion_factor": 1,
                "uom": "Nos",
                "expense_account": income_accounts,
                "cost_center": cost_centers,
                "qty": abs(float(row["ItemQuantity"])),
                # "warehouse": row["Location"].strip() + " - DCL",
                "warehouse": to_warehouse,
                "Location": to_warehouse,
                "OrderDate": row["OrderDate"],
                "DatePaid": row["DatePaid"],
                "InventoryStatus": row["InventoryStatus"],
                "PaymentStatus": row["PaymentStatus"]
            })

        total_paid +=float(row["ItemSubtotal"])

    SI_dict = last_single_SI_dict
    if last_single_SI_dict != {}:

        # print "* END *", current_order
        # print last_single_SI_dict["items"]
        SI = frappe.get_doc(last_single_SI_dict)
        # print SI_dict
        # print last_single_SI_dict

        for item in last_single_SI_dict["items"]:
            datepaid = SI_dict['DatePaid']
            if not datepaid:
                datepaid = SI_dict["OrderDate"]
            else:
                datepaid = parser.parse(datepaid)
            # pi.posting_date = datepaid.date()
            # pi.posting_time = str(datepaid.time())
            make_stock_entry(item_code=item["item_code"], qty=item['qty'],
                             to_warehouse=item["warehouse"],
                             valuation_rate=1, remarks="This is affected by data import. " + file,
                             posting_date=datepaid.date(),
                             posting_time=str(datepaid.time()),
                             set_posting_time=1, inflow_file=file)
            frappe.db.commit()


        SI_created = SI.insert(ignore_permissions=True)
        frappe.db.commit()
        SI_created.submit()
        frappe.db.commit()
        rename_doc("Sales Order", SI_created.name, current_order, force=True)
        frappe.db.commit()

        if last_single_paid_items:
            make_invoice(last_single_paid_items,current_order,SI_dict)

        if last_single_fulfilled_items:
            make_delivery(last_single_fulfilled_items,current_order,SI_dict)

    None


def remove_imported_data(file,force=0):

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
        if counter >= stop:
            print "Commit"
            frappe.db.commit()
            counter = 0
        counter += 1
        print counter

    if force == 1:
        SIs = frappe.db.sql("""SELECT name FROM `tabDelivery Note`""")
    else:
        SIs = frappe.db.sql("""SELECT name FROM `tabDelivery Note` WHERE inflow_file=%s""", (file))

    for i,si in enumerate(SIs):
        si_doc = frappe.get_doc("Delivery Note", si[0])
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
        SIs = frappe.db.sql("""SELECT name FROM `tabSales Invoice`""")
    else:
        SIs = frappe.db.sql("""SELECT name FROM `tabSales Invoice` WHERE inflow_file=%s""",(file))


    for i,si in enumerate(SIs):
        si_doc = frappe.get_doc("Sales Invoice",si[0])
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
        SIs = frappe.db.sql("""SELECT name FROM `tabSales Order`""")
    else:
        SIs = frappe.db.sql("""SELECT name FROM `tabSales Order` WHERE inflow_file=%s""",(file))

    for i,si in enumerate(SIs):
        si_doc = frappe.get_doc("Sales Order", si[0])
        if si_doc.docstatus == 1:
            si_doc.cancel()
        si_doc.delete()
        if counter >= stop:
            print "Commit"
            frappe.db.commit()
            counter = 0
        counter += 1
        print counter