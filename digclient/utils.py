from dataclasses import dataclass, asdict
from decimal import ROUND_HALF_UP, Decimal
import json
import frappe
from frappe import _
from frappe.utils import flt, now
from diginvoicing.digital_invoicing.doctype.integration_log.integration_log import (
    create_log,
)
from frappe.integrations.utils import make_post_request

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


def get_taxes(taxes_lines):
    """
    Organize item-wise tax data from taxes_lines into structured InvoiceItem format,
    keyed by tax_type from Sales Taxes and Charges table.
    """
    itemised_tax = {}

    for tax in taxes_lines:
        item_tax_map = json.loads(tax.item_wise_tax_detail or "{}")
        if not item_tax_map:
            continue

        tax_type_key = tax.tax_type or ""
        if not tax_type_key:
            continue

        for item_code, tax_data in item_tax_map.items():
            tax_rate = 0.0
            tax_amount = 0.0

            if isinstance(tax_data, list):
                tax_rate = flt(tax_data[0])
                tax_amount = flt(tax_data[1])
            else:
                tax_rate = flt(tax_data)

            # Initialize per item entry if not exists
            if item_code not in itemised_tax:
                itemised_tax[item_code] = {}

            # Set the tax_type key with percentage and amount
            itemised_tax[item_code][tax_type_key] = {
                "percentage": tax_rate,
                "amount": tax_amount,
            }

    return itemised_tax


def get_items(sales_taxes, line_items):
    item_taxes = get_taxes(sales_taxes)

    invoice_items = []
    for line in line_items:
        index = frappe.db.get_value("Item Log", {"reference_document": line.get("parent"), "index": line.get("idx")}, "index")
        item_code = line.get("item_code")
        tax_data = item_taxes.get(item_code, {})

        gst = tax_data.get("Sales Tax", {"percentage": 0.0, "amount": 0.0})
        further_tax = tax_data.get("Further Tax", {"percentage": 0.0, "amount": 0.0})
        extra_tax = tax_data.get("Advance Tax", {"percentage": 0.0, "amount": 0.0})

        invoice_item = InvoiceItem(
            discount=0,
            fedPayable=round(line.get("fed_payable", 0), 2),
            furtherTax=round(further_tax["amount"], 2) or 0,
            hsCode=line.get("hs_code", ""),
            extraTax=(
                str(0)
                if not is_reduced_rate_item(line.get("sales_type", ""))
                else ""
            ),
            productDescription=f'{line.get("item_code", "")} - {line.get("item_name", "")}',
            quantity=round(line.get("quantity_ltr_kg", 0), 2),
            rate=(
                f'{int(gst["percentage"])}%'
                if not is_exempted_item(line.get("sales_type", ""))
                else "Exempt"
            ),
            salesTaxApplicable=cascade_round(gst["amount"]) if not index else cascade_round(gst["amount"] + 0.01),
            salesTaxWithheldAtSource=0,
            sroItemSerialNo=line.get("sro_serial_no", ""),
            sroScheduleNo=line.get("schedule_no", ""),
            totalValues=round(flt(line.get("net_amount", 0))
            + flt(gst["amount"])
            + flt(further_tax["amount"])
            + flt(extra_tax["amount"]), 2),
            uoM=line.get("hs_uom", ""),
            valueSalesExcludingST=round(line.get("net_amount", 0), 2),
            saleType=line.get("sales_type", ""),
            fixedNotifiedValueOrRetailPrice=round(line.get("rate", 0), 2),
        )
        invoice_items.append(asdict(invoice_item))

    return invoice_items


def cascade_round(value: float, places: int = 2) -> float:
    """
    Custom rounding with cascade effect:
    - 176.9849 -> 176.99
    - 176.985  -> 176.99
    - 10.8345  -> 10.84
    """
    d = Decimal(str(value))
    quantize_str = "0." + "0" * (places - 1) + "1"
    return float(d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP))


def is_exempted_item(sales_type):
    return sales_type == "Exempt goods"


def is_reduced_rate_item(sales_type):
    return sales_type == "Goods at Reduced Rate"


@frappe.whitelist()
def get_digital_invoice_preview(doctype, docname):
    """Return the digital invoice payload preview (without posting)."""
    doc = frappe.get_doc(doctype, docname)
    return get_items(doc.taxes, doc.items)