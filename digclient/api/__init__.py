import frappe
from digclient.digclient.utils import sync_invoice


@frappe.whitelist()
def resync_invoice(doctype, name):
    doc = frappe.get_doc(doctype, name)
    if doc:
        sync_invoice(doc, True)

@frappe.whitelist()
def get_sales_types_for_company(doctype, txt, searchfield, start, page_len, filters):
    company = filters.get("company")
    if not company:
        return []

    return frappe.db.sql(
    """
        SELECT
            cs.sales_type, sales_type as description
        FROM
            `tabCompany Sales Type` cs
        WHERE
            cs.parent = %(company)s
            AND (
                cs.sales_type LIKE %(txt)s
            )
        LIMIT %(page_len)s OFFSET %(start)s
    """,
        {"company": company, "txt": f"%{txt}%", "page_len": page_len, "start": start},
    )