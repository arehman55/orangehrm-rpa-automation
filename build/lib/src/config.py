"""
Configuration and static test data module for OrangeHRM Automation.
Separates test data and environment constants from page logic.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
DEVDATA_DIR = BASE_DIR / "devdata"

# Ensure directories exist prior to execution
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEVDATA_DIR.mkdir(parents=True, exist_ok=True)

# Portal Credentials & URLs
BASE_URL = "https://opensource-demo.orangehrmlive.com/web/index.php/auth/login"
USERNAME = os.getenv("ORANGEHRM_USER", "Admin")
PASSWORD = os.getenv("ORANGEHRM_PASS", "admin123")

# Excel Output Paths
PRIMARY_EXCEL_PATH = OUTPUT_DIR / "OrangeHRM_Data.xlsx"
ATTACHMENTS_EXCEL_PATH = OUTPUT_DIR / "OrangeHRM_Attachments.xlsx"
SAMPLE_ATTACHMENT_PATH = DEVDATA_DIR / "sample_attachment.pdf"

# Fallback: if sample_attachment.pdf is missing, create a valid dummy PDF
if not SAMPLE_ATTACHMENT_PATH.exists():
    SAMPLE_ATTACHMENT_PATH.write_bytes(
        b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
    )

# Phase 2: Timesheet Dummy Data
TIMESHEET_DATA = {
    "project_search_hint": "Apache",
    "hours": {
        "Mon": "08:00",
        "Tue": "08:00",
        "Wed": "07:30",
        "Thu": "08:00",
        "Fri": "08:00",
        "Sat": "04:00",
        "Sun": "00:00",
    },
}

# Phase 3: 10 Sections of "My Info" Dummy Data
MY_INFO_SECTIONS_DATA = {
    "Personal_Details": {
        "first_name": "Muhammad",
        "middle_name": "Abdul",
        "last_name": "Rehman",
        "employee_id": "EMP-9042",
        "other_id": "PK-44210",
        "drivers_license": "DL-998877",
        "license_expiry": "2028-12-31",
        "nationality": "Pakistani",
        "marital_status": "Single",
        "dob": "1999-05-15",
    },
    "Contact_Details": {
        "street_1": "142 Tech Boulevard, Johar Town",
        "street_2": "Street 400",
        "city": "Lahore",
        "state": "Punjab",
        "zip_code": "54000",
        "country": "Pakistan",
        "mobile": "+923001234567",
        "work_email": "test@gmail.com",
    },
    "Emergency_Contacts": {
        "name": "AbdulRehman",
        "relationship": "Myself",
        "home_telephone": "04235551234",
        "mobile": "+923219876543",
        "work_telephone": "04235559999",
    },
    "Dependents": {
        "name": "AbdulRehman",
        "relationship": "Myself",
        "dob": "2004-08-10",
    },
    "Immigration": {
        "document_type": "Passport",
        "number": "PK9988112",
        "issued_date": "2022-01-10",
        "expiry_date": "2032-01-09",
        "eligible_status": "Verified Citizen",
        "issued_by": "Pakistan",
        "eligible_review_date": "2026-12-01",
        "comments": "Primary international travel document.",
    },
    "Job": {
        # Note: Job tab fields are read-only for self-service users in OrangeHRM,
        # so we validate state, upload a verification contract, and scrape active job parameters.
        "verification_note": "Job contract verified via RPA audit."
    },
    "Salary": {
        # Salary fields are strictly read-only in My Info; we scrape assigned salary components & direct deposit.
        "audit_status": "Verified"
    },
    "Report_To": {
        # Report-to hierarchy is read-only under My Info; we scrape assigned supervisors/subordinates.
        "hierarchy_check": "Completed"
    },
    "Qualifications": {
        "company": "Enterprise Automation Labs",
        "job_title": "Senior RPA Engineer",
        "from_date": "2024-01-01",
        "to_date": "2026-09-01",
        "comment": "Architected Selenium 4 and Sema4.ai automation pipelines.",
    },
    "Memberships": {
        "membership_index": 1,  # Selects the first available membership in dropdown
        "subscription_paid_by": "Company",
        "subscription_amount": "250",
        "currency_index": 1,
        "commence_date": "2025-01-01",
        "renewal_date": "2027-01-01",
    },
}

# ==============================================================================
# PHASE 4: THUNDERBIRD EMAIL AUTOMATION CONFIGURATION
# ==============================================================================
TEAM_LEAD_EMAIL = "fa22-bcs-260@students.cuisahiwal.edu.pk"
EMAIL_1_SUBJECT = "OrangeHRM RPA Report: Weekly Timesheet Automation Summary"

# Standard Windows installation paths for Mozilla Thunderbird
THUNDERBIRD_PATHS = [
    Path(r"C:\Program Files\Mozilla Thunderbird\thunderbird.exe"),
    Path(r"C:\Program Files (x86)\Mozilla Thunderbird\thunderbird.exe"),
]