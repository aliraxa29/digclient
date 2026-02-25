frappe.ui.form.on("Item", {
    onload(frm) {
        frm.set_query("sales_type", () => {
            return {
                query: "digclient.api.get_sales_types_for_company",
                filters: {
                    company: frm.doc.company
                }
            };
        });
    },
})