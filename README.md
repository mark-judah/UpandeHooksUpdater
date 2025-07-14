## Upande Hooks Updater & customization tracker
 
ERPNext often allows users and developers to make changes to their system through the Desk UI — including Custom Fields, Workflows, Print Formats, Workspaces, and more.

However, **these UI changes are not version-controlled by default** and are prone to being overwritten or lost during:
- Pulls from remote repositories
- App reinstallations
- Migration between environments
- Bench updates or restores

This repository addresses that issue by automating the **export of Desk-based customizations into `hooks.py` fixtures** using a custom Frappe script and workspace tool.

---

## 🔍 Problem

ERPNext UI customizations (like adding a field or modifying a form) are stored in the database. Unless exported manually or set as a fixture, these changes:

- Are **not included in git**,
- Do **not appear in PRs or commits**, and
- Are often **silently lost during deployments or syncs**.

ERPNext expects developers to export them using `bench export-fixtures`, which:
- Is **manual and error-prone**,
- Often exports more than necessary,
- Is unaware of the **user who made the change**, and
- Doesn't make it easy to **track which customizations belong to which app or developer**.

---

## ✅ Solution: Hooks Updater

This repo provides a tool that:

### 🔧 Auto-generates `fixtures` entries in your `hooks.py`

Based on:
- Custom Fields
- Workflows
- Reports
- Client/Server Scripts
- Workspaces
- Notifications
- Custom Doctypes
- Property Setters
- Print Formats
- Workflow Action Masters

### 👤 Filters by current user (optional)

So that you can:
- Only view **your own changes**,
- Track team member contributions,

### 🗃 Tracks skipped exports
To avoid duplicating already-exported files on disk, and logs what was skipped.
---

## 🚀 Usage

### 1. Install this app to your site
### 2. Open the Update Hooks File doctype
### 3. Enter the module name that you want to export
### 4. Click "Pull Latest Customizations"
### 5. Check if the hooks file has been updated
### 6. Run bench export-fixtures to save changes to disk.

