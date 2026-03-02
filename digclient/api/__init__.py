from digclient.constants import DI_HOST
from digclient.di_client.doctype.integration_log.integration_log import create_log
from digclient.utils import get_configurations, is_enabled
import frappe
from frappe import _
from frappe.utils import now
import requests
import requests


@frappe.whitelist()
def sync_invoice(doc, resync=False):
    setting = frappe.get_doc("Digital Invoice Setting", doc.company)
    doc = doc.as_dict()
    if is_enabled(doc.get("company")):
        if setting.auto_post_invoices_on_submit or resync:
            for item in doc.get("items", []):
                item.unit_size = (
                    frappe.db.get_value("Item", item.get("item_code"), "unit_size") or 1
                )
                item.packet_size = (
                    frappe.db.get_value(
                        "Item", item.get("item_code"), "custom_packet_size"
                    )
                    or 1
                )

            token = setting.get_password("access_token")
            settings = setting.as_dict()
            settings["access_token"] = token
            result = call(
                url=f"{DI_HOST}/diginvoicing.utils.post_invoice",
                payload={
                    "sales_invoice": doc,
                    "settings": settings,
                    "configurations": get_configurations(
                        doc.get("customer"), doc.get("supplier"), doc.get("company")
                    ),
                },
            )
            if result.get("message").get("invoiceNumber", None):
                message = result.get("message")
                frappe.db.delete(
                    "Integration Log",
                    {"document_type": doc.get("doctype"), "document_name": doc.get("name")},
                )
                create_log(
                    doc.get("doctype"),
                    doc.get("name"),
                    message.get("payload"),
                    message.get("response"),
                    "Success",
                    f"Success Dig. Invoicing Sync {doc.get('doctype')} {doc.get('name')}",
                )
                frappe.db.set_value(
                    doc.get("doctype"),
                    doc.get("name"),
                    {
                        "integration_id": message.get("invoiceNumber"),
                        "posting_datetime": now(),
                        "is_posted": 1,
                    },
                    update_modified=False,
                )
            else:
                for item in message.get("response").get("validationResponse", {}).get("invoiceStatuses", []):
                    status = item.get("status", "")
                    error = item.get("error", "")
                    item_index = str(item.get("itemSNo", ""))
                    if (
                        status != "Valid"
                        and "Provided sales tax amount does not match the calculated sales tax amount. Please ensure that the provided Sale Value is used to calculate the Sales Tax Amount for the provided Rate."
                        == error
                    ):
                        if not frappe.db.exists(
                            "Item Log",
                            {
                                "reference_doctype": doc.get("doctype"),
                                "reference_document": doc.get("name"),
                                "index": item_index,
                            },
                        ):
                            frappe.get_doc(
                                {
                                    "doctype": "Item Log",
                                    "reference_doctype": doc.get("doctype"),
                                    "reference_document": doc.get("name"),
                                    "index": item.get("itemSNo", ""),
                                }
                            ).insert(ignore_permissions=True)
                frappe.db.commit()
                create_log(
                    doc.get("doctype"),
                    doc.get("name"),
                    message.get("payload"),
                    message.get("response"),
                    status="Error",
                    title=f"Dig. Invoicing Sync Error {doc.get('doctype')} {doc.get('name')}",
                )
                frappe.throw(
                    _(
                        "There is an error while submitting invoice to Digital Invoicing \nError: {0}"
                    ).format(message.get("response"))
                )

    else:
        frappe.throw(
            _("Digital Invoicing is not enabled for company {0}").format(doc.company)
        )


@frappe.whitelist()
def resync_invoice(doctype, name):
    doc = frappe.get_doc(doctype, name)
    return sync_invoice(doc, resync=True)


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


@frappe.whitelist()
def get_digital_invoice_preview(doctype, docname):
    """Return the digital invoice payload preview (without posting)."""
    doc = frappe.get_doc(doctype, docname).as_dict()
    for item in doc.get("items", []):
        item.unit_size = (
            frappe.db.get_value("Item", item.get("item_code"), "unit_size") or 1
        )
        item.packet_size = (
            frappe.db.get_value("Item", item.get("item_code"), "custom_packet_size")
            or 1
        )

    item_logs = [
        {
            line.item_code: frappe.db.get_value(
                "Item Log",
                {"reference_document": line.get("parent"), "index": line.get("idx")},
                "index",
            )
        }
        for line in doc.get("items", [])
    ]
    url = f"{DI_HOST}/diginvoicing.utils.get_preview"
    result = call(
        url=url,
        payload={"sales_invoice": doc, "item_logs": item_logs},
    )
    return result.get("message")


def call(
    url: str,
    payload: dict | None = None,
    headers: dict | None = None,
):
    with requests.Session() as s:
        body = frappe.as_json(payload)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "token b6db3872d172f33:d5be4b5605ff60c",
        }
        resp = s.post(url, data=body, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
