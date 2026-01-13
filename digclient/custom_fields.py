from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup_custom_fields():
    custom_fields = {
        "Customer": [
            dict(
                fieldname="ntn",
                label="NTN Number",
                fieldtype="Data",
                insert_after="customer_group",
                reqd=1,
            ),
            dict(
                fieldname="address",
                label="Address",
                fieldtype="Data",
                insert_after="ntn",
                reqd=1,
            ),
            dict(
                fieldname="province",
                label="Province",
                fieldtype="Select",
                options="PUNJAB\nBALOCHISTAN\nAZAD JAMMU AND KASHMIR\nCAPITAL TERRITORY\nKHYBER PAKHTUNKHWA\nSINDH\nGILGIT BALTISTAN",
                insert_after="address",
                reqd=1,
            ),
            dict(
                fieldname="registration_type",
                label="Registration Type",
                fieldtype="Select",
                options="Registered\nUnregistered",
                insert_after="province",
                reqd=1,
            ),
            dict(
                fieldname="enable_digital_invoicing",
                label="Enable Digital Invoicing",
                fieldtype="Check",
                insert_after="registration_type",
            ),
        ],
        "Company": [
            dict(
                fieldname="address",
                label="Address",
                fieldtype="Data",
                insert_after="sale_types",
                reqd=1,
            ),
            dict(
                fieldname="custom_fbr_settings",
                label="FBR Settings",
                fieldtype="Tab Break",
                insert_after="old_parent",
            ),
            dict(
                fieldname="province",
                label="Province",
                fieldtype="Select",
                options="PUNJAB\nBALOCHISTAN\nAZAD JAMMU AND KASHMIR\nCAPITAL TERRITORY\nKHYBER PAKHTUNKHWA\nSINDH\nGILGIT BALTISTAN",
                insert_after="address",
                reqd=1,
            ),
            dict(
                fieldname="sale_types",
                label="Sale Types",
                fieldtype="Table",
                options="Company Sales Type",
                insert_after="custom_fbr_settings",
                reqd=1,
            ),
            dict(
                fieldname="sale_types",
                label="Sale Types",
                fieldtype="Table",
                options="Company Sales Type",
                insert_after="custom_fbr_settings",
                reqd=1,
            ),
        ],
        "Item": [
            dict(
                fieldname="tab_fbr_settings",
                label="FBR Settings",
                fieldtype="Tab Break",
                insert_after="uoms",
            ),
            dict(
                fieldname="hs_code",
                label="HS Code",
                fieldtype="Link",
                options="HS Code",
                insert_after="tab_fbr_settings",
                reqd=1,
            ),
            dict(
                fieldname="hs_uom",
                label="HS UOM",
                fieldtype="Link",
                options="HS Uom",
                insert_after="hs_code",
                read_only=1,
            ),
            dict(
                fieldname="column_break_fbr_setting",
                fieldtype="Column Break",
                insert_after="hs_uom",
            ),
            dict(
                fieldname="sales_type",
                label="Sale Type",
                fieldtype="Link",
                options="Sales Type",
                insert_after="column_break_fbr_setting",
                reqd=1,
            ),
        ],
        "Supplier": [
            dict(
                fieldname="address",
                label="Address",
                fieldtype="Data",
                insert_after="registration_type",
                reqd=1,
            ),
            dict(
                fieldname="province",
                label="Province",
                fieldtype="Select",
                options="PUNJAB\nBALOCHISTAN\nAZAD JAMMU AND KASHMIR\nCAPITAL TERRITORY\nKHYBER PAKHTUNKHWA\nSINDH\nGILGIT BALTISTAN",
                insert_after="country",
                reqd=1,
            ),
            dict(
                fieldname="registration_type",
                label="Registration Type",
                fieldtype="Select",
                options="Registered\nUnregistered",
                insert_after="province",
                reqd=1,
            ),
        ],
        "Purchase Invoice Item": [
            dict(
                fieldname="hs_code",
                label="HS Code",
                fieldtype="Read Only",
                fetch_from="item_code.hs_code",
                insert_after="item_name",
                reqd=1,
            ),
        ],
        "Purchase Invoice": [
            dict(
                fieldname="column_break_integration_info",
                fieldtype="Column Break",
                insert_after="posting_datetime",
            ),
            dict(
                fieldname="fbr_integration",
                fieldtype="Section Break",
                insert_after="remarks",
                label="FBR Integration",
            ),
            dict(
                fieldname="integration_id",
                fieldtype="Read Only",
                label="Integration ID",
                insert_after="column_break_integration_info",
                read_only=1,
            ),
            dict(
                fieldname="is_posted",
                fieldtype="Check",
                label="Is Posted",
                insert_after="fbr_integration",
                read_only=1,
            ),
            dict(
                fieldname="posting_datetime",
                fieldtype="Datetime",
                label="Posting Datetime",
                insert_after="integration_id",
                read_only=1,
            ),
        ],
        "Sales Taxes and Charges": [
            dict(
                label="Tax Type",
                fieldname="tax_type",
                fieldtype="Select",
                insert_after="account_head",
                options="Sales Tax\nFurther Tax\nAdvance Tax",
                reqd=1,
                in_list_view=1,
            ),
        ],
        "Sales Invoice": [
            dict(
                fieldname="column_break_32hi0",
                fieldtype="Column Break",
                insert_after="posting_datetime",
            ),
            dict(
                fieldname="fbr_integration",
                label="Digital Invoicing Integration",
                fieldtype="Section Break",
                insert_after="remarks",
            ),
            dict(
                fieldname="integration_id",
                label="Integration ID",
                fieldtype="Read Only",
                insert_after="fbr_integration",
            ),
            dict(
                fieldname="is_posted",
                label="Is Posted",
                fieldtype="Check",
                insert_after="column_break_32hi0",
                read_only=1,
            ),
            dict(
                fieldname="posting_datetime",
                label="Posting Datetime",
                fieldtype="Datetime",
                insert_after="integration_id",
                read_only=1,
            ),
        ],
        "Sales Invoice Item": [
            dict(
                fieldname="custom_digital_invoicing_taxes",
                label="Digital Invoicing Taxes",
                fieldtype="Section Break",
                insert_after="grant_commission",
            ),
            dict(
                fieldname="fed_payable",
                label="FED Payable",
                fieldtype="Float",
                insert_after="custom_digital_invoicing_taxes",
            ),
            dict(
                fieldname="sales_type",
                label="Sales Type",
                fieldtype="Link",
                options="Sales Type",
                insert_after="customer_item_code",
                fetch_from="item_code.sales_type",
                read_only=1
            ),
            dict(
                fieldname="schedule_no",
                label="Schedule No",
                fieldtype="Read Only",
                insert_after="sro_serial_no",
                fetch_from="item_code.sro_schedule_no",
            ),
            dict(
                fieldname="sro_serial_no",
                label="SRO Serial No",
                fieldtype="Read Only",
                insert_after="sales_type",
                fetch_from="item_code.sro_item_serial_no",
            ),
            dict(
                fieldname="hs_code",
                label="HS Code",
                fieldtype="Link",
                insert_after="item_code",
                options="HS Code",
                fetch_from="item_code.hs_code",
                read_only=1,
            ),
            dict(
                fieldname="hs_uom",
                label="HS UOM",
                fieldtype="Link",
                insert_after="hs_code",
                options="HS Uom",
                fetch_from="item_code.hs_uom",
                read_only=1,
            ),
        ],
    }

    custom_fields2 = {
        "Item": [
            dict(
                fieldname="sro_item_serial_no",
                label="SRO Item Serial No",
                fieldtype="Data",
                insert_after="hs_uom",
            ),
            dict(
                fieldname="sro_schedule_no",
                label="SRO Schedule No",
                fieldtype="Data",
                insert_after="sro_item_serial_no",
            ),
        ]
    }

    create_custom_fields(custom_fields)
    create_custom_fields(custom_fields2)
