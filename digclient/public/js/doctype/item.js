frappe.ui.form.on("Item", {
    onload(frm) {
        frm.set_query("sales_type", () => {
            return {
                query: "diginvoicing.api.get_sales_types_for_company",
                filters: {
                    company: frm.doc.company
                }
            };
        });
    },
    // sales_type: function (frm) {
    //     const taxable_types = [
    //         "Exempt goods",
    //         "Goods at zero-rate",
    //         "3rd Schedule Goods",
    //         "Goods as per SRO.297(|)/2023",
    //     ];
    //     const is_required = taxable_types.includes(frm.doc.sales_type);
    //     frm.toggle_reqd("sro_schedule_no", is_required);
    //     frm.toggle_reqd("sro_item_serial_no", is_required);
    // }
})