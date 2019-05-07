import frappe


def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '%.12f' % f
    i, p, d = s.partition('.')
    return float('.'.join([i, (d + '0' * n)[:n]]))


def make_contact(**args):
    contact = frappe.get_doc({
        'doctype': 'Contact',
        'first_name': args.get('name'),
        'mobile_no': args.get('mobile_no'),
        'email_id': args.get('email_id'),
        'inflow_file':args.get('inflow_file'),
        'is_primary_contact': 1,
        'links': [{
            'link_doctype': args.get('doctype'),
            'link_name': args.get('name')
        }]
    }).insert()

    return contact


def make_address(**args):
    address = frappe.get_doc({
        'doctype': 'Address',
        'address_title': args.get('address_line1'),
        'address_line1': args.get('address_line1'),
        'address_line2': args.get('address_line2'),
        'city': args.get('city'),
        'state': args.get('state'),
        'pincode': args.get('pincode'),
        'inflow_file': args.get('inflow_file'),
        'is_primary_address': 1,
        'country': args.get('country'),
        'links': [{
            'link_doctype': args.get('doctype'),
            'link_name': args.get('name')
        }]
    }).insert()

    return address


# fordavidbanjo.inflow_import.import_sales.start_import
def start_import():
    import csv
    import os
    current_customer = ""
    SI_dict = {}
    SI_items = []
    # input_file = csv.DictReader(open(os.path.dirname(os.path.abspath(__file__))+'/data/inFlow_ProductDetails_test.csv'))
    input_file = csv.DictReader(open(os.path.dirname(os.path.abspath(__file__)) + '/data/inFlow_Customer.csv'))

    # current_customer = input_file[0]["Customer"]

    income_accounts = "Sales - JC"
    # income_accounts = "Sales - J"
    cost_centers = "Main - JC"
    # cost_centers = "Main - J"

    rows = list(input_file)
    total_paid = 0.0
    # print rows
    totalrows = len(rows)
    for i, row in enumerate(rows):
        print row

        customer_name = ""
        exists_cat = frappe.db.sql("""SELECT name FROM `tabCustomer` WHERE customer_name=%s""",
                                   (row["Name"].strip()))
        if exists_cat == ():
            customer = frappe.get_doc({"doctype": "Customer", "customer_name": row["Name"].strip(),
                                       "customer_group": "All Customer Groups", "customer_type": "Company"}).insert()
            customer_name = customer.name
            frappe.db.commit()

        else:
            print "updating:", exists_cat[0][0]
            customer_name = exists_cat[0][0]

        try:
            # country = row["Country"].strip() or "No Country Specified."
            make_address(
                address_line1=row["Address1"],
                address_line2=row["Address2"],
                city=row["City"].strip() or "Not specified.",
                state=row["State"],
                pincode=row["PostalCode"],
                country=row["Country"].strip() or "Nigeria",
                doctype="Customer",
                name=customer_name,
                inflow_file='inFlow_Customer.csv'
            )
            print "success address"
        except Exception as e:
            print e
            print "error address"
            # try:
            #     item_doc.save()
            # except:
            #     pass


        try:
            # country = row["Country"].strip() or "No Country Specified."
            make_contact(
                first_name=row["ContactName"].strip() or row["Name"],
                mobile_no=row["Phone"],
                email_id=row["Email"],
                doctype="Customer",
                name=customer_name,
                inflow_file='inFlow_Customer.csv'
            )
            print "success contact"
        except Exception as e:
            print e
            print "error contact"
