# Copyright (c) 2025, Ali Raza and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IntegrationLog(Document):
	pass


def create_log(doctype, docname, payload, response, status="Success", title=None):
	"""Create a log entry for integration events."""
	log = frappe.get_doc({
		"doctype": "Integration Log",
		"title": title or f"Integration Log for {doctype} {docname}",
		"document_type": doctype,
		"document_name": docname,
		"status": status,
		"payload": str(payload),
		"response": str(response),
	})
	log.insert(ignore_permissions=True)
	frappe.db.commit()
	return log