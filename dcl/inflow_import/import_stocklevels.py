import frappe
from erpnext.stock.utils import get_stock_value_from_bin
from dcl.inflow_import.stock import make_stock_entry
from dateutil import parser

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '%.12f' % f
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))


#dcl.inflow_import.import_buy.start_import
def start_import():
    import csv
    import os
    current_customer = ""
    current_order = ""
    SI_dict = {}
    SI_items = []
    paid_and_fulfilled_items = []
    fulfilled_items = []
    paid_items = []
    input_file = csv.DictReader(open(os.path.dirname(os.path.abspath(__file__))+'/data/inFlow_StockLevels.csv'))

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

           # from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
            #/home/jvfiel/frappe-v11/apps/dcl/dcl/inflow_import/stock/__init__.py
        # for item in SI_items:
        #def get_stock_value_from_bin(warehouse="DCLWarehouse - Abuja - DCL", item_code=item["item_code"]):
        item = row
        print item
        bal = get_stock_value_from_bin(warehouse="DCLWarehouse - Abuja - DCL", item_code=item["Item"])
        print "          * * * * Check Bin * * * *"
        # print "          "+str(bal[0][0]),item['qty']
        # print "          "+item['item_code']
        # if bal[0][0] < item['qty'] or bal[0][0] == None or bal[0][0] == 0:
        #     diff = 0
        #     if bal[0][0] != None:
         #       diff = bal[0][0]
        to_warehouse = ""
        if row["Location"] == "DCL House, Plot 1299 Fumilayo Ransome Kuti Way, Area 3, PMB 690 Garki, Abuja":
            to_warehouse = "DCLWarehouse - Abuja - DCL"
        elif row["Location"] == "DCL Laboratory Products Ltd, Plot 5 Block 4 Etal Avenue off Kudirat Abiola Way by NNPC Lagos NG - DCL":
            to_warehouse = "Lagos Warehouse - DCL"
        else:
            to_warehouse = row["Location"] + " - DCL"
        if float(item["Quantity"]) < 1:

            exists_cat = frappe.db.sql("""SELECT Count(*) FROM `tabItem` WHERE item_code=%s""",
                                       (row["Item"].strip()))
            # print exists_cat
            if exists_cat[0][0] == 0:
                item_code = row["Item"]
                if row[
                    "Item"] == "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser.\nSupplied specifically without top plate (ring) for use only with the autoclave / steam sterilizer.":
                    item_code = "Kerosene Stove"
                item_dict = {"doctype": "Item",
                             "item_code": item_code.strip(),
                             "description": row["Item"],
                             # "item_group": row["Category"].strip() + " Category"
                             "item_group": "All Item Groups"
                             }
                SI = frappe.get_doc(item_dict)
                SI.insert(ignore_permissions=True)
                frappe.db.commit()

            make_stock_entry(item_code=item["Item"].strip(),qty=abs(float(item["Quantity"])),
                             to_warehouse=to_warehouse,
                             valuation_rate=1,remarks="This is affected by data import. StockLevels",
                             posting_date=parser.parse("3/15/2017"),
                             posting_time="00:00:00",
                             set_posting_time=1,inflow_file="inFlow_StockLevels.csv"
                             )
            frappe.db.commit()


def remove_imported_data():


    # frappe.db.sql("""UPDATE `tabStock Entry` SET posting_date=%s""",(str(parser.parse("3/15/2017"))))
    # frappe.db.commit()

    SIs = frappe.db.sql("""SELECT name FROM `tabStock Entry` WHERE docstatus=1 and inflow_file=%s""",(inFlow_StockLevels.csv))

    for si in SIs:
        si_doc = frappe.get_doc("Stock Entry", si[0])
        si_doc.cancel()
        si_doc.delete()