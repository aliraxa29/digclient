import frappe
from frappe import _
from digclient.utils import is_enabled
from digclient.api import sync_invoice

def sync_fbr_invoice(doc, method):
    """
    Sync FBR invoice on submit.
    """
    if is_enabled(doc.company):
        for item in doc.items:
            if not item.sales_type:
                frappe.throw(_("Please select sales type for item {0}").format(item.item_code))

            types = [
                "Goods as per SRO.297(|)/2023",
            ]
            if item.sales_type in types:
                if not item.sro_serial_no or not item.schedule_no:
                    frappe.throw(_("SRO Serial No or Schedule no is required"))
                

            if not item.hs_uom:
                item.hs_uom = frappe.db.get_value(
                    "HS Code", {"name": item.hs_code}, "uom"
                )
        
        return sync_invoice(doc)
