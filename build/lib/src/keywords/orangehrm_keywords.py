"""
Robot Framework Keyword Library bridging tasks.robot with the modular Page Object Model.
Manages browser initialization, custom exceptions, screenshots on failure, and safe teardown.
Exports strictly 2 Excel workbooks:
1. OrangeHRM_Data.xlsx (Timesheets)
2. Details.xlsx (10 My Info Worksheets, each with its own Attachments section & PDF hyperlinks)
"""

import logging
from typing import Optional
from robot.api.deco import keyword, library
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

from src.config import (
    BASE_URL,
    USERNAME,
    PASSWORD,
    TIMESHEET_DATA,
    MY_INFO_SECTIONS_DATA,
    SAMPLE_ATTACHMENT_PATH,
    OUTPUT_DIR,
)
from src.excel_manager import ExcelManager
from src.pages.login_page import LoginPage
from src.pages.time_page import TimePage
from src.pages.my_info_page import MyInfoPage
from src.pages.thunderbird_mailer import ThunderbirdMailer
from src.exceptions import (
    AuthenticationError,
    TimesheetAutomationError,
    MyInfoAutomationError,
    EmailAutomationError,
)

logger = logging.getLogger(__name__)


@library(scope="GLOBAL", auto_keywords=False)
class OrangeHRMKeywords:
    """Enterprise Keyword Library for OrangeHRM End-to-End RPA."""

    def __init__(self) -> None:
        self.driver: Optional[webdriver.Chrome] = None

    @keyword("Initialize Browser Session")
    def initialize_browser_session(self, headless: bool = False) -> None:
        """Initializes a configured Selenium 4 Chrome WebDriver instance."""
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=options)
        logger.info("Chrome WebDriver session initialized successfully.")

    @keyword("Execute Phase 1 Authentication")
    def execute_phase_1_authentication(self) -> None:
        """Executes Phase 1: Portal navigation, login, and Dashboard assertion."""
        if not self.driver:
            raise RuntimeError("WebDriver is not initialized.")
        try:
            login_page = LoginPage(self.driver)
            login_page.login(BASE_URL, USERNAME, PASSWORD)
        except AuthenticationError:
            self._capture_failure_state("phase1_auth_failure")
            raise
        except Exception as exc:
            self._capture_failure_state("phase1_auth_failure")
            raise AuthenticationError(f"Phase 1 Authentication failed: {exc}") from exc

    @keyword("Execute Phase 2 Time Module Automation And Scraping")
    def execute_phase_2_time_module(self) -> None:
        """
        Executes Phase 2: Navigates to My Timesheets, inputs 7 separate daily entries,
        validates save state, scrapes grid, and saves to 'OrangeHRM_Data.xlsx' (Workbook 1).
        """
        if not self.driver:
            raise RuntimeError("WebDriver is not initialized.")
        try:
            time_page = TimePage(self.driver)
            time_page.navigate_to_my_timesheets()
            time_page.enter_and_save_timesheet(TIMESHEET_DATA)
            scraped_timesheet = time_page.scrape_saved_timesheet()

            timesheet_excel_path = OUTPUT_DIR / "OrangeHRM_Data.xlsx"
            if timesheet_excel_path.exists():
                timesheet_excel_path.unlink()

            # Workbook 1: OrangeHRM_Data.xlsx (Strictly Timesheet Data)
            ExcelManager.save_to_sheet(
                file_path=timesheet_excel_path,
                sheet_name="Timesheet_Data",
                data=scraped_timesheet,
            )
        except TimesheetAutomationError:
            self._capture_failure_state("phase2_time_failure")
            raise
        except Exception as exc:
            self._capture_failure_state("phase2_time_failure")
            raise TimesheetAutomationError(
                f"Phase 2 Time Module failed: {exc}"
            ) from exc

    @keyword("Execute Phase 3 My Info Automation And Scraping")
    def execute_phase_3_my_info_module(self) -> None:
        """
        Executes Phase 3: Iterates through all 10 My Info sections, injects dummy data,
        uploads sample_attachment.pdf, and writes 10 worksheets into 'Details.xlsx' (Workbook 2),
        where each worksheet contains both the section's data AND its Attachments table with PDF hyperlinks.
        """
        if not self.driver:
            raise RuntimeError("WebDriver is not initialized.")
        try:
            my_info_page = MyInfoPage(self.driver)
            sections_map, attachments_by_section = (
                my_info_page.process_all_ten_sections(
                    sections_data=MY_INFO_SECTIONS_DATA,
                    attachment_file=SAMPLE_ATTACHMENT_PATH,
                )
            )

            details_excel_path = OUTPUT_DIR / "Details.xlsx"
            if details_excel_path.exists():
                details_excel_path.unlink()

            # Remove legacy Attachments.xlsx if it exists from previous runs so only 2 Excel files remain
            legacy_attachments_path = OUTPUT_DIR / "Attachments.xlsx"
            if legacy_attachments_path.exists():
                legacy_attachments_path.unlink()

            # Map each of the 10 sheet names to its corresponding attachment dictionary key
            section_to_attachment_key = {
                "Personal_Details": "1. Personal Details",
                "Contact_Details": "2. Contact Details",
                "Emergency_Contacts": "3. Emergency Contacts",
                "Dependents": "4. Dependents",
                "Immigration": "5. Immigration",
                "Job": "6. Job",
                "Salary": "7. Salary",
                "Report_To": "8. Report-to",
                "Qualifications": "9. Qualifications",
                "Memberships": "10. Memberships",
            }

            # Workbook 2: Details.xlsx (10 Worksheets, each with Section Data + Attachments + Hyperlink)
            for sheet_name, section_rows in sections_map.items():
                att_key = section_to_attachment_key.get(sheet_name, "")
                att_rows = attachments_by_section.get(att_key, [])

                ExcelManager.save_section_with_attachments(
                    file_path=details_excel_path,
                    sheet_name=sheet_name,
                    section_data=section_rows,
                    attachments_data=att_rows,
                    pdf_path=SAMPLE_ATTACHMENT_PATH,
                )

        except MyInfoAutomationError:
            self._capture_failure_state("phase3_my_info_failure")
            raise
        except Exception as exc:
            self._capture_failure_state("phase3_my_info_failure")
            raise MyInfoAutomationError(
                f"Phase 3 My Info Module failed: {exc}"
            ) from exc

    @keyword("Execute Phase 4 Email Reporting Via Thunderbird")
    def execute_phase_4_email_reporting(self) -> None:
        """
        Executes Phase 4: Dispatches Email 1 (Simple black-and-white HTML table + OrangeHRM_Data.xlsx)
        and Email 2 (Threaded Reply with Details.xlsx) via Mozilla Thunderbird desktop client.
        """
        try:
            mailer = ThunderbirdMailer()
            timesheet_excel = OUTPUT_DIR / "OrangeHRM_Data.xlsx"
            details_excel = OUTPUT_DIR / "Details.xlsx"

            mailer.send_timesheet_html_email(timesheet_excel)
            mailer.send_reply_with_details_excel(details_excel)
        except EmailAutomationError:
            raise
        except Exception as exc:
            raise EmailAutomationError(
                f"Phase 4 Thunderbird Email Reporting failed: {exc}"
            ) from exc

    @keyword("Close Browser Safely")
    def close_browser_safely(self) -> None:
        """Safely terminates the WebDriver session during Suite Teardown."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser session closed cleanly.")
            except WebDriverException as exc:
                logger.warning("Error while closing WebDriver: %s", exc)
            finally:
                self.driver = None

    def _capture_failure_state(self, prefix: str) -> None:
        """Captures a diagnostic screenshot into the output folder upon unexpected exception."""
        if self.driver:
            screenshot_path = OUTPUT_DIR / f"{prefix}.png"
            try:
                self.driver.save_screenshot(str(screenshot_path))
                logger.error("Saved diagnostic screenshot to %s", screenshot_path)
            except WebDriverException:
                pass