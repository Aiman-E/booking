// Copyright (c) 2024, Gestio ltd and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Reservation", {
// 	refresh(frm) {

// 	},
// });


function calculate_grand_total(frm) {
    frm.doc.grand_total = 0;
    frm.doc.items.forEach(i => {
        frm.doc.grand_total += i.rate * frm.doc.duration;
    });
}

frappe.ui.form.on('Reservation', {
    onload: function (frm) {
        // Add two and half hours since the code doesn't include the local time
        if (frm.is_new()) {
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

                frm.trigger("calculate_duration");
            }
        }
    },
    refresh: function (frm) {
        if (frm.doc.docstatus == 0 && !frm.is_new()  ) {
            frm.add_custom_button(__("Generate Invoice"),
                () => frm.trigger("generate_invoice"));

            frm.add_custom_button(__("Cancel Reservation"),
                () => frm.trigger("cancel_invoice"));

            frm.add_custom_button(__("Update Reservation Status"),
                () => frm.trigger("update_status"));

            frm.add_custom_button(__("Create Repeats"),
                () => frm.trigger("create_repeats"));
            
        }
    },
    start_date: function (frm) {
        frm.trigger("calculate_duration");
    },
    end_date: function (frm) {
        frm.trigger("calculate_duration");
    },
    duration: function (frm) {
        frm.trigger("calculate_grand_total");
    },
    generate_invoice: function (frm) {
        frappe.confirm(__("Are you sure you want to generate an invoice?"), () => {
            frm.call("generate_invoice").then((r) => {
                if (!r.exec) {
                    frm.reload_doc();
                }
            });
        });
    },
    cancel_invoice: function (frm) {
        frappe.confirm(__("Are you sure you want to cancel the invoice?"), () => {
            frm.call("cancel_invoice").then((r) => {
                if (!r.exec) {
                    frm.reload_doc();
                } else {
                    // Handle the case where an exception was raised
                    frappe.show_alert({
                        message: r.exc,
                        indicator: 'red'
                    });
                }
            });
        });
    },
    calculate_duration: function(frm) {
        frm.call("calculate_duration").then((r) =>{
            if(!r.exec){
                calculate_grand_total(frm);
                frm.refresh_fields();
            }  
        })
    },
    update_status: async function(frm) {
        await frm.reload_doc();
        frm.call("update_status").then((r) => {
            if (!r.exec) {
                frm.refresh_fields();
                frm.reload_doc();
            }
        })
    },
    create_repeats: function(frm) {
        frm.call("create_repeats").then((r) => {
            if (!r.exec) {
                frm.refresh_fields();
            }
        })
    }
});

frappe.ui.form.on('Reservation Item', {
    items_add: function (frm, cdt, cdn) {
        
    },
    item_code: function(frm, cdt, cdn) {
        row = locals[cdt][cdn]
        frm.call(
            'update_item_rates',
            {"cdt": cdt, "cdn": cdn, "item_code": row.item_code}
        ).then((r)=>{
            if(!r.exec){
                rate = r['message']['rate'];
                cdt = r['message']['cdt'];
                cdn = r['message']['cdn'];

                row = locals[cdt][cdn];
                row.rate = rate;

                calculate_grand_total(frm);

                frm.refresh_fields();
            } else {
                // Handle the case where an exception was raised
                frappe.show_alert({
                    message: r.exc,
                    indicator: 'red'
                });
            }
        });
    }
});