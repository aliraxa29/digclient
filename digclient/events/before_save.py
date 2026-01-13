import frappe


def item_before_save(doc, method):
    if not doc.hs_uom:
        doc.hs_uom = frappe.db.get_value("HS Code", {"name": doc.hs_code}, "uom")


def company_before_save(doc, method):
    seen = set()
    for st in doc.get("sale_types"):
        if st.sales_type in seen:
            frappe.throw(
                f"Duplicate scenario '{st.sales_type}' found in sales types for company '{doc.name}'."
            )
        seen.add(st.sales_type)
