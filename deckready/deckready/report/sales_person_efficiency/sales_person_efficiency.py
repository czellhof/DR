# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt,cstr
from erpnext.accounts.report.financial_statements import get_period_list

def execute(filters=None):
	columns, data = [], []
	columns=get_columns()
	data=get_lead_data(filters)
	chart=get_chart_data(data)
	return columns, data, None, chart
	
def get_columns():
	columns = [_("Sales Persons") + ":data:110", _("Lead Count") + ":Int:70",
				_("Interaction") + ":Int:60",
				_("Opp Count") + ":Int:80",
				_("Quot Count") + ":Int:80", _("Order Count") + ":Int:80",
				_("Order Value") + ":Float:100",_("Opp/Lead %") + ":Float:100",
				_("Quot/Lead %") + ":Float:100",_("Order/Quot %") + ":Float:100"
	]
	return columns

def get_lead_data(filters):
	conditions=""
	if filters.from_date:
		conditions += " and date(creation) >= %(from_date)s"
	if filters.to_date:
		conditions += " and date(creation) <= %(to_date)s"
	#drive it by order
	data = frappe.db.sql("""select sales_person as "Sales Person", count(name) as "Lead Count" from `tabLead` where 1 = 1 %s group by sales_person""" % (conditions,),filters, as_dict=1)
	dl=list(data)
	for row in dl:
		is_quot_count_zero = False
		row["Interaction"] = interaction_count(row["Sales Person"])
		row["Quot Count"]= get_lead_quotation_count(row["Sales Person"])
		row["Opp Count"] = get_lead_opp_count(row["Sales Person"])
		row["Order Count"] = get_quotation_ordered_count(row["Sales Person"])
		row["Order Value"] = get_order_amount(row["Sales Person"])
		row["Opp/Lead %"] = row["Opp Count"] / row["Lead Count"] * 100
		row["Quot/Lead %"] = row["Quot Count"] / row["Lead Count"] * 100
		if row["Quot Count"] == 0:
			row["Quot Count"] = 1
			is_quot_count_zero = True
		row["Order/Quot %"] = row["Order Count"] / row["Quot Count"] * 100
		if is_quot_count_zero ==  True:
			row["Quot Count"] = 0
	return dl
	
def get_lead_quotation_count(salesperson):
	quotation_count = frappe.db.sql("""select count(name) from `tabQuotation` 
										where lead in (select name from `tabLead` where sales_person = %s)""",salesperson)
	return flt(quotation_count[0][0]) if quotation_count else 0
	
def get_lead_opp_count(salesperson):
	opportunity_count = frappe.db.sql("""select count(name) from `tabOpportunity` 
										where lead in (select name from `tabLead` where sales_person = %s)""",salesperson)
	return flt(opportunity_count[0][0]) if opportunity_count else 0
	
def get_quotation_ordered_count(salesperson):
	#quotation_ordered_count = frappe.db.sql("""select count(name) from `tabQuotation` 
	#											where status = 'Ordered' and lead in (select name from `tabLead` where sales_person = %s)""",salesperson)
	quotation_ordered_count = frappe.db.sql("""select count(name) from `tabSales Order` 
												where sales_person = %s""",salesperson)
	return flt(quotation_ordered_count[0][0]) if quotation_ordered_count else 0
	
def get_order_amount(salesperson):
	#ordered_count_amount = frappe.db.sql("""select sum(base_net_amount) from `tabSales Order Item` 
	#										where prevdoc_docname in (select name from `tabQuotation` 
	#										where status = 'Ordered' and lead in (select name from `tabLead` 
	#										where sales_person = %s))""",salesperson)
	ordered_count_amount = frappe.db.sql("""select sum(base_grand_total) from `tabSales Order` 
											where sales_person = %s and docstatus = 1""",salesperson)
	return flt(ordered_count_amount[0][0]) if ordered_count_amount else 0
	
def interaction_count(salesperson):
	interaction_count = frappe.db.sql("""select count(name) from `tabInteraction Master` where reference_name in (select name from `tabLead` where sales_person = %s) """,salesperson)
	return flt(interaction_count[0][0]) if interaction_count else 0
	
def get_chart_data(data):
	x_intervals = ['x'] + [row["Sales Person"] for row in data]
	columns = [x_intervals]
	order_data = [row["Order Value"] for row in data]
	lead_data = [row["Lead Count"] for row in data]
	if order_data:
		columns.append(["Order Amount"]+ order_data)
	if lead_data:
		columns.append(["Lead Count"]+ lead_data)
	print columns
	chart = {
		"data": {
			'x': 'x',
			'columns': columns,
			'colors': {
				'Order Amount': '#5E64FF',
				'Lead Count': '#ff5858'
			}
		}
	}
	chart["chart_type"] = "bar"
	return chart
	