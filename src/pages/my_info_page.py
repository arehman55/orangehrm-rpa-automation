"""
Phase 3: 'My Info' Module Automation & Scraping Page Object Model.
Automates data entry, PDF attachment uploads, save validations, and scraping across all 10 sections.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from src.base_page import BasePage

logger = logging.getLogger(__name__)


class MyInfoPage(BasePage):
    """Page Object for the 10 sub-sections inside the OrangeHRM 'My Info' module."""

    TAB_LINK_TPL = "//div[@role='tablist']//a[normalize-space()='{tab_name}']"
    PRIMARY_SAVE_BTN = (
        By.XPATH,
        "(//form[@class='oxd-form']//button[@type='submit' and normalize-space()='Save'])[1]",
    )

    def navigate_to_my_info(self) -> None:
        """Opens the My Info module from the main left sidebar."""
        logger.info("Navigating to My Info module...")
        self.navigate_sidebar("My Info")
        self.wait_for_Check_loaders()

    def open_sub_tab(self, tab_name: str) -> None:
        """Clicks one of the 10 left-hand tabs inside My Info."""
        logger.info("Switching to My Info section: [%s]", tab_name)
        locator = (By.XPATH, self.TAB_LINK_TPL.format(tab_name=tab_name))
        self.click_element(locator)
        self.wait_for_Check_loaders()

    def process_all_ten_sections(
        self,
        sections_data: Dict[str, Dict[str, Any]],
        attachment_file: Path,
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
        """
        Executes data entry, PDF file upload, validation, and data scraping across all 10 My Info sections.
        Returns:
            Tuple containing:
            - Dict mapping each of the 10 sheet names to its scraped data rows.
            - Dict mapping each of the 10 section headings to its scraped attachment rows.
        """
        self.navigate_to_my_info()

        all_sections_scraped: Dict[str, List[Dict[str, Any]]] = {}
        all_attachments_by_section: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Personal Details
        sec_1, att_1 = self._handle_personal_details(
            sections_data["Personal_Details"], attachment_file
        )
        all_sections_scraped["Personal_Details"] = sec_1
        all_attachments_by_section["1. Personal Details"] = att_1

        # 2. Contact Details
        sec_2, att_2 = self._handle_contact_details(
            sections_data["Contact_Details"], attachment_file
        )
        all_sections_scraped["Contact_Details"] = sec_2
        all_attachments_by_section["2. Contact Details"] = att_2

        # 3. Emergency Contacts
        sec_3, att_3 = self._handle_emergency_contacts(
            sections_data["Emergency_Contacts"], attachment_file
        )
        all_sections_scraped["Emergency_Contacts"] = sec_3
        all_attachments_by_section["3. Emergency Contacts"] = att_3

        # 4. Dependents
        sec_4, att_4 = self._handle_dependents(
            sections_data["Dependents"], attachment_file
        )
        all_sections_scraped["Dependents"] = sec_4
        all_attachments_by_section["4. Dependents"] = att_4

        # 5. Immigration
        sec_5, att_5 = self._handle_immigration(
            sections_data["Immigration"], attachment_file
        )
        all_sections_scraped["Immigration"] = sec_5
        all_attachments_by_section["5. Immigration"] = att_5

        # 6. Job
        sec_6, att_6 = self._handle_job_section(attachment_file)
        all_sections_scraped["Job"] = sec_6
        all_attachments_by_section["6. Job"] = att_6

        # 7. Salary
        sec_7, att_7 = self._handle_salary_section(attachment_file)
        all_sections_scraped["Salary"] = sec_7
        all_attachments_by_section["7. Salary"] = att_7

        # 8. Report-to
        sec_8, att_8 = self._handle_report_to_section(attachment_file)
        all_sections_scraped["Report_To"] = sec_8
        all_attachments_by_section["8. Report-to"] = att_8

        # 9. Qualifications
        sec_9, att_9 = self._handle_qualifications(
            sections_data["Qualifications"], attachment_file
        )
        all_sections_scraped["Qualifications"] = sec_9
        all_attachments_by_section["9. Qualifications"] = att_9

        # 10. Memberships
        sec_10, att_10 = self._handle_memberships(
            sections_data["Memberships"], attachment_file
        )
        all_sections_scraped["Memberships"] = sec_10
        all_attachments_by_section["10. Memberships"] = att_10

        return all_sections_scraped, all_attachments_by_section

    # -------------------------------------------------------------------------
    # Individual Section Handlers (1 to 10)
    # -------------------------------------------------------------------------

    def _handle_personal_details(
        self, data: Dict[str, Any], attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 1: Personal Details"""
        self.open_sub_tab("Personal Details")

        self.clear_and_type((By.NAME, "firstName"), data["first_name"])
        self.clear_and_type((By.NAME, "middleName"), data["middle_name"])
        self.clear_and_type((By.NAME, "lastName"), data["last_name"])
        self.fill_field_by_label("Employee Id", data["employee_id"])
        self.fill_field_by_label("Other Id", data["other_id"])
        self.fill_field_by_label("Driver's License Number", data["drivers_license"])
        self.fill_field_by_label("License Expiry Date", data["license_expiry"])
        self.select_dropdown_by_label("Nationality", data["nationality"])
        self.select_dropdown_by_label("Marital Status", data["marital_status"])
        self.fill_field_by_label("Date of Birth", data["dob"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.validate_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Personal Details - Official ID Document"
        )

        scraped = [
            {
                "First Name": self.find_visible((By.NAME, "firstName")).get_attribute(
                    "value"
                ),
                "Middle Name": self.find_visible((By.NAME, "middleName")).get_attribute(
                    "value"
                ),
                "Last Name": self.find_visible((By.NAME, "lastName")).get_attribute(
                    "value"
                ),
                "Employee Id": self.read_field_by_label("Employee Id"),
                "Other Id": self.read_field_by_label("Other Id"),
                "Driver's License Number": self.read_field_by_label(
                    "Driver's License Number"
                ),
                "License Expiry Date": self.read_field_by_label("License Expiry Date"),
                "Nationality": self.read_dropdown_by_label("Nationality"),
                "Marital Status": self.read_dropdown_by_label("Marital Status"),
                "Date of Birth": self.read_field_by_label("Date of Birth"),
            }
        ]
        attachments = [
            self.download_attachment_from_current_section("Personal Details")
        ]
        return scraped, attachments

    def _handle_contact_details(
        self, data: Dict[str, Any], attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 2: Contact Details"""
        self.open_sub_tab("Contact Details")

        self.fill_field_by_label("Street 1", data["street_1"])
        self.fill_field_by_label("Street 2", data["street_2"])
        self.fill_field_by_label("City", data["city"])
        self.fill_field_by_label("State/Province", data["state"])
        self.fill_field_by_label("Zip/Postal Code", data["zip_code"])
        self.select_dropdown_by_label("Country", data["country"])
        self.fill_field_by_label("Mobile", data["mobile"])
        self.fill_field_by_label("Work Email", data["work_email"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.validate_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Contact Details - Residence Verification PDF"
        )

        scraped = [
            {
                "Street 1": self.read_field_by_label("Street 1"),
                "Street 2": self.read_field_by_label("Street 2"),
                "City": self.read_field_by_label("City"),
                "State/Province": self.read_field_by_label("State/Province"),
                "Zip/Postal Code": self.read_field_by_label("Zip/Postal Code"),
                "Country": self.read_dropdown_by_label("Country"),
                "Mobile": self.read_field_by_label("Mobile"),
                "Work Email": self.read_field_by_label("Work Email"),
            }
        ]
        attachments = [self.download_attachment_from_current_section("Contact Details")]
        return scraped, attachments

    def _handle_emergency_contacts(
        self, data: Dict[str, Any], attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 3: Emergency Contacts"""
        self.open_sub_tab("Emergency Contacts")

        add_btn = (
            By.XPATH,
            "//h6[normalize-space()='Assigned Emergency Contacts']/ancestor::div[contains(@class, 'orangehrm-action-header')]//button",
        )
        self.click_element(add_btn)

        self.fill_field_by_label("Name", data["name"])
        self.fill_field_by_label("Relationship", data["relationship"])
        self.fill_field_by_label("Home Telephone", data["home_telephone"])
        self.fill_field_by_label("Mobile", data["mobile"])
        self.fill_field_by_label("Work Telephone", data["work_telephone"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.validate_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Emergency Contacts - Consent PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Emergency Contacts",
            ["Name", "Relationship", "Home Telephone", "Mobile", "Work Telephone"],
        )
        attachments = [
            self.download_attachment_from_current_section("Emergency Contacts")
        ]
        return scraped, attachments

    def _handle_dependents(
        self, data: Dict[str, Any], attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 4: Dependents"""
        self.open_sub_tab("Dependents")

        add_btn = (
            By.XPATH,
            "//h6[normalize-space()='Assigned Dependents']/ancestor::div[contains(@class, 'orangehrm-action-header')]//button",
        )
        self.click_element(add_btn)

        self.fill_field_by_label("Name", data["name"])
        self.select_dropdown_by_label("Relationship", data["relationship"])
        self.fill_field_by_label("Date of Birth", data["dob"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.validate_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Dependents - Birth Certificate PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Dependents", ["Name", "Relationship", "Date of Birth"]
        )
        attachments = [self.download_attachment_from_current_section("Dependents")]
        return scraped, attachments

    def _handle_immigration(
        self, data: Dict[str, Any], attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 5: Immigration"""
        self.open_sub_tab("Immigration")

        add_btn = (
            By.XPATH,
            "//h6[normalize-space()='Assigned Immigration Records']/ancestor::div[contains(@class, 'orangehrm-action-header')]//button",
        )
        self.click_element(add_btn)

        self.fill_field_by_label("Number", data["number"])
        self.fill_field_by_label("Issued Date", data["issued_date"])
        self.fill_field_by_label("Expiry Date", data["expiry_date"])
        self.fill_field_by_label("Eligible Status", data["eligible_status"])
        self.select_dropdown_by_label("Issued By", data["issued_by"])
        self.fill_field_by_label("Eligible Review Date", data["eligible_review_date"])
        self.fill_field_by_label("Comments", data["comments"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.validate_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Immigration - Scanned Passport PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Immigration Records",
            ["Document", "Number", "Issued By", "Issued Date", "Expiry Date"],
        )
        attachments = [self.download_attachment_from_current_section("Immigration")]
        return scraped, attachments

    def _handle_job_section(
        self, attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 6: Job (Scrapes job details + uploads attachment if enabled)"""
        self.open_sub_tab("Job")

        # Upload attachment if the Attachments header is present on the Job tab
        self._try_upload_attachment(attachment_file, "Job - Employment Contract PDF")

        scraped = [
            {
                "Joined Date": self.read_field_by_label("Joined Date"),
                "Job Title": self.read_dropdown_by_label("Job Title"),
                "Job Category": self.read_dropdown_by_label("Job Category"),
                "Sub Unit": self.read_dropdown_by_label("Sub Unit"),
                "Location": self.read_dropdown_by_label("Location"),
                "Employment Status": self.read_dropdown_by_label("Employment Status"),
            }
        ]
        attachments = [self.download_attachment_from_current_section("Job")]
        return scraped, attachments

    def _handle_salary_section(
        self, attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 7: Salary (Uploads Salary Slip attachment + scrapes components)"""
        self.open_sub_tab("Salary")

        self._try_upload_attachment(
            attachment_file, "Salary - Approved Compensation PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Salary Components",
            [
                "Salary Component",
                "Amount",
                "Currency",
                "Pay Frequency",
                "Direct Deposit Amount",
            ],
        )
        attachments = [self.download_attachment_from_current_section("Salary")]
        return scraped, attachments

    def _handle_report_to_section(
        self, attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 8: Report-to (Uploads Hierarchy attachment + scrapes supervisors)"""
        self.open_sub_tab("Report-to")

        self._try_upload_attachment(
            attachment_file, "Report-to - Reporting Line Approval PDF"
        )

        supervisors = self._scrape_generic_section_table(
            "Assigned Supervisors", ["Name", "Reporting Method"]
        )
        attachments = [self.download_attachment_from_current_section("Report-to")]
        return supervisors, attachments

    def _handle_qualifications(
        self, data: Dict[str, Any], attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 9: Qualifications (Work Experience + PDF Attachment)"""
        self.open_sub_tab("Qualifications")

        add_work_exp_btn = (
            By.XPATH,
            "//h6[normalize-space()='Work Experience']/ancestor::div[contains(@class, 'orangehrm-action-header')]//button",
        )
        self.click_element(add_work_exp_btn)

        self.fill_field_by_label("Company", data["company"])
        self.fill_field_by_label("Job Title", data["job_title"])
        self.fill_field_by_label("From", data["from_date"])
        self.fill_field_by_label("To", data["to_date"])
        self.fill_field_by_label("Comment", data["comment"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.validate_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Qualifications - Experience Certificate PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Work Experience",
            ["Company", "Job Title", "From", "To", "Comment"],
        )
        attachments = [self.download_attachment_from_current_section("Qualifications")]
        return scraped, attachments

    def _handle_memberships(
        self, data: Dict[str, Any], attachment_file: Path
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Section 10: Memberships"""
        self.open_sub_tab("Memberships")

        add_btn = (
            By.XPATH,
            "//h6[normalize-space()='Assigned Memberships']/ancestor::div[contains(@class, 'orangehrm-action-header')]//button",
        )
        self.click_element(add_btn)

        self.select_dropdown_by_label("Membership", index=2)
        self.select_dropdown_by_label(
            "Subscription Paid By", data["subscription_paid_by"]
        )
        self.fill_field_by_label("Subscription Amount", data["subscription_amount"])
        self.select_dropdown_by_label("Currency", index=2)
        self.fill_field_by_label("Subscription Commence Date", data["commence_date"])
        self.fill_field_by_label("Subscription Renewal Date", data["renewal_date"])

        self.click_element(self.PRIMARY_SAVE_BTN)
        self.validate_success_toast()

        self.upload_attachment_in_current_section(
            attachment_file, "Memberships - Subscription Receipt PDF"
        )

        scraped = self._scrape_generic_section_table(
            "Assigned Memberships",
            [
                "Membership",
                "Subscription Paid By",
                "Subscription Amount",
                "Currency",
                "Subscription Commence Date",
                "Subscription Renewal Date",
            ],
        )
        attachments = [self.download_attachment_from_current_section("Memberships")]
        return scraped, attachments

    def _try_upload_attachment(self, file_path: Path, comment: str) -> None:
        """Uploads an attachment if the current tab has an '+ Add' button under Attachments."""
        add_btn_xpath = "//h6[normalize-space()='Attachments']/ancestor::div[contains(@class, 'orangehrm-action-header')]//button"
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, add_btn_xpath))
            )
            self.upload_attachment_in_current_section(file_path, comment)
        except TimeoutException:
            logger.info(
                "No editable Attachment widget on this read-only tab; skipping upload."
            )

    def _scrape_generic_section_table(
        self, header_title: str, columns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Scrapes any OrangeHRM `oxd-table` positioned immediately below a given `h6` section header.
        """
        self.wait_for_Check_loaders()
        rows_xpath = (
            f"//h6[normalize-space()='{header_title}']"
            f"/ancestor::div[contains(@class, 'orangehrm-action-header') or contains(@class, 'orangehrm-horizontal-padding')]"
            f"/following-sibling::div[contains(@class, 'orangehrm-container')][1]"
            f"//div[@class='oxd-table-body']//div[@role='row']"
        )
        rows = self.driver.find_elements(By.XPATH, rows_xpath)
        results: List[Dict[str, Any]] = []

        for row in rows:
            cells = row.find_elements(By.XPATH, ".//div[@role='cell']")
            if len(cells) > 1:
                record: Dict[str, Any] = {}
                for i, col_name in enumerate(columns):
                    cell_idx = i + 1
                    record[col_name] = (
                        cells[cell_idx].text.strip() if cell_idx < len(cells) else ""
                    )
                results.append(record)

        if not results:
            results.append({col: "No Records Found" for col in columns})
        return results
