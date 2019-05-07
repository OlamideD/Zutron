import frappe
from dcl.inflow_import.stock import make_stock_entry
from erpnext.stock.utils import get_stock_value_from_bin
from dateutil import parser
import math
from frappe import _
# /home/jvfiel/frappe-v11/apps/erpnext/erpnext/accounts/doctype/payment_request/payment_request.py
from erpnext.accounts.doctype.payment_request.payment_request \
    import get_amount, get_gateway_details, get_dummy_message,get_party_bank_account


@frappe.whitelist(allow_guest=True)
def make_payment_request(**args):
    """Make payment request"""

    args = frappe._dict(args)

    ref_doc = frappe.get_doc(args.dt, args.dn)
    grand_total = get_amount(ref_doc, args.dt)
    if args.loyalty_points and args.dt == "Sales Order":
        from erpnext.accounts.doctype.loyalty_program.loyalty_program import validate_loyalty_points
        loyalty_amount = validate_loyalty_points(ref_doc, int(args.loyalty_points))
        frappe.db.set_value("Sales Order", args.dn, "loyalty_points", int(args.loyalty_points), update_modified=False)
        frappe.db.set_value("Sales Order", args.dn, "loyalty_amount", loyalty_amount, update_modified=False)
        grand_total = grand_total - loyalty_amount

    gateway_account = get_gateway_details(args) or frappe._dict()

    existing_payment_request = frappe.db.get_value("Payment Request",
                                                   {"reference_doctype": args.dt, "reference_name": args.dn,
                                                    "docstatus": ["!=", 2]})

    bank_account = (get_party_bank_account(args.get('party_type'), args.get('party'))
                    if args.get('party_type') else '')

    if existing_payment_request:
        frappe.db.set_value("Payment Request", existing_payment_request, "grand_total", grand_total,
                            update_modified=False)
        pr = frappe.get_doc("Payment Request", existing_payment_request)

    else:
        pr = frappe.new_doc("Payment Request")
        pr.update({
            "payment_gateway_account": gateway_account.get("name"),
            "payment_gateway": gateway_account.get("payment_gateway"),
            "payment_account": gateway_account.get("payment_account"),
            "payment_request_type": args.get("payment_request_type"),
            "currency": ref_doc.currency,
            "grand_total": grand_total,
            "email_to": args.recipient_id or "",
            "subject": _("Payment Request for {0}").format(args.dn),
            "message": gateway_account.get("message") or get_dummy_message(ref_doc),
            "reference_doctype": args.dt,
            "reference_name": args.dn,
            "party_type": args.get("party_type"),
            "party": args.get("party"),
            "bank_account": bank_account,
            "inflow_file":args.inflow_file,
            "posting_date":args.posting_date,
            "posting_time":args.posting_time,
            "set_posting_time":1
        })

        if args.order_type == "Shopping Cart" or args.mute_email:
            pr.flags.mute_email = True

        if args.submit_doc:
            pr.insert(ignore_permissions=True)
            pr.submit()

    if args.order_type == "Shopping Cart":
        frappe.db.commit()
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = pr.get_payment_url()

    if args.return_doc:
        return pr

    return pr.as_dict()


def get_stock_value_on(warehouse=None, posting_date=None, item_code=None):
    from frappe.utils import flt, cstr, nowdate, nowtime
    # if not posting_date: posting_date = nowdate()

    values, condition = [posting_date], ""

    if warehouse:

        lft, rgt, is_group = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt", "is_group"])

        if is_group:
            values.extend([lft, rgt])
            condition += "and exists (\
				select name from `tabWarehouse` wh where wh.name = sle.warehouse\
				and wh.lft >= %s and wh.rgt <= %s)"

        else:
            values.append(warehouse)
            condition += " AND warehouse = %s"

    if item_code:
        values.append(item_code)
        print condition
        condition += (" AND item_code = %s")

    stock_ledger_entries = frappe.db.sql("""
		SELECT item_code, stock_value, name, warehouse
		FROM `tabStock Ledger Entry` sle
		WHERE posting_date <= %s {0}
		ORDER BY timestamp(posting_date, posting_time) DESC, name DESC
	""".format(condition), values, as_dict=1)

    sle_map = {}
    for sle in stock_ledger_entries:
        if not (sle.item_code, sle.warehouse) in sle_map:
            sle_map[(sle.item_code, sle.warehouse)] = flt(sle.stock_value)

    return sum(sle_map.values())


def add_stocks(items, file):
    for item in items:

        print item
        # if item["Location"] == "DCL House, Plot 1299 Fumilayo Ransome Kuti Way, Area 3, PMB 690 Garki, Abuja":
        #     to_warehouse = "DCLWarehouse - Abuja - DCL"
        # elif item[
        #     "Location"] == "DCL Laboratory Products Ltd, Plot 5 Block 4 Etal Avenue off Kudirat Abiola Way by NNPC Lagos NG - DCL":
        #     to_warehouse = "Lagos Warehouse - DCL"
        # else:
        to_warehouse = item["Location"]

        if item["OrderDate"]:
            OrderDate = parser.parse(item["OrderDate"])
        else:
            OrderDate = None

        if item["DatePaid"]:
            DatePaid = parser.parse(item["DatePaid"])
        else:
            DatePaid = None

        if item["DatePaid"]:
            # print "          ", item["DatePaid"].date(), item["DatePaid"].time()
            date = DatePaid.date()
            time = DatePaid.time()
        elif item["OrderDate"]:
            date = OrderDate.date()
            time = OrderDate.time()

        # def get_stock_value_from_bin(warehouse="DCLWarehouse - Abuja - DCL", item_code=item["item_code"]):
        bal = get_stock_value_on(warehouse=to_warehouse, posting_date=str(date), item_code=item["item_code"])
        print "          * * * * Check Bin * * * *"
        # print "          " + str(bal[0][0]), item['qty']
        print "          " + str(bal), item['qty']
        print "          " + item['item_code']

        if bal < item['qty'] or bal == None or bal == 0:
            diff = 0
            if bal != None:
                diff = bal

            print "              Diff:", item["qty"], diff, round(abs(float(item["qty"]) - diff), 2)
            qty = round(abs(float(item["qty"]) - diff), 2)
            # if qty < 1:
            qty = math.ceil(qty)
            make_stock_entry(item_code=item["item_code"], qty=qty,
                             to_warehouse=to_warehouse,
                             valuation_rate=1, remarks="This is affected by data import. " + file,
                             posting_date=date,
                             posting_time=time,
                             set_posting_time=1, inflow_file=file)
            frappe.db.commit()
            print "Stock entry created."
