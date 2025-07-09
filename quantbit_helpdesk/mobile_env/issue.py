
import frappe
from frappe.utils import now
import json





@frappe.whitelist()
def get_issues(user=None, status=None, priority=None, limit=20):
    try:
        filters = {}
        if user:
            filters["raised_by"] = user
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        
        # Query the Issue doctype
        issues = frappe.get_all(
            "Issue", 
            fields=["name", "subject", "status", "priority", "creation",
                    "description","issue_type","resolution_by","opening_date","opening_time",
                    "contact","customer","via_customer_portal"],
            filters=filters,
            limit_page_length=limit,
        )

        if not issues:
            return {"message": "No issues found.", "issues": []}

        return {"message": "Issues retrieved successfully.", "issues": issues}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_issues")
        return {"error": str(e), "message": "Failed to retrieve issues."}

@frappe.whitelist()
def create_or_update_issue(data):
    """
    Create a new Issue or update an existing one in ERPNext.
    """
    try:
        issue_data = frappe.parse_json(data)

        # Mandatory fields check
        mandatory_fields = ["subject", "raised_by", "priority", "status", "issue_type"]
        missing_fields = [field for field in mandatory_fields if not issue_data.get(field)]
        if missing_fields:
            return {
                "status": "error",
                "code": 400,
                "message": f"Missing mandatory fields: {', '.join(missing_fields)}",
            }

        # Check if updating an existing issue
        if issue_data.get("name"):
            try:
                issue = frappe.get_doc("Issue", issue_data["name"])
            except frappe.DoesNotExistError:
                return {
                    "status": "error",
                    "code": 404,
                    "message": f"Issue with name {issue_data['name']} does not exist.",
                }
        else:
            # Create a new Issue
            issue = frappe.new_doc("Issue")

        # Map fields to the Issue document
        fields_to_map = [
            "subject", "raised_by", "priority", "status", "issue_type",
            "description", "resolution_by", "first_responded_on", "opening_date",
            "opening_time", "contact", "customer", "via_customer_portal",
            "feedback_rating", "feedback_text", "assigned_to", "resolution_details"
        ]
        for field in fields_to_map:
            if field in issue_data:
                issue.set(field, issue_data.get(field))

        # Save the issue
        issue.save()
        frappe.db.commit()

        return {
            "status": "success",
            "code": 200,
            "message": f"Issue {issue.name} saved successfully.",
            "issue_name": issue.name,
        }

    except frappe.ValidationError as e:
        frappe.log_error(frappe.get_traceback(), "Validation Error in Issue")
        return {
            "status": "error",
            "code": 422,
            "message": f"Validation error: {str(e)}",
        }

    except frappe.PermissionError as e:
        frappe.log_error(frappe.get_traceback(), "Permission Error in Issue")
        return {
            "status": "error",
            "code": 403,
            "message": f"Permission denied: {str(e)}",
        }

    except frappe.DuplicateEntryError as e:
        frappe.log_error(frappe.get_traceback(), "Duplicate Entry in Issue")
        return {
            "status": "error",
            "code": 409,
            "message": f"Duplicate entry: {str(e)}",
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Unexpected Error in Issue")
        return {
            "status": "error",
            "code": 500,
            "message": f"An unexpected error occurred: {str(e)}",
        }
    
