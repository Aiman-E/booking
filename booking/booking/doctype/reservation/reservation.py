# Copyright (c) 2024, Gestio ltd and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


class Reservation(Document):	

	def before_insert(self):
		a=1
		pass

	def before_save(self):
		a=1
		pass


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
		select
			name,
			title,
			start_date,
			end_date
		from `tabReservation`
		""",
		as_dict=True,
		update= {
		'allDay': 0,
	},
	)

	return d
