
import frappe
from frappe.utils import now



@frappe.whitelist()
def get_hd_tickets(user=None, status=None, priority=None, limit=20):
    try:
        filters = {}
        if user:
            filters["user"] = user
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        
        tickets = frappe.get_all(
            "HD Ticket", 
            fields=[
                "name", "subject", "status", "priority", "creation",
                "agent_group", "ticket_type", "opening_date", 
                "resolution_date", "_assign"
            ],
            filters=filters,
            limit_page_length=limit,
        )

        if not tickets:
            return {"message": "No tickets found.", "tickets": []}
        
        for ticket in tickets:
            if ticket.get("_assign"):
                try:
                    assigned_emails = json.loads(ticket["_assign"])
                    if assigned_emails:
                        # Get the first assigned user's full name
                        assigned_user = frappe.db.get_value(
                            "User",
                            assigned_emails[0],
                            "full_name"
                        )
                        ticket["assigned_to"] = assigned_user
                    else:
                        ticket["assigned_to"] = None
                except Exception as e:
                    frappe.log_error(frappe.get_traceback(), f"Error parsing _assign for ticket {ticket['name']}")
                    ticket["assigned_to"] = None
            else:
                ticket["assigned_to"] = None

            del ticket["_assign"]

        return {"message": "Tickets retrieved successfully.", "tickets": tickets}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_hd_tickets")
        return {"error": str(e), "message": "Failed to retrieve tickets."}






import json
@frappe.whitelist()
def save_ticket():
    try:
        ticket_data = frappe.local.form_dict

        if frappe.request.data:
            ticket_data = json.loads(frappe.request.data)
        else:
            ticket_data = frappe.form_dict

        mandatory_fields = ["subject", "priority"]
        missing_fields = [field for field in mandatory_fields if not ticket_data.get(field)]
        if missing_fields:
            return {
                "status": "error",
                "code": 400,
                "message": f"Missing mandatory fields: {', '.join(missing_fields)}",
            }

    
        if ticket_data.get("name"):
            try:
                ticket = frappe.get_doc("HD Ticket", ticket_data["name"])
            except frappe.DoesNotExistError:
                return {
                    "status": "error",
                    "code": 404,
                    "message": f"Ticket with name {ticket_data['name']} does not exist.",
                }
        else:
            ticket = frappe.new_doc("HD Ticket")


        fields_to_map = [
            "subject", "raised_by", "priority", "status", "ticket_type", "agent_group", 
            "template", "sla", "response_by", "agreement_status", "resolution_by", 
            "service_level_agreement_creation", "first_responded_on", "opening_date", 
            "opening_time", "contact", "customer", "email_account", "via_customer_portal", 
            "feedback_rating", "feedback_text", "feedback", "feedback_extra","custom_department",
            "custom_module","custom_sub_module", "custom_environment_type", "custom_development_state",
            "custom_sub_department", "custom_team", "custom_description", "custom_notes"
        ]
        for field in fields_to_map:
            if field in ticket_data and ticket_data[field] is not None:
                ticket.set(field, ticket_data[field])

        ticket.save()
        frappe.db.commit()

        return {
            "status": "success",
            "code": 200,
            "message": f"Ticket {ticket.name} saved successfully.",
            "ticket_name": ticket.name,
        }

    except frappe.ValidationError as e:
        frappe.log_error(frappe.get_traceback(), "Validation Error in Ticket")
        return {
            "status": "error",
            "code": 422,
            "message": f"Validation error: {str(e)}",
        }

    except frappe.PermissionError as e:
        frappe.log_error(frappe.get_traceback(), "Permission Error in Ticket")
        return {
            "status": "error",
            "code": 403,
            "message": f"Permission denied: {str(e)}",
        }

    except frappe.DuplicateEntryError as e:
        frappe.log_error(frappe.get_traceback(), "Duplicate Entry in Ticket")
        return {
            "status": "error",
            "code": 409,
            "message": f"Duplicate entry: {str(e)}",
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Unexpected Error in Ticket")
        return {
            "status": "error",
            "code": 500,
            "message": f"An unexpected error occurred: {str(e)}",
        }



@frappe.whitelist()
def get_helpdesk_masters():
    try:
        response = {
            "departments": [d["name"] for d in frappe.get_all("Quantbit Department", fields=["name"])],
            "subdepartments": [sd["name"] for sd in frappe.get_all("SubDepartment", fields=["name"])],
            "teams": [t["name"] for t in frappe.get_all("HD Team", fields=["name"])],
            "environment_types": [e["name"] for e in frappe.get_all("Environment", fields=["name"])],
            "modules": [m["name"] for m in frappe.get_all("Module", fields=["name"])],
            "submodules": [ {"name": sm["name"], "module": sm["module"]} for sm in frappe.get_all("SubModule", fields=["name", "module"])
             ],
            "development_states": [ds["name"] for ds in frappe.get_all("Development State", fields=["name"])],
            "ticket_types": [tt["name"] for tt in frappe.get_all("HD Ticket Type", fields=["name"])],
            "priorities": [tt["name"] for tt in frappe.get_all("HD Ticket Priority", fields=["name"])],
            'contacts': [c["name"] for c in frappe.get_all("Contact", fields=["name"])],
            'customers': [c["name"] for c in frappe.get_all("HD Customer", fields=["name"])],
            'sla': [s["name"] for s in frappe.get_all("HD Service Level Agreement", fields=["name"])],
            'email_accounts': [ea["name"] for ea in frappe.get_all("Email Account", fields=["name"])] 
        }
        return {
            "status": "success",
            "data": response
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_helpdesk_masters_error")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_ticket_details(helpdeskid):
    try:
        if not helpdeskid:
            return {
                "status": "error",
                "code": 400,
                "message": "helpdeskid is required.",
            }

        if not frappe.db.exists("HD Ticket", helpdeskid):
            return {
                "status": "error",
                "code": 404,
                "message": f"Ticket with id {helpdeskid} does not exist.",
            }

        ticket = frappe.get_doc("HD Ticket", helpdeskid)

        return {
            "status": "success",
            "code": 200,
            "data": ticket.as_dict()
        }

    except frappe.PermissionError as e:
        frappe.log_error(frappe.get_traceback(), "Permission Error in get_ticket_details")
        return {
            "status": "error",
            "code": 403,
            "message": f"Permission denied: {str(e)}",
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Unexpected Error in get_ticket_details")
        return {
            "status": "error",
            "code": 500,
            "message": f"An unexpected error occurred: {str(e)}",
        }


@frappe.whitelist()
def get_all_hd_agent_names():
    try:
        agents = frappe.get_all(
            "HD Agent",
            fields=["agent_name"]
        )
        return [agent["agent_name"] for agent in agents]
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get HD Agent Names Error")
        return []



@frappe.whitelist()
def get_ticket_type_and_agent():
    try:
        response = {
            "ticket_types": [d["name"] for d in frappe.get_all("HD Ticket Type", fields=["name"])],
            "agents": [sd["agent_name"] for sd in frappe.get_all("HD Agent", fields=["agent_name"])],
            "priorities": [sd["name"] for sd in frappe.get_all("HD Ticket Priority", fields=["name"])],
    
        }
        return {
            "status": "success",
            "data": response
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_helpdesk_masters_error")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_communications(name):
    communications = frappe.get_all(
        "Communication",
        filters={
            "reference_doctype": "HD Ticket",
            "reference_name": name
        },
        fields=["name", "communication_type", "content", "subject", "sender", "creation"],
        order_by="creation asc"
    )
    return communications
