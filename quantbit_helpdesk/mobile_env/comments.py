import frappe
from bs4 import BeautifulSoup
from frappe.utils import cstr, now, today,pretty_date
from mobile.mobile_env.app_utils import (
    gen_response,
    generate_key,
    role_profile,
    ess_validate,
    get_employee_by_user,
    validate_employee_data,
    get_ess_settings,
    get_global_defaults,
    exception_handel,
)


@frappe.whitelist()
def edit_note_in_ticket(doc_name, note, row_id):
    doc=frappe.get_doc("HD Ticket",{'name':doc_name},['notes'])
    for d in doc.notes:
        if cstr(d.name) == row_id:
            d.note = note
            d.db_update()

@frappe.whitelist()
def delete_note_in_ticket(doc_name, row_id):
    try:
        doc=frappe.get_doc("HD Ticket",{'name':doc_name},['notes'])
        for d in doc.notes:
            if cstr(d.name) == row_id:
                doc.remove(d)
                break
        doc.save()
        return gen_response(200, "Comment Delete Successfully")
    except Exception as e:
        return exception_handel(e)


@frappe.whitelist()
def get_data_from_notes(doc_name):
    emp_data = get_employee_by_user(frappe.session.user, fields=["name", "company", "employee_name"])
    doc = frappe.get_doc("HD Ticket", {'name': doc_name}, ['notes'])
    note_li = []
    current_site = frappe.local.site
   
   
    for i in doc.notes:
        note_dict = {}
        
        soup = BeautifulSoup(i.note, 'html.parser')
        paragraphs = soup.find_all('p')
        text_list = [p.get_text(strip=True) for p in paragraphs]
        text_list = list(filter(None, text_list))
        
        
        note_dict["name"] = int(i.name)
        note_dict["note"] = str(i.note)
        note_dict["commented"] = str(i.added_by)
        

        note_dict["added_on"] = pretty_date(i.creation)
        str1 = frappe.get_value(
                "User", i.added_by, "user_image", cache=True
            )
        frappe.msgprint(str1)
        if str1 is not None:
            note_dict['image'] = frappe.utils.get_url()+ str1
        else:
            note_dict['image'] = None
        
        note_li.append(note_dict)

    return gen_response(200, "Notes get successfully", note_li)

