import frappe
from frappe import _

def is_enabled(company):
    """Check if the Digital Invoice feature is enabled."""
    return frappe.db.get_value("Digital Invoice Setting", {"name": company}, "enabled")


def get_configurations(customer, supplier, company):
    customer = frappe.get_doc("Customer", customer) if customer else None
    supplier = frappe.get_doc("Supplier", supplier) if supplier else None
    company = frappe.get_doc("Company", company) if company else None
    return {
        "customer": (
            {
                "ntncnic": customer.get("ntn", default=""),
                "business_name": customer.get("customer_name", default=""),
                "registration_type": customer.get("registration_type", default=""),
                "province": customer.get("province", default=""),
                "address": customer.get("address", default=""),
            }
            if customer
            else {}
        ),
        "supplier": (
            {
                "ntncnic": supplier.get("tax_id", default=""),
                "business_name": supplier.get("supplier_name", default=""),
                "registration_type": supplier.get("registration_type", default=""),
                "province": supplier.get("province", default=""),
                "address": supplier.get("address", default=""),
            }
            if supplier
            else {}
        ),
        "company": {
            "ntncnic": company.get("tax_id", default=""),
            "business_name": company.get("company_name", default=""),
            "province": company.get("province", default=""),
            "address": company.get("address", default=""),
        },
    }