# Copyright (c) 2024, Gestio ltd and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document
from frappe import _

from erpnext import get_default_company, get_default_cost_center
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)

from datetime import datetime, timedelta

'''
	TODO: Export Customization from sales invoice
	TODO: Double check on conditions and validations
	TODO: Retrict saving price rate if existed or not
	TODO: multiple dates with same time
	TODO: check if end before start date and raise error
'''
class Reservation(Document):
	def validate(self):
		# check the price rate if existed or not
		pass

	def get_items(self):
		items = []
		
		for i in self.items:
			item = {
					"item_code": i.item_code,
					"rate": i.rate,
					"qty": self.duration,
				}
			items.append(item)

		return items
	
	def check_dates(self):
		pass

	def set_status(self, status):
		self.status = status

	def calculate_total_hours(self):
		whole_hours = int(self.duration)
		minutes = int((self.duration - whole_hours) * 60)
		self.total_hours = f"{whole_hours} hours - {minutes} minutes"

	def get_month_in_days(self, month):
		if month == 2: return 28
		if month in [1, 3, 5, 7,8, 10, 12]: return 31
		return 30

	@frappe.whitelist()
	def update_status(self):
		if self.status == "Cancelled and Refunded":
			return
		
		self.status = "Unconfirmed"

		linked_invoices = frappe.get_all('Sales Invoice',
									fields=[
										'name',
										'status',
										'docstatus'
									],
									filters={
										'custom_reservation': self.name,
		})

		if len(linked_invoices) > 0:
			i = linked_invoices[0] # Get latest invoice
			if i['docstatus'] == 1:
				self.status = "Confirmed"

			if i['docstatus'] == 2:
				self.status = "Cancelled"

		self.save()
			
				

	@frappe.whitelist()	
	def generate_invoice(self):
		linked_invoices = frappe.get_all('Sales Invoice',
								   fields=[
									   'name',
									   'status'
								   ],
								   filters={
									   'custom_reservation': self.name,
        })

		for i in linked_invoices:
			if i['status'] == "Cancelled":
				continue
			frappe.throw(
				_(
					"Sales invoice already exist"
				)
			)

		company = get_default_company()
		cost_center = get_default_cost_center(company)

		if not company:
			frappe.throw(
				_(
					"Company is mandatory for generating an invoice. Please set a default company in Global Defaults."
				)
			)
		
		invoice = frappe.new_doc("Sales Invoice")
		invoice.company = company

		invoice.cost_center = cost_center
		invoice.customer = self.customer

		item_list = self.get_items()
		for item in item_list:
			item['cost_center'] = cost_center
			invoice.append("items", item)

		self.save()
		invoice.custom_reservation = self.name

		if(self.paid_amount > 0):
			invoice.is_pos = 1
			payment = {
				"mode_of_payment": self.mode_of_payment,
				"amount": self.paid_amount
			}
			invoice.append("payments", payment)

		invoice.insert()
		invoice.submit()

	@frappe.whitelist()
	def cancel_invoice(self):
		linked_invoices = frappe.get_all('Sales Invoice',
								   filters={
									   'custom_reservation': self.name
        })

		if linked_invoices:
			for invoice in linked_invoices:
				invoice_doc = frappe.get_doc('Sales Invoice', invoice.name)
				
				# Check if the invoice is already cancelled
				if invoice_doc.docstatus == 2:
					frappe.msgprint(_(f"Invoice {invoice.name} is already cancelled."))
					continue
				
				# Cancel the invoice
				invoice_doc.cancel()
				frappe.msgprint(_(f"Sales Invoice {invoice.name} has been cancelled."))
		else:
			frappe.msgprint_(("No linked invoice found for this reservation."))
		

	@frappe.whitelist()
	def update_item_rates(self, args):
		rate = frappe.get_list('Item Price', ['price_list_rate'], {'item_code': args['item_code']})
		if len(rate) > 0:
			return {"cdt": args['cdt'], "cdn": args['cdn'], "rate": rate[0]['price_list_rate']}
		
		frappe.throw(_(f"Create price rate for item '{args['item_code']}' before using it"))

	@frappe.whitelist()
	def calculate_duration(self):
		if self.start_date and self.end_date:
			# Calculate the difference
			start = datetime.fromisoformat(self.start_date)
			end = datetime.fromisoformat(self.end_date)
			duration = (end - start).total_seconds() / 3600
			self.duration = duration

			self.calculate_total_hours()		

	@frappe.whitelist()
	def create_repeats(self):
		start_date = datetime.fromisoformat(self.start_date)
		end_date = datetime.fromisoformat(self.end_date)
		interval = self.interval
		count = self.count

		for i in range(count):
			if interval == "Daily":
				start_date += timedelta(days=1)
				end_date += timedelta(days=1)
			elif interval == "Weekly":
				start_date += timedelta(days=7)
				end_date += timedelta(days=7)
			elif interval == "Monthly":
				d = self.get_month_in_days(start_date.month)
				start_date += timedelta(days=d)
				end_date += timedelta(days=d)

			new_reservation = frappe.get_doc({
				"doctype": "Reservation",
				"start_date": start_date.isoformat(),
				"end_date": end_date.isoformat(),
				"customer": self.customer,
				"items": self.items,
				"confirmation": self.confirmation,
				"paid_amount": self.paid_amount,
				"mode_of_payment": self.mode_of_payment,
				"receipt_number": self.receipt_number,
				"grand_total": self.grand_total,
				"is_repeat_reservation": 1,
				"parent_reservation": self.name,
			})
			new_reservation.insert()

			self.append("linked_reservations", {
				"reservation": new_reservation.name,
				"status": "Unconfirmed"
			})

			
		self.save()


"""select `tabTimesheet Detail`.name as name,
			`tabTimesheet Detail`.docstatus as status,
			`tabTimesheet Detail`.parent as parent,
			from_time as start_date,
			hours,
			activity_type,
			`tabTimesheet Detail`.project,
			to_time as end_date,
			CONCAT(`tabTimesheet Detail`.parent, ' (', ROUND(hours,2),' hrs)') as title
		from `tabTimesheet Detail`, `tabTimesheet`
		"""
@frappe.whitelist()
def get_events(start, end, filters=None):

	d = frappe.db.sql("""
		SELECT
			name,
			title,
			start_date,
			end_date
		FROM `tabReservation`
		WHERE status != 'Cancelled'
		""",
		as_dict=True,
		update= {
		'allDay': 0
	},
	)

	return d
