frappe.ui.form.on("Sales Invoice", {
    async onload(frm) {
        const company = frm.doc.company;

        if (!company) return;

        if (!await frappe.db.exists("Digital Invoice Setting", company)) return;

        const doc = await frappe.db.get_doc("Digital Invoice Setting", company);

        if (doc.enabled) {
            frm.toggle_display("fbr_integration", true);
            frm.toggle_reqd("sales_type", true);
            frm.fields_dict["items"].grid.update_docfield_property("sales_type", "reqd", 1);
        } else {
            frm.toggle_display("fbr_integration", false);
        }
        setup_custom_buttons(frm, doc);
    },

    sales_type(frm) {
        frm.doc.items.forEach(row => {
            row.sales_type = frm.doc.sales_type;
            frappe.ui.form.trigger("Sales Invoice Item", "sales_type", frm, row.doctype, row);
        });
        frm.refresh_field("items");
    },

    refresh: function (frm) {
        if (!frm.is_new() && frm.doc.is_posted === 0 && frm.doc.docstatus !== 2) {
            frm.add_custom_button(
                __("Digital Invoice Preview"),
                function () {
                    frappe.call({
                        method: "digclient.api.get_digital_invoice_preview",
                        args: {
                            doctype: frm.doc.doctype,
                            docname: frm.doc.name,
                        },
                        callback: function (r) {
                            if (r.message) {
                                diginvoicing.digital_invoice_preview.make_dialog(r.message);
                            }
                        },
                    });
                },
                __("Preview")
            );
        }
    }
});

frappe.provide("diginvoicing.digital_invoice_preview");

diginvoicing.digital_invoice_preview.make_dialog = function (invoice) {
    const columns = [
        { name: "HS Code", id: "hsCode", width: 100, editable: false },
        { name: "Description", id: "productDescription", width: 200, editable: false },
        { name: "Qty", id: "quantity", width: 80, editable: false },
        { name: "Rate", id: "fixedNotifiedValueOrRetailPrice", width: 100, editable: false },
        { name: "Discount", id: "discount", width: 100, editable: false },
        { name: "Amount", id: "valueSalesExcludingST", width: 120, editable: false },
        { name: "Sales Tax Rate", id: "rate", width: 120, editable: false },
        { name: "Sales Tax Amount", id: "salesTaxApplicable", width: 120, editable: false },
        { name: "Further Tax", id: "furtherTax", width: 120, editable: false },
        { name: "Extra Tax", id: "extraTax", width: 120, editable: false },
        { name: "Total", id: "totalValues", width: 120, editable: false },
    ];

    let dialog = new frappe.ui.Dialog({
        size: "extra-large",
        title: __("Digital Invoice Preview"),
        fields: [{ fieldtype: "HTML", fieldname: "preview_html" }],
    });
    setTimeout(function () {
        new frappe.DataTable(dialog.get_field("preview_html").wrapper, {
            columns: columns,
            data: invoice,
            dynamicRowHeight: false,
            checkboxColumn: false,
            inlineFilters: false,
        });
        const datatable = new frappe.DataTable(dialog.get_field("preview_html").wrapper, {
            dynamicRowHeight: false,
            checkboxColumn: false,
            inlineFilters: false,
        });
        datatable.refresh(invoice, columns);
    }, 200);

    dialog.show();
};


async function setup_custom_buttons(frm, doc) {
    const enable_for_customer = await frappe.db.get_value("Customer", frm.doc.customer, "enable_digital_invoicing");
    if (!frm.doc.is_posted && frm.doc.docstatus && doc.enabled && enable_for_customer.message.enable_digital_invoicing && frappe.user.has_role("Digi. Invoicing User") && frm.doc.docstatus !== 2) {
        frm.add_custom_button(__("Post to DI"), async () => {
            await frappe.call({
                method: "digclient.api.resync_invoice",
                args: {
                    doctype: "Sales Invoice",
                    name: frm.doc.name
                },
                freeze: true,
                freeze_message: __(`Resyncing Sales Invoice ${frm.doc.name} for Digi. Invoicing...`),
                callback: (r) => {
                    if (!r.exc) {
                        frm.remove_custom_button("Post to DI")
                        frappe.show_alert(__(`Sales Invoice ${frm.doc.name} Synced successfully.`));
                    }
                }
            });
        });
    }
}

frappe.ui.form.on("Sales Invoice Item", {
    sales_type(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        const taxable_types = [
            "Exempt goods",
            "Goods at zero-rate",
            "3rd Schedule Goods",
            "Goods as per SRO.297(|)/2023",
            "Goods at Reduced Rate"
        ];
        const is_required = taxable_types.includes(row.sales_type);
        frm.fields_dict["items"].grid.toggle_reqd("sro_serial_no", is_required);
        frm.fields_dict["items"].grid.toggle_reqd("schedule_no", is_required);
    }
});