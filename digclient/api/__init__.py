from digclient.constants import DI_HOST
from digclient.di_client.doctype.integration_log.integration_log import create_log
from digclient.utils import get_configurations, is_enabled
import frappe
from frappe import _
from frappe.utils import now
import requests
import ast


TAX_MISMATCH_ERROR = (
    "Provided sales tax amount does not match the calculated sales tax amount."
    " Please ensure that the provided Sale Value is used to calculate the"
    " Sales Tax Amount for the provided Rate."
)


@frappe.whitelist()
def sync_invoice(doc, resync=False):
    """
    Sync a Sales/Purchase Invoice to FBR.
    Called on before_submit or manual resync.
    """
    setting = frappe.get_doc("Digital Invoice Setting", doc.company)
    doc = doc.as_dict()

    if not is_enabled(doc.get("company")):
        frappe.throw(
            _("Digital Invoicing is not enabled for company {0}").format(doc.get("company"))
        )

    if not (setting.auto_post_invoices_on_submit or resync):
        return

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

    item_logs = _get_item_logs_for_doc(doc)

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
            "item_logs": item_logs,
        },
    )

    message = result.get("message") if isinstance(result, dict) else None

    response_data = message if message else result

    if isinstance(response_data, dict) and response_data.get("status") == "Success" and response_data.get("invoiceNumber"):
        frappe.db.delete(
            "Integration Log",
            {"document_type": doc.get("doctype"), "document_name": doc.get("name")},
        )
        create_log(
            doc.get("doctype"),
            doc.get("name"),
            response_data.get("payload"),
            response_data.get("response"),
            "Success",
            f"Success Dig. Invoicing Sync {doc.get('doctype')} {doc.get('name')}",
        )
        frappe.db.set_value(
            doc.get("doctype"),
            doc.get("name"),
            {
                "integration_id": response_data.get("invoiceNumber"),
                "posting_datetime": now(),
                "is_posted": 1,
            },
            update_modified=False,
        )
    else:
        _process_error_response(doc, response_data)

        frappe.db.commit()
        create_log(
            doc.get("doctype"),
            doc.get("name"),
            response_data.get("payload") if isinstance(response_data, dict) else {},
            response_data.get("response") if isinstance(response_data, dict) else response_data,
            status="Error",
            title=f"Dig. Invoicing Sync Error {doc.get('doctype')} {doc.get('name')}",
        )
        error_detail = response_data.get("response") if isinstance(response_data, dict) else response_data
        frappe.throw(
            _(
                "There is an error while submitting invoice to Digital Invoicing \nError: {0}"
            ).format(error_detail)
        )


def _get_item_logs_for_doc(doc):
    """
    Build item_logs list for items that previously failed FBR rounding validation.
    Returns list of dicts: [{item_code: item_log_index}, ...]
    """
    item_logs = []
    for line in doc.get("items", []):
        item_code = line.get("item_code")
        log_index = frappe.db.get_value(
            "Item Log",
            {
                "reference_doctype": doc.get("doctype"),
                "reference_document": doc.get("name"),
                "index": line.get("idx"),
            },
            "index",
        )
        if log_index:
            item_logs.append({item_code: log_index})
    return item_logs


def _process_error_response(doc, response_data):
    """
    Process FBR error response and create Item Logs for tax rounding mismatches.
    This tracks which items need 0.01 adjustment on retry.
    """
    if not isinstance(response_data, dict):
        return

    fbr_response = response_data.get("response", response_data)
    if isinstance(fbr_response, str):
        return

    validation_response = {}
    if isinstance(fbr_response, dict):
        validation_response = fbr_response.get("validationResponse", {})

    item_statuses = validation_response.get("invoiceStatuses") or []

    for item in item_statuses:
        status = item.get("status", "")
        error = item.get("error", "")
        item_index = str(item.get("itemSNo", ""))

        if status != "Valid" and TAX_MISMATCH_ERROR == error:
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


@frappe.whitelist()
def resync_invoice(doctype, name):
    """Manually resync an invoice to FBR (Post to DI button)."""
    doc = frappe.get_doc(doctype, name)
    return sync_invoice(doc, resync=True)


@frappe.whitelist()
def validate_fbr_invoice(doctype, docname):
    """
    Validate invoice against FBR without actually posting it.
    Uses FBR's validateinvoicedata endpoint.
    """
    doc = frappe.get_doc(doctype, docname)
    setting = frappe.get_doc("Digital Invoice Setting", doc.company)

    if not setting.enabled:
        frappe.throw(_("Digital Invoicing is not enabled for company {0}").format(doc.company))

    doc_dict = doc.as_dict()
    for item in doc_dict.get("items", []):
        item.unit_size = (
            frappe.db.get_value("Item", item.get("item_code"), "unit_size") or 1
        )
        item.packet_size = (
            frappe.db.get_value("Item", item.get("item_code"), "custom_packet_size") or 1
        )

    item_logs = _get_item_logs_for_doc(doc_dict)

    token = setting.get_password("access_token")
    settings = setting.as_dict()
    settings["access_token"] = token

    result = call(
        url=f"{DI_HOST}/diginvoicing.utils.validate_invoice",
        payload={
            "sales_invoice": doc_dict,
            "settings": settings,
            "configurations": get_configurations(
                doc_dict.get("customer"), doc_dict.get("supplier"), doc_dict.get("company")
            ),
            "item_logs": item_logs,
        },
    )
    return result.get("message") if isinstance(result, dict) else result


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

    item_logs = _get_item_logs_for_doc(doc)

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

        resp = s.post(url, data=body, headers=headers, timeout=300)

        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                _json = resp.json()
                _json = _json.get("exception", "").replace("Error: ", "") if _json.get("exception") else str(_json)
                return ast.literal_eval(_json)
            except Exception:
                return {"error": resp.text}

        try:
            return resp.json()
        except Exception:
            return {"error": resp.text}