import frappe

def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '%.12f' % f
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))


#fordavidbanjo.inflow_import.import_sales.start_import
def start_import():
    import csv
    import os
    current_customer = ""
    SI_dict = {}
    SI_items = []
    # input_file = csv.DictReader(open(os.path.dirname(os.path.abspath(__file__))+'/data/inFlow_ProductDetails_test.csv'))
    input_file = csv.DictReader(open(os.path.dirname(os.path.abspath(__file__))+'/data/inFlow_ProductDetails.csv'))

    # current_customer = input_file[0]["Customer"]

    income_accounts = "Sales - JC"
    # income_accounts = "Sales - J"
    cost_centers = "Main - JC"
    # cost_centers = "Main - J"

    rows = list(input_file)
    total_paid = 0.0
    # print rows
    totalrows = len(rows)
    for i,row in enumerate(rows):
        print row

        exists_cat = frappe.db.sql("""SELECT Count(*) FROM `tabItem Group` WHERE item_group_name=%s""",(row["Category"].strip() + " Category"))
        print exists_cat
        if exists_cat[0][0] == 0:
            print "sulod!"
            if row["ItemType"] == "Stockable":
                SI_dict = {"doctype": "Item Group",
                           "item_group_name": row["Category"].strip() + " Category",
                           "parent_item_group": "Products"
                           }
                SI = frappe.get_doc(SI_dict)
                SI_created = SI.insert(ignore_permissions=True)
                frappe.db.commit()
            else:
                SI_dict = {"doctype": "Item Group",
                           "item_group_name": row["Category"].strip() + " Category",
                           "parent_item_group": "Services"
                           }
                SI = frappe.get_doc(SI_dict)
                SI_created = SI.insert(ignore_permissions=True)
                frappe.db.commit()

        exists_cat = frappe.db.sql("""SELECT name FROM `tabItem` WHERE item_code=%s""", (row["Name"].strip()))
        print exists_cat
        if exists_cat == ():
            item_code = row["Name"]
            if row["Name"] == "Kerosene stove, four burner pressure type for use with 39L autoclave / steriliser.\nSupplied specifically without top plate (ring) for use only with the autoclave / steam sterilizer.":
                item_code = "Kerosene Stove"
            SI_dict = {"doctype": "Item",
                       "item_code": item_code.strip(),
                       "description": row["Description"],
                       "item_group":row["Category"].strip() + " Category"
                       }
            SI = frappe.get_doc(SI_dict)
            try:
                SI_created = SI.insert(ignore_permissions=True)
                frappe.db.commit()
            except:
                pass
        else:
            if row["BarCode"].strip():
                print "updating:",exists_cat[0][0]
                item_doc = frappe.get_doc("Item",exists_cat[0][0])
                bc = item_doc.append('barcodes', {})
                bc.barcode = row["BarCode"]
                item_doc.barcode = row["BarCode"]
                try:
                    item_doc.save()
                except:
                    pass