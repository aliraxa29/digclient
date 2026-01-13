frappe.ui.form.on("Purchase Invoice", {
    refresh: async function (frm) {
        const company = frm.doc.company;

        if (!company) return;

        if (!await frappe.db.exists("Digital Invoice Setting", company)) return;

        const doc = await frappe.db.get_doc("Digital Invoice Setting", company);

        if (doc.enabled) {
            frm.toggle_display("fbr_integration", true);
            frm.toggle_reqd("sales_type", true);
        } else {
            frm.toggle_display("fbr_integration", false);
        }
    }
});