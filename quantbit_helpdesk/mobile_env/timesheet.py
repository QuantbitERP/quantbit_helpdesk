import json
import os
import calendar
import frappe
from frappe import _
from frappe.auth import LoginManager
from frappe.utils import (
    cstr,
    get_date_str,
    today,
    nowdate,
    getdate,
    now_datetime,
    get_first_day,
    get_last_day,
    date_diff,
    flt,
    pretty_date,
    fmt_money,
)
from mobile.mobile_env.app_utils import (
    gen_response,
    generate_key,
    ess_validate,
    get_employee_by_user,
    validate_employee_data,
    get_ess_settings,
    get_global_defaults,
    exception_handel,
)

from erpnext.accounts.utils import get_fiscal_year

import frappe
import json
from frappe import _


import frappe
from frappe.utils import getdate

@frappe.whitelist()
def create_timesheet(**data):
    try:
        # Retrieve employee details based on the logged-in user
        emp_data = get_employee_by_user(
            frappe.session.user, fields=["name", "image", "department", "company"]
        )
        frappe.msgprint(str(emp_data))  # Log employee data for debugging
    
        # Check if updating an existing timesheet or creating a new one
        if data.get("name"):  # If name is provided, update existing timesheet
            timesheet_doc = frappe.get_doc("Timesheet", data.get("name"))
        else:  # Create a new timesheet
            timesheet_doc = frappe.new_doc("Timesheet")
        
        # Update timesheet data with the provided details from 'data'
        timesheet_doc.update({
            'employee': data.get("employee",""),
            'company': data.get("company",""),
            'start_date': getdate(data.get("start_date")),  # Ensure date format is correct
            'end_date': getdate(data.get("end_date")),
            'remarks': data.get("remarks", ""),
            'parent_project': data.get("project", ""),
        })

        # Add the time_logs if present hyyhhy
        if "time_logs" in data and isinstance(data["time_logs"], list):
            timesheet_doc.time_logs = []
            for log in data["time_logs"]:
                timesheet_doc.append('time_logs', {
                    'activity_type': log.get('activity_type'),
                    'task': log.get('task'),
                    'hours': log.get('hours'),
                    'from_time': log.get('from_time'),
                    'to_time': log.get('to_time'),
                    'project': log.get('project'),
                    'description': log.get('description'),
                })
        
        # Determine if timesheet should be submitted or just saved
        timesheet_submit = frappe.db.get_value(
            "Employee Self Service Settings", "Employee Self Service Settings", "submit_timesheet"
        )
        
        if timesheet_submit == 1:
            timesheet_doc.submit()
        else:
            timesheet_doc.save()

        return gen_response(200, "Timesheet has been updated successfully")

    except frappe.PermissionError:
        return gen_response(500, "Not permitted to perform this action")
    
    except Exception as e:
        return exception_handler(e)



def exception_handler(e):
    frappe.log_error(message=str(e), title="Exception Occurred")
    return {"status": "error", "message": str(e)}

        
@frappe.whitelist()
def get_timesheet_list(start=0, page_length=10, filters=None, month=None, year=None):
    try:
        # Initialize filters as a list if not provided
        filters = filters or []

        # Log input for debugging
        frappe.msgprint(f'Month: {month}, Year: {year}, Filters: {filters}', 'Timesheet API Debug')
        # Ensure month and year are passed as strings or integers
        if month and year:
            # Create a date range filter for the entire month
            start_date = f'{year}-{int(month):02d}-01'
            end_date = f'{year}-{int(month):02d}-{get_last_day_of_month(year, month)}'
            frappe.msgprint(start_date)
            frappe.msgprint(end_date)
            
            # Add date range filter for start_date field in the Timesheet
            filters.append(['start_date', 'between', [start_date, end_date]])

        # Fetch timesheet list with applied filters
        timesheet_list = frappe.get_list(
            "Timesheet",
            fields=["*"],
            start=start,
            page_length=page_length,
            order_by="modified desc",
            filters=filters,
        )

        # Return response with the filtered list
        return gen_response(200, "Timesheet List retrieved successfully", timesheet_list)
    
    except frappe.PermissionError:
        return gen_response(500, "Not permitted to read Timesheet")
    except Exception as e:
        return exception_handel(e)

def get_last_day_of_month(year, month):
    import calendar
    return calendar.monthrange(int(year), int(month))[1]
    
@frappe.whitelist()
def get_timesheet_details(**data):
    try:
        timesheet_doc= frappe.get_doc("Timesheet",data.get("name"))
        return gen_response(200, "Timesheet get successfully", timesheet_doc)
    except frappe.PermissionError:
        return gen_response(500, "Not permitted for read Timesheet")
    except Exception as e:
        return exception_handel(e)
    
@frappe.whitelist()
def get_activity_type_list():
    try:
        activity_types = frappe.get_all("Activity Type")
        return gen_response(200, "Activity Type list get successfully", activity_types)
    except frappe.PermissionError:
        return gen_response(500, "Not permitted for activity type")
    except Exception as e:
        return exception_handel(e)
    
@frappe.whitelist()
def get_task_list(filters=None):
    try:
        task_list = frappe.get_list("Task",filters=filters,fields=["name","subject"])
        return gen_response(200,"Task list get successfully",task_list)
    except frappe.PermissionError:
        return gen_response(500, "Not permitted for read task")
    except Exception as e:
        return exception_handel(e)

@frappe.whitelist()
def get_project_list(start=0, page_length=10, filters=None):
    try:
        project_list = frappe.get_list("Project",filters=filters,fields=["name","project_name"],start=start,
            page_length=page_length,)
        return gen_response(200,"Project list get successfully",project_list)
    except frappe.PermissionError:
        return gen_response(500, "Not permitted for read project")
    except Exception as e:
        return exception_handel(e)