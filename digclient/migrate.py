import frappe
from digclient.custom_fields import setup_custom_fields


def after_migrate():
    setup_custom_fields()
    frappe.db.sql(
        "UPDATE `tabSales Taxes and Charges` SET tax_type = 'Sales Tax' WHERE tax_type IS NULL AND rate > 4;"
    )
    frappe.db.sql(
        "UPDATE `tabSales Taxes and Charges` SET tax_type = 'Further Tax' WHERE tax_type IS NULL AND rate = 4;"
    )
    frappe.db.sql(
        "UPDATE `tabSales Taxes and Charges` SET tax_type = 'Advance Tax' WHERE tax_type IS NULL AND rate < 4;"
    )