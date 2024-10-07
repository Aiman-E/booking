frappe.views.calendar["Reservation"] = {
    field_map: {
		start: "start_date",
		end: "end_date",
		name: "name",
		id: "name",
		allDay: "allDay",
		child_name: "name",
		title: "title",
    },
    gantt: false,
    get_events_method: "booking.booking.doctype.reservation.reservation.get_events",
};

