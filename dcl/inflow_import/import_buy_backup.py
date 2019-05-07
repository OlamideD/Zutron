import frappe
from dateutil import parser
from frappe.model.rename_doc import rename_doc
from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_invoice
from dcl.inflow_import.stock import make_stock_entry


def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '%.12f' % f
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))


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

        if row["Location"].strip():
            if row["Location"].strip() == "DCL House, Plot 1299 Fumilayo Ransome Kuti Way, Area 3, PMB 690 Garki, Abuja":
                to_warehouse = "DCLWarehouse - Abuja - DCL"
            elif row[
                "Location"].strip() == "DCL Laboratory Products Ltd, Plot 5 Block 4 Etal Avenue off Kudirat Abiola Way by NNPC Lagos NG - DCL":
                to_warehouse = "Lagos Warehouse - DCL"
            else:
                to_warehouse = row["Location"].strip() + " - DCL"
        else:
            to_warehouse = ""
            #make item non stock
            item_code1 = row["ItemName"].strip()
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
        exists_cat = frappe.db.sql("""SELECT Count(*) FROM `tabItem` WHERE item_code=%s""", (item_code1))
        # print exists_cat
        if exists_cat[0][0] == 0:
            SI = frappe.get_doc({"doctype": "Item",
                       "item_code": item_code1,
                       "description": row["ItemDescription"],
                       # "item_group": row["Category"].strip() + " Category"
                       "item_group": "All Item Groups"
                       })
            SI_created = SI.insert(ignore_permissions=True)
            frappe.db.commit()


        #CREATE SUPPLIER IF NOT EXISTS
        exists_supplier = frappe.db.sql("""SELECT Count(*) FROM `tabSupplier` WHERE name=%s""",(row["Vendor"].strip()))
        if exists_supplier[0][0] == 0:
            frappe.get_doc({"doctype":"Supplier","supplier_name":row["Vendor"].strip(),
                            "supplier_group":"All Supplier Groups","supplier_type":"Company"}).insert()
            frappe.db.commit()





        if i==0:
            current_customer = row["Vendor"].strip()
            current_order = row["OrderNumber"]
            dt = parser.parse(row["OrderDate"])
            currency = ""
            conversion_rate = 0.0
            if float(row["ExchangeRate"]) != 0.0 and float(row["ExchangeRate"]) != 1.0:
                currency = row["CurrencyCode"]
                conversion_rate = float(row["ExchangeRate"])
            elif float(row["ExchangeRate"]) == 0.0 or float(row["ExchangeRate"]) == 1.0:
                currency = "NGN"
                conversion_rate = 0.0

            po_status = ""
            if row["InventoryStatus"] == "Fulfilled" and row["PaymentStatus"] == "Paid":
                po_status = "Completed"
            elif row["InventoryStatus"] == "Unfulfilled" and row["PaymentStatus"] == "Paid":
                po_status = "To Receive"
            elif row["InventoryStatus"] == "Fulfilled" and row["PaymentStatus"] == "Unpaid":
                po_status = "To Bill"
            SI_dict = {"doctype": "Purchase Order",
                       "title": current_customer,
                       "supplier": current_customer,
                       "posting_date": dt.date(),
                       "schedule_date": dt.date(),  # TODO + 30 days
                       "transaction_date": dt.date(),
                       # "due_date": row["DueDate"],
                       "po_status":po_status,
                       "due_date": dt.date(),
                       "items": SI_items,
                       # "docstatus": 1,
                       "outstanding_amount": total_paid,
                       "name": row["OrderNumber"],
                       "OrderDate":dt,
                       "inflow_remarks":row["OrderRemarks"],
                       "inflow_file":file,
                       "currency": currency,
                       "conversion_rate":conversion_rate
                       }
        # print(current_customer,row["Vendor"],totalrows)
        print "                                  ",totalrows,i
        if current_customer != row["Vendor"].strip() or current_customer != row["Vendor"].strip() \
                or current_order!= row["OrderNumber"] or totalrows == i:


            if totalrows == i and current_customer == row["Vendor"]:
                print "LAST ROW!"
                item_code1 = row["ItemName"].strip()
                # if row[
                #     "ItemName"] == "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser.\nSupplied specifically without top plate (ring) for use only with the autoclave / steam sterilizer.":
                if "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser." in item_code1:
                    item_code1 = "Kerosene Stove"

                print row["ItemName"]
                SI_item = {
                    # "item_code": installment.item,  # test
                    "description": row["ItemDescription"].strip() or row["ItemName"],
                    "item_name": item_code1,
                    "item_code": item_code1,
                    # "rate": truncate(float(row["ItemSubtotal"]),2),
                    "rate": truncate(float(row["ItemUnitPrice"]),2),
                    "conversion_factor": 1,
                    "uom": "Nos",
                    "expense_account": income_accounts,
                    "cost_center": cost_centers,
                    "qty": float(row["ItemQuantity"]),
                    "received_qty": float(row["ItemQuantity"]),
                    # "warehouse":row["Location"].strip() +" - DCL",
                    "warehouse":to_warehouse,
                    "InventoryStatus":row["InventoryStatus"],
                    "PaymentStatus":row["PaymentStatus"],
                    "OrderDate":row["OrderDate"]
                }
                SI_items.append(SI_item)

                if row["PaymentStatus"] == "Paid" and row["InventoryStatus"] == "Fulfilled":
                    paid_and_fulfilled_items.append({
                        # "item_code": installment.item,  # test
                        "description": row["ItemDescription"] or row["ItemName"],
                        "item_name": item_code1,
                        "item_code": item_code1,
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
                        "item_name": item_code1,
                        "item_code": item_code1,
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
                        "item_name": item_code1,
                        "item_code": item_code1,
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

                total_paid += float(row["ItemSubtotal"])

            elif totalrows == i:




                print "LAST SINGLE ROW!"
                item_code1 = row["ItemName"].strip()
                # if row[
                #     "ItemName"] == "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser.\nSupplied specifically without top plate (ring) for use only with the autoclave / steam sterilizer.":
                if "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser." in item_code1:
                    item_code1 = "Kerosene Stove"
                last_single_SI_items.append({
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
                    "qty": row["ItemQuantity"],
                    # "warehouse":row["Location"].strip() +" - DCL",
                    "warehouse": to_warehouse,
                    "InventoryStatus": row["InventoryStatus"],
                    "PaymentStatus": row["PaymentStatus"],
                    "OrderDate": row["OrderDate"]
                })
                print last_single_SI_items
                last_single_SI_dict = {"doctype": "Purchase Order",
                                       "title": current_customer,
                                       "supplier": current_customer,
                                       "posting_date": dt.date(),
                                       "schedule_date": dt.date(),  # TODO + 30 days
                                       "transaction_date": dt.date(),
                                       # "due_date": row["DueDate"],
                                       "due_date": dt.date(),
                                       "items": last_single_SI_items,
                                       # "docstatus": 1,
                                       "outstanding_amount": total_paid,
                                       "name": row["OrderNumber"],
                                       "OrderDate": dt,
                                       "inflow_remarks": row["OrderRemarks"],
                                       "currency": currency,
                                       "conversion_rate": conversion_rate,
                                       "inflow_file":file
                                       }

                if row["PaymentStatus"] == "Paid" and row["InventoryStatus"] == "Fulfilled":
                    last_single_paid_and_fulfilled_items.append({
                        # "item_code": installment.item,  # test
                        "description": row["ItemDescription"] or row["ItemName"],
                        "item_name": item_code1,
                        "item_code": item_code1,
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
                    last_single_paid_items.append({
                        # "item_code": installment.item,  # test
                        "description": row["ItemDescription"] or row["ItemName"],
                        "item_name": item_code1,
                        "item_code": item_code1,
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
                    last_single_fulfilled_items.append({
                        "description": row["ItemDescription"] or row["ItemName"],
                        "item_name": item_code1,
                        "item_code": item_code1,
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

                last_single_total_paid += float(row["ItemSubtotal"])


            SI_dict.update({"outstanding_amount":total_paid,
                            "inflow_file":file,
                            "per_received":100.0,
                            "per_billed":100.0
                            })

            print SI_dict["items"]
            SI = frappe.get_doc(SI_dict)
            # print SI_dict
            print("                     CURRENT:",current_order,SI_dict["po_status"])
            SI_created = SI.insert(ignore_permissions=True)
            SI_created.submit()
            """
            To Receive and Bill
            To Bill
            To Receive
            Completed
            """
            # print "                   PO Status: ",SI_dict["po_status"]
            # if SI_dict["po_status"] == "To Receive and Bill":
            #     print "To Receive and Bill"
            #     SI_created.db_set("per_received", 100, update_modified=False)
            #     SI_created.db_set("per_billed", 100, update_modified=False)
            # elif SI_dict["po_status"] == "To Receive":
            #     print "To Receive"
            #     SI_created.db_set("per_billed", 100, update_modified=False)
            # if SI_dict["po_status"] == "To Bill":
            #     print "To Bill"
            #     SI_created.db_set("per_received", 100, update_modified=False)


            # SI_created.status = SI_dict["po_status"]
            frappe.db.commit()
            #/home/jvfiel/frappe-v11/apps/erpnext/erpnext/buying/doctype/purchase_order/purchase_order.py
            from erpnext.buying.doctype.purchase_order.purchase_order import update_status


            #/home/jvfiel/frappe-v11/apps/frappe/frappe/model/rename_doc.py
            rename_doc("Purchase Order",SI_created.name,current_order,force=True)
            frappe.db.commit()

            # update_status(SI_dict["po_status"], current_order)
            # SI_created.set_status(update=True, status=SI_dict["po_status"])

            #self.db_set('status', self.status, update_modified = update_modified)
            # SI_created.db_set(fieldname='status',value=SI_dict['po_status'])
            # frappe.db.sql("""UPDATE `tabPurchase Order` SET status=%s WHERE name=%s""",(SI_dict["po_status"],current_order),debug=1)
            #self.db_set("per_received", flt(received_qty / total_qty) * 100, update_modified=False)
            # frappe.db.commit()

            print paid_and_fulfilled_items
            if paid_and_fulfilled_items:
                pi = make_purchase_invoice(current_order)
                if to_warehouse:
                    pi.update_stock = 1
                pi.is_paid = 1
                pi.items = []
                pi.posting_date = SI_dict['OrderDate'].date()
                pi.posting_time = str(SI_dict['OrderDate'].time())
                pi_total = 0.0
                if float(SI_dict["conversion_rate"]) != 0.0 and float(SI_dict["conversion_rate"]) != 1.0:
                    pi.currency = SI_dict["currency"]
                    pi.conversion_rate = float(SI_dict["conversion_rate"])
                elif float(SI_dict["conversion_rate"]) == 0.0 or float(SI_dict["conversion_rate"]) == 1.0:
                    pi.currency = "NGN"
                    pi.conversion_rate = None
                zeros = []
                for item in paid_and_fulfilled_items:
                    # if float(item["rate"]) < 0:
                    #     zeros.append(item)
                    # else:
                    nl = pi.append('items', {})
                    nl.description = item["description"]
                    nl.item_name = item["item_name"]
                    nl.item_code = item["item_name"]
                    nl.rate = float(item["rate"])
                    # nl.base_rate = float(item["rate"])
                    nl.conversion_factor = item["conversion_factor"]
                    nl.uom = item["uom"]
                    nl.expense_account = item["expense_account"]
                    nl.cost_center = item["cost_center"]
                    nl.qty = float(item["qty"])
                    nl.warehouse = item["warehouse"]
                    nl.purchase_order = current_order
                    pi_total += float(nl.rate) * float(nl.qty)
                    print(nl.rate)
                # if pi.items:
                pi.set_posting_time = 1
                pi.cash_bank_account = "Access Bank - DCL"
                pi.taxes_and_charges = ""
                pi.taxes = []
                pi.inflow_file = file
                print "             ", paid_and_fulfilled_items
                print "             Paid and Fulfilled PI Total", pi_total,current_order,pi.currency
                # print "             ", pi.as_dict()["items"]
                if pi_total:
                    pi.mode_of_payment = "Cash"
                    # if pi.conversion_rate:
                    # print "<<<<",pi.grand_total,">>>>"
                    # print "<<<<",pi.conversion_rate,">>>>"
                    # print "<<<<",pi.grand_total * pi.conversion_rate,">>>>"
                    pi.paid_amount = pi.grand_total
                    pi.base_paid_amount = pi.outstanding_amount
                    pi.insert()
                    pi.save()
                    frappe.db.commit()
                    pi.submit()
                    frappe.db.commit()
                else:
                    for item in zeros:
                        make_stock_entry(item_code=item["item_code"], qty=item['qty'],
                                         to_warehouse=item["warehouse"],
                                         valuation_rate=1, remarks="This is affected by data import. " + file,
                                         posting_date=pi.posting_date,
                                         posting_time=pi.posting_time,
                                         set_posting_time=1, inflow_file=file)
                        frappe.db.commit()
                        print "Stock entry created."

            if paid_items:
                pi = make_purchase_invoice(current_order)
                # pi.update_stock = 1
                pi.is_paid = 1
                pi.items = []
                pi.posting_date = SI_dict['OrderDate'].date()
                pi.posting_time = str(SI_dict['OrderDate'].time())
                pi_total = 0.0
                if float(SI_dict["conversion_rate"]) != 0.0 and float(SI_dict["conversion_rate"]) != 1.0:
                    pi.currency = SI_dict["currency"]
                    pi.conversion_rate = float(SI_dict["conversion_rate"])
                elif float(SI_dict["conversion_rate"]) == 0.0 or float(SI_dict["conversion_rate"]) == 1.0:
                    pi.currency = "NGN"
                    pi.conversion_rate = None
                zeros = []
                for item in paid_items:
                    nl = pi.append('items', {})
                    nl.description = item["description"]
                    nl.item_name = item["item_name"]
                    nl.item_code = item["item_name"]
                    nl.rate = float(item["rate"])
                    nl.conversion_factor = item["conversion_factor"]
                    nl.uom = item["uom"]
                    nl.expense_account = item["expense_account"]
                    nl.cost_center = item["cost_center"]
                    nl.qty = float(item["qty"])
                    nl.warehouse = item["warehouse"]
                    nl.purchase_order = current_order

                    pi_total += float(nl.rate) * float(nl.qty)
                # if pi.items:
                pi.set_posting_time = 1
                pi.cash_bank_account = "Access Bank - DCL"
                pi.taxes_and_charges = ""
                pi.taxes = []
                pi.inflow_file = file
                print "             Paid Items:", paid_items
                print "             Paid Items Only PI Total", pi_total,current_order,pi.currency
                # print "             ", pi.as_dict()["items"]
                if pi_total:
                    pi.mode_of_payment = "Cash"
                    pi.insert()
                    frappe.db.commit()
                    if pi.currency != "NGN":
                        pi.paid_amount = pi.grand_total
                        pi.base_paid_amount = pi.outstanding_amount
                        pi.save()
                        frappe.db.commit()
                    pi.submit()
                    frappe.db.commit()
                else:
                    pass


            if fulfilled_items:
                pi = make_purchase_invoice(current_order)
                if to_warehouse:
                    pi.update_stock = 1
                # pi.is_paid = 1
                pi.items = []
                pi.posting_date = SI_dict['OrderDate'].date()
                pi.posting_time = str(SI_dict['OrderDate'].time())
                pi_total = 0.0
                if float(SI_dict["conversion_rate"]) != 0.0 and float(
                        SI_dict["conversion_rate"]) != 1.0:
                    pi.currency = SI_dict["currency"]
                    pi.conversion_rate = float(SI_dict["conversion_rate"])
                elif float(SI_dict["conversion_rate"]) == 0.0 or float(
                        SI_dict["conversion_rate"]) == 1.0:
                    pi.currency = "NGN"
                    pi.conversion_rate = None
                zeros = []
                for item in fulfilled_items:
                    nl = pi.append('items', {})
                    nl.description = item["description"]
                    nl.item_name = item["item_name"]
                    nl.item_code = item["item_name"]
                    nl.rate = float(item["rate"])
                    nl.conversion_factor = item["conversion_factor"]
                    nl.uom = item["uom"]
                    nl.expense_account = item["expense_account"]
                    nl.cost_center = item["cost_center"]
                    nl.qty = float(item["qty"])
                    nl.received_qty = float(item["qty"])
                    nl.warehouse = item["warehouse"]
                    nl.purchase_order = current_order

                    pi_total += abs(float(nl.rate) * float(nl.qty))
                    # print nl.rate
                # if pi.items:
                pi.set_posting_time = 1
                pi.cash_bank_account = "Access Bank - DCL"
                pi.taxes_and_charges = ""
                pi.taxes = []
                pi.inflow_file = file
                print "             ", fulfilled_items
                print "             Fulfilled Items Only PI Total", pi_total, current_order, pi.currency
                print "             conversion rate", pi.conversion_rate
                if pi_total:
                    pi.mode_of_payment = "Cash"
                    pi.insert()
                    frappe.db.commit()
                    if pi.currency != "NGN":
                        # pi.paid_amount = pi.grand_total
                        # pi.base_paid_amount = pi.outstanding_amount
                        pi.rounding_adjustment = 0.0
                        pi.disable_rounded_total = 1
                        pi.save()
                        frappe.db.commit()
                    pi.submit()
                    frappe.db.commit()
                else:
                    pass




            current_customer = row["Vendor"].strip()
            current_order = row["OrderNumber"]
            dt = parser.parse(row["OrderDate"])
            SI_items = []

            currency = ""
            conversion_rate = 0.0
            if float(row["ExchangeRate"]) != 0.0 and float(row["ExchangeRate"]) != 1.0:
                currency = row["CurrencyCode"]
                conversion_rate = float(row["ExchangeRate"])
            elif float(row["ExchangeRate"]) == 0.0 or float(row["ExchangeRate"]) == 1.0:
                currency = "NGN"
                conversion_rate = 0.0

            po_status = ""
            if row["InventoryStatus"] == "Fulfilled" and row["PaymentStatus"] == "Paid":
                po_status = "Completed"
            elif row["InventoryStatus"] == "Unfulfilled" and row["PaymentStatus"] == "Paid":
                po_status = "To Receive"
            elif row["InventoryStatus"] == "Fulfilled" and row["PaymentStatus"] == "Unpaid":
                po_status = "To Bill"
            SI_dict = {"doctype": "Purchase Order",
                       "title": current_customer,
                       "supplier": current_customer,
                       "posting_date": dt.date(),
                       "schedule_date": dt.date(),  # TODO + 30 days
                       "transaction_date": dt.date(),
                       # "due_date": row["DueDate"],
                       "po_status":po_status,
                       "due_date": dt.date(),
                       "items": SI_items,
                       # "docstatus": 1,
                       "outstanding_amount": total_paid,
                       "name": row["OrderNumber"],
                       "OrderDate":dt,
                       "inflow_remarks": row["OrderRemarks"],
                       "inflow_file": file,
                       "currency": currency,
                       "conversion_rate": conversion_rate
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
        SI_item = {
            # "item_code": installment.item,  # test
            "description": row["ItemDescription"].strip() or row["ItemName"],
            "item_name": item_code1,
            "item_code": item_code1,
            # "warehouse": row["Location"].strip() +" - DCL",
            "warehouse": to_warehouse,
            "rate": float(row["ItemUnitPrice"]),
            "conversion_factor":1,
            "uom":"Nos",
            "expense_account": income_accounts,
            "cost_center": cost_centers,
            "qty": float(row["ItemQuantity"]),
            "received_qty": float(row["ItemQuantity"]),
            "InventoryStatus": row["InventoryStatus"],
            "PaymentStatus": row["PaymentStatus"],
            "OrderDate":row["OrderDate"]
        }
        SI_items.append(SI_item)

        if row["PaymentStatus"] == "Paid" and row["InventoryStatus"] == "Fulfilled":
            paid_and_fulfilled_items.append({
                # "item_code": installment.item,  # test
                "description": row["ItemDescription"] or row["ItemName"],
                "item_name": item_code1,
                "item_code": item_code1,
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
                "item_name": item_code1,
                "item_code": item_code1,
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
                "item_name": item_code1,
                "item_code": item_code1,
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

        total_paid +=float(row["ItemSubtotal"])



    if last_single_SI_dict != {}:

        print "* END *", current_order
        print last_single_SI_dict["items"]
        SI = frappe.get_doc(last_single_SI_dict)
        # print SI_dict
        SI_created = SI.insert(ignore_permissions=True)
        frappe.db.commit()
        SI_created.submit()
        frappe.db.commit()
        rename_doc("Purchase Order", SI_created.name, current_order, force=True)
        frappe.db.commit()
        if last_single_paid_and_fulfilled_items:
            pi = make_purchase_invoice(current_order)
            pi.update_stock = 1
            pi.is_paid = 1
            pi.items = []
            pi.posting_date = SI_dict['OrderDate'].date()
            pi.posting_time = str(SI_dict['OrderDate'].time())
            pi_total = 0.0
            if float(last_single_SI_dict["conversion_rate"]) != 0.0 and float(last_single_SI_dict["conversion_rate"]) != 1.0:
                pi.currency = SI_dict["currency"]
                pi.conversion_rate = float(SI_dict["conversion_rate"])
            elif float(last_single_SI_dict["conversion_rate"]) == 0.0 or float(last_single_SI_dict["conversion_rate"]) == 1.0:
                pi.currency = "NGN"
                pi.conversion_rate = None
            zeros = []
            for item in last_single_paid_and_fulfilled_items:
                # if float(item["rate"]) < 0:
                #     zeros.append(item)
                # else:
                nl = pi.append('items', {})
                nl.description = item["description"]
                nl.item_name = item["item_name"]
                nl.item_code = item["item_name"]
                nl.rate = float(item["rate"])
                # nl.base_rate = float(item["rate"])
                nl.conversion_factor = item["conversion_factor"]
                nl.uom = item["uom"]
                nl.expense_account = item["expense_account"]
                nl.cost_center = item["cost_center"]
                nl.qty = float(item["qty"])
                nl.warehouse = item["warehouse"]
                nl.purchase_order = current_order
                pi_total += float(nl.rate) * float(nl.qty)
            # if pi.items:
            pi.set_posting_time = 1
            pi.cash_bank_account = "Access Bank - DCL"
            pi.taxes_and_charges = ""
            pi.taxes = []
            pi.inflow_file = file
            # print "             ", paid_and_fulfilled_items
            print "             Paid and Fulfilled PI Total", pi_total, current_order, pi.currency
            # print "             ", pi.as_dict()["items"]
            if pi_total:
                pi.mode_of_payment = "Cash"
                # if pi.conversion_rate:
                # print "<<<<",pi.grand_total,">>>>"
                # print "<<<<",pi.conversion_rate,">>>>"
                # print "<<<<",pi.grand_total * pi.conversion_rate,">>>>"
                pi.paid_amount = pi.grand_total
                pi.base_paid_amount = pi.outstanding_amount
                pi.insert()
                pi.save()
                frappe.db.commit()
                pi.submit()
                frappe.db.commit()
            else:
                for item in zeros:
                    make_stock_entry(item_code=item["item_code"], qty=item['qty'],
                                     to_warehouse=item["warehouse"],
                                     valuation_rate=1, remarks="This is affected by data import. " + file,
                                     posting_date=pi.posting_date,
                                     posting_time=pi.posting_time,
                                     set_posting_time=1, inflow_file=file)
                    frappe.db.commit()
                    print "Stock entry created."

        if last_single_paid_items:
            pi = make_purchase_invoice(current_order)
            # pi.update_stock = 1
            pi.is_paid = 1
            pi.items = []
            pi.posting_date = last_single_SI_dict['OrderDate'].date()
            pi.posting_time = str(last_single_SI_dict['OrderDate'].time())
            pi_total = 0.0
            if float(last_single_SI_dict["conversion_rate"]) != 0.0 and float(last_single_SI_dict["conversion_rate"]) != 1.0:
                pi.currency = last_single_SI_dict["currency"]
                pi.conversion_rate = float(last_single_SI_dict["conversion_rate"])
            elif float(last_single_SI_dict["conversion_rate"]) == 0.0 or float(last_single_SI_dict["conversion_rate"]) == 1.0:
                pi.currency = "NGN"
                pi.conversion_rate = None
            zeros = []
            for item in last_single_paid_items:
                nl = pi.append('items', {})
                nl.description = item["description"]
                nl.item_name = item["item_name"]
                nl.item_code = item["item_name"]
                nl.rate = float(item["rate"])
                nl.conversion_factor = item["conversion_factor"]
                nl.uom = item["uom"]
                nl.expense_account = item["expense_account"]
                nl.cost_center = item["cost_center"]
                nl.qty = float(item["qty"])
                nl.warehouse = item["warehouse"]
                nl.purchase_order = current_order

                pi_total += float(nl.rate) * float(nl.qty)
            # if pi.items:
            pi.set_posting_time = 1
            pi.cash_bank_account = "Access Bank - DCL"
            pi.taxes_and_charges = ""
            pi.taxes = []
            pi.inflow_file = file
            # print "             ", paid_items
            print "             Paid Items Only PI Total", pi_total, current_order, pi.currency
            # print "             ", pi.as_dict()["items"]
            if pi_total:
                pi.mode_of_payment = "Cash"
                pi.insert()
                frappe.db.commit()
                if pi.currency != "NGN":
                    pi.paid_amount = pi.grand_total
                    pi.base_paid_amount = pi.outstanding_amount
                    pi.save()
                    frappe.db.commit()
                pi.submit()
                frappe.db.commit()
            else:
                pass

        if last_single_fulfilled_items:
            pi = make_purchase_invoice(current_order)
            pi.update_stock = 1
            # pi.is_paid = 1
            pi.items = []
            pi.posting_date = last_single_SI_dict['OrderDate'].date()
            pi.posting_time = str(last_single_SI_dict['OrderDate'].time())
            pi_total = 0.0
            if float(last_single_SI_dict["conversion_rate"]) != 0.0 and float(
                    last_single_SI_dict["conversion_rate"]) != 1.0:
                pi.currency = last_single_SI_dict["currency"]
                pi.conversion_rate = float(last_single_SI_dict["conversion_rate"])
            elif float(last_single_SI_dict["conversion_rate"]) == 0.0 or float(
                    last_single_SI_dict["conversion_rate"]) == 1.0:
                pi.currency = "NGN"
                pi.conversion_rate = None
            zeros = []
            for item in last_single_fulfilled_items:
                nl = pi.append('items', {})
                nl.description = item["description"]
                nl.item_name = item["item_name"]
                nl.item_code = item["item_name"]
                nl.rate = float(item["rate"])
                nl.conversion_factor = item["conversion_factor"]
                nl.uom = item["uom"]
                nl.expense_account = item["expense_account"]
                nl.cost_center = item["cost_center"]
                nl.qty = float(item["qty"])
                nl.warehouse = item["warehouse"]
                nl.purchase_order = current_order

                pi_total += float(nl.rate) * float(nl.qty)
            # if pi.items:
            pi.set_posting_time = 1
            pi.cash_bank_account = "Access Bank - DCL"
            pi.taxes_and_charges = ""
            pi.taxes = []
            pi.inflow_file = file
            # print "             ", paid_items
            print "             Paid Items Only PI Total", pi_total, current_order, pi.currency
            # print "             ", pi.as_dict()["items"]
            if pi_total:
                pi.mode_of_payment = "Cash"
                pi.insert()
                frappe.db.commit()
                if pi.currency != "NGN":
                    pi.paid_amount = pi.grand_total
                    pi.base_paid_amount = pi.outstanding_amount
                    pi.save()
                    frappe.db.commit()
                pi.submit()
                frappe.db.commit()
            else:
                pass

    None


def remove_imported_data(file):
    SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Invoice` WHERE inflow_file=%s""",(file))

    for si in SIs:
        si_doc = frappe.get_doc("Purchase Invoice",si[0])
        if si_doc.docstatus == 1:
            si_doc.cancel()
        si_doc.delete()

    # SIs = frappe.db.sql("""SELECT name FROM `tabStock Entry` WHERE docstatus=1""")
    #
    # for si in SIs:
    #     si_doc = frappe.get_doc("Stock Entry", si[0])
    #     si_doc.cancel()
    #     si_doc.delete()

    SIs = frappe.db.sql("""SELECT name FROM `tabPurchase Order` WHERE inflow_file=%s""",(file))

    for si in SIs:
        si_doc = frappe.get_doc("Purchase Order", si[0])
        if si_doc.docstatus == 1:
            si_doc.cancel()
        si_doc.delete()