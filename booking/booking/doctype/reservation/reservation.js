// Copyright (c) 2024, Gestio ltd and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Reservation", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on('Reservation', {
    onload: function(frm) {
        // Code to run when the form is loaded
        if (frm.is_new()) {
            // Check if start_date and end_date are set
        if (frm.doc.start_date && frm.doc.end_date) {
            // Create a Date object from start_date
            let startDate = new Date(frm.doc.start_date);
            let endDate = new Date(frm.doc.end_date);
            
            // Add 2 hours and 30 minutes to start_date
            startDate.setHours(startDate.getHours() + 2);
            startDate.setMinutes(startDate.getMinutes() + 30);
            frm.set_value('start_date', frappe.datetime.convert_to_user_tz(startDate));

            // Add 2 hours and 30 minutes to end_date
            endDate.setHours(endDate.getHours() + 2);
            endDate.setMinutes(endDate.getMinutes() + 30);
            frm.set_value('end_date', frappe.datetime.convert_to_user_tz(endDate));
        }
        }
    }
});
