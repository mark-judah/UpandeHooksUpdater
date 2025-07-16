import frappe
import os
import json
import re

@frappe.whitelist()
def update_hooks_file(module=None, currentUser=None):
    doctypes = [
        "Client Script",
        "Server Script",
        "Workflow",
        "Workflow Action Master",
        "Custom Field",
        "Property Setter",
        "Email Template",
        "Custom DocPerm"
    ]
    docname = None
    customizations_map = {}
    skipped_duplicates = {}
    users_customizations = {}
    updating_external_app=True

    if module == "Upande Hooks Updater":
        updating_external_app=False
    
    def to_snake_case(name):
        return re.sub(r'[\W]+', '_', name.strip()).lower()

    if updating_external_app:
        app_path = os.path.abspath(os.path.join(os.path.dirname(
        __file__), "..", "..", "..", to_snake_case(module), to_snake_case(module),to_snake_case(module)))
    else:
        app_path = os.path.abspath(os.path.join(os.path.dirname(
        __file__), "..", to_snake_case(module)))

    def is_already_exported(doctype, name):
        folder_name = to_snake_case(name)
        doctype_folder = doctype.lower().replace(" ", "_")
        possible_dirs = [
            os.path.join(app_path, "custom", doctype_folder, folder_name),
            os.path.join(app_path, "doctype", folder_name),
            os.path.join(app_path, folder_name),
        ]
        return any(os.path.isdir(path) for path in possible_dirs)

    def record_skipped(dt, name):
        skipped_duplicates.setdefault(dt, []).append(name)

    # Include custom reports only
    try:
        custom_reports = frappe.get_all(
            "Report", filters={"is_standard": "No"}, fields=["name", "owner"])
        filtered = []
        for r in custom_reports:
            if is_already_exported("Report", r.name):
                record_skipped("Report", r.name)
            else:
                filtered.append(r.name)
                if currentUser == r.owner:
                    users_customizations.setdefault("Report", []).append(r.name)
        if filtered:
            customizations_map["Report"] = filtered
    except Exception as e:
        frappe.log_error("Report error", str(e))

    # Include custom workspaces only
    try:
        custom_workspace = frappe.get_all(
            "Workspace", filters={"owner": ["!=", "Administrator"]}, fields=["name", "owner"])
        filtered = []
        for w in custom_workspace:
            if is_already_exported("Workspace", w.name):
                record_skipped("Workspace", w.name)
            else:
                filtered.append(w.name)
                if currentUser == w.owner:
                    users_customizations.setdefault("Workspace", []).append(w.name)
        if filtered:
            customizations_map["Workspace"] = filtered
    except Exception as e:
        frappe.log_error("Workspace error", str(e))

    # Include custom notifications only
    try:
        custom_notifications = frappe.get_all(
            "Notification", filters={"is_standard": "No"}, fields=["name", "owner"])
        filtered = []
        for n in custom_notifications:
            if is_already_exported("Notification", n.name):
                record_skipped("Notification", n.name)
            else:
                filtered.append(n.name)
                if currentUser == n.owner:
                    users_customizations.setdefault("Notification", []).append(n.name)
        if filtered:
            customizations_map["Notification"] = filtered
    except Exception as e:
        frappe.log_error("Notification error", str(e))
        
     # Include custom print formats only
    try:
        custom_print_format = frappe.get_all(
            "Print Format", filters={"module": module}, fields=["name", "owner"])
        filtered = []
        for pf in custom_print_format:
            if is_already_exported("Print Format", pf.name):
                record_skipped("Print Format", pf.name)
            else:
                filtered.append(pf.name)
                if currentUser == pf.owner:
                    users_customizations.setdefault("Print Format", []).append(pf.name)
        if filtered:
            customizations_map["Print Format"] = filtered
    except Exception as e:
        frappe.log_error("Print Format error", str(e))

    # Include custom doctypes
    try:
        custom_doctypes = frappe.get_all(
            "DocType", filters={"custom": 1}, fields=["name", "owner"])
        filtered = []
        for dt in custom_doctypes:
            if is_already_exported("DocType", dt.name):
                record_skipped("DocType", dt.name)
            else:
                filtered.append(dt.name)
                if currentUser == dt.owner:
                    users_customizations.setdefault("DocType", []).append(dt.name)
        if filtered:
            customizations_map["DocType"] = sorted(filtered)
    except Exception as e:
        frappe.log_error("Custom Doctype error", str(e))

    # Add other doctypes
    for doctype in doctypes:
        try:
            records = frappe.get_all(
                doctype, fields=["name", "owner"], order_by="modified desc")
            filtered = []
            for r in records:
                if is_already_exported(doctype, r.name):
                    record_skipped(doctype, r.name)
                else:
                    filtered.append(r.name)
                    if currentUser == r.owner:
                        users_customizations.setdefault(doctype, []).append(r.name)
            if filtered:
                customizations_map[doctype] = filtered
        except Exception as e:
            frappe.log_error(f"{doctype} error", str(e))

    # Format the fixtures block
    formatted_fixtures = "fixtures = [\n"
    for dt, names in customizations_map.items():
        if names:
            formatted_fixtures += "    {\n"
            formatted_fixtures += f"        \"dt\": \"{dt}\",\n"
            formatted_fixtures += "        \"filters\": [\n"
            formatted_fixtures += "            [\"name\", \"in\", [\n"
            for name in names:
                formatted_fixtures += f"                \"{name}\",\n"
            formatted_fixtures += "            ]]\n"
            formatted_fixtures += "        ]\n"
            formatted_fixtures += "    },\n"
    formatted_fixtures += "]\n"

    # Update customizations field in the DocType record
    if docname:
        try:
            doc = frappe.get_doc("Update hooks file", docname)
            doc.customizations = formatted_fixtures
            doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error("Doc update error", str(e))

    # Path to hooks.py
    if module == "Upande Hooks Updater":
        hooks_path = os.path.abspath(os.path.join(os.path.dirname(
            __file__), "..", "hooks.py"))
    else:
        hooks_path = os.path.abspath(os.path.join(os.path.dirname(
            __file__), "..", "..", "..", to_snake_case(module), to_snake_case(module), "hooks.py"))
        
    try:
        with open(hooks_path, "r") as f:
            lines = f.readlines()

        # Remove existing fixtures block
        start_idx = -1
        bracket_count = 0
        for idx, line in enumerate(lines):
            if "fixtures" in line and "=" in line and "[" in line:
                start_idx = idx
                bracket_count = line.count("[") - line.count("]")
                break

        if start_idx != -1:
            end_idx = start_idx
            for i in range(start_idx + 1, len(lines)):
                bracket_count += lines[i].count("[") - lines[i].count("]")
                end_idx = i
                if bracket_count <= 0:
                    break
            del lines[start_idx:end_idx + 1]

        lines.append("\n" + formatted_fixtures)

        with open(hooks_path, "w") as f:
            f.writelines(lines)

    except Exception as e:
        frappe.log_error("Hooks Write Error", str(e))
        return f"Failed to write to hooks.py: {e}"

    return {
        "fixtures": formatted_fixtures,
        "skipped": skipped_duplicates,
        "users_customizations": users_customizations
    }
