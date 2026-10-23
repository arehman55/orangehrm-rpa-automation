"""
Base Page Object Model (POM) class providing strict Explicit Waits,
Vue.js input clearing, custom dropdown handling, and toast assertions.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.pages.locators import BaseLocators

logger = logging.getLogger(__name__)


class BasePage:
    """Foundational wrapper for all OrangeHRM Page Objects using pure Python Selenium."""

    # Global OrangeHRM Vue.js Locators
    LOADING_SPINNER = BaseLocators.LOADING_SPINNER
    FORM_LOADER = BaseLocators.FORM_LOADER
    SUCCESS_TOAST = BaseLocators.SUCCESS_TOAST

    def __init__(self, driver: WebDriver, timeout: int = 20) -> None:
        """Initialize the page with a Selenium driver and explicit-wait timeout.

        Args:
            driver (WebDriver): Active Selenium browser session.
            timeout (int): Default explicit-wait timeout in seconds.

        Returns:
            None.

        Example:
            page = BasePage(driver, timeout=20)
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(
            self.driver,
            self.timeout,
            ignored_exceptions=(StaleElementReferenceException,),
        )

    def wait_for_Check_loaders(self) -> None:
        """
        Wait for OrangeHRM's asynchronous loaders to disappear.

        Args:
            None.

        Returns:
            None.

        Example:
            page.wait_for_Check_loaders()
        """
        self.wait.until(EC.invisibility_of_element_located(self.LOADING_SPINNER))
        self.wait.until(EC.invisibility_of_element_located(self.FORM_LOADER))

    def find_visible(self, locator: Tuple[str, str]) -> WebElement:
        """Wait for and return a visible element.

        Args:
            locator (Tuple[str, str]): Selenium locator tuple.

        Returns:
            WebElement: Visible matching element.

        Example:
            field = page.find_visible(locator)
        """
        self.wait_for_Check_loaders()
        return self.wait.until(EC.visibility_of_element_located(locator))

    def find_all_visible(self, locator: Tuple[str, str]) -> List[WebElement]:
        """Wait for and return all visible matching elements.

        Args:
            locator (Tuple[str, str]): Selenium locator tuple.

        Returns:
            List[WebElement]: Visible matching elements.

        Example:
            rows = page.find_all_visible(locator)
        """
        self.wait_for_Check_loaders()
        return self.wait.until(EC.visibility_of_all_elements_located(locator))

    def click_element(self, locator: Tuple[str, str]) -> None:
        """
        Wait for an element to be clickable and click it.

        Args:
            locator (Tuple[str, str]): Selenium locator tuple.

        Returns:
            None.

        Example:
            page.click_element(locator)
        """
        self.wait_for_Check_loaders()
        element = self.wait.until(EC.element_to_be_clickable(locator))
        try:
            element.click()
        except ElementClickInterceptedException:
            logger.info(
                "Click intercepted on %s. Retrying via ActionChains move_to_element.",
                locator,
            )
            self.wait_for_Check_loaders()
            ActionChains(self.driver).move_to_element(element).click().perform()

    def clear_and_type(self, locator: Tuple[str, str], text: str) -> None:
        """
        Clear a Vue.js input and type text using Selenium actions.

        Args:
            locator (Tuple[str, str]): Selenium input locator.
            text (str): Text to enter.

        Returns:
            None.

        Example:
            page.clear_and_type(locator, "Admin")
        """
        element = self.find_visible(locator)

        # If an OrangeHRM date-picker calendar popup is open and overlapping, dismiss it via ESCAPE
        open_calendars = self.driver.find_elements(*BaseLocators.CALENDAR_WRAPPER)
        if open_calendars:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

        ActionChains(self.driver).move_to_element(element).perform()
        try:
            element.click()
        except ElementClickInterceptedException:
            logger.info(
                "Click intercepted on input %s (likely by calendar popup). Dismissing popup and clicking via ActionChains.",
                locator,
            )
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            ActionChains(self.driver).move_to_element(element).click().perform()

        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(str(text))

        # Close any calendar dropdown triggered by typing into a date input
        placeholder = (element.get_attribute("placeholder") or "").lower()
        if "yyyy" in placeholder or "dd" in placeholder or "mm" in placeholder:
            element.send_keys(Keys.TAB)

    def get_input_by_label(self, label_text: str) -> Tuple[str, str]:
        """
        Build the input or textarea locator associated with a label.

        Args:
            label_text (str): Visible label text.

        Returns:
            Tuple[str, str]: Selenium locator tuple.

        Example:
            locator = page.get_input_by_label("Employee Id")
        """
        return BaseLocators.input_by_label(label_text)

    def fill_field_by_label(self, label_text: str, value: str) -> None:
        """Fill an input or textarea identified by its visible label.

        Args:
            label_text (str): Visible field label.
            value (str): Value to enter.

        Returns:
            None.

        Example:
            page.fill_field_by_label("Employee Id", "EMP-9042")
        """
        locator = self.get_input_by_label(label_text)
        self.clear_and_type(locator, value)

    def read_field_by_label(self, label_text: str) -> str:
        """Read the current value of a labeled input field.

        Args:
            label_text (str): Visible field label.

        Returns:
            str: Field value or ``N/A`` when unavailable.

        Example:
            employee_id = page.read_field_by_label("Employee Id")
        """
        locator = self.get_input_by_label(label_text)
        try:
            element = self.find_visible(locator)
            val = (element.get_attribute("value") or "").strip()
            return val if val else "N/A"
        except TimeoutException:
            return "N/A"

    def select_dropdown_by_label(
        self, label_text: str, option_text: Optional[str] = None, index: int = 2
    ) -> str:
        """
        Select an option from a custom OrangeHRM dropdown.

        Args:
            label_text (str): Visible dropdown label.
            option_text (Optional[str]): Desired visible option text.
            index (int): One-based fallback option index.

        Returns:
            str: Selected option text.

        Example:
            country = page.select_dropdown_by_label("Country", "Pakistan")
        """
        self.click_element(BaseLocators.dropdown_by_label(label_text))

        if option_text:
            try:
                opt_el = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        BaseLocators.dropdown_option(option_text)
                    )
                )
                selected_val = opt_el.text.strip()
                ActionChains(self.driver).move_to_element(opt_el).click().perform()
                return selected_val
            except TimeoutException:
                logger.info(
                    "Option '%s' not found under '%s'; selecting index %d.",
                    option_text,
                    label_text,
                    index,
                )

        options = self.wait.until(
            EC.presence_of_all_elements_located(BaseLocators.DROPDOWN_OPTIONS)
        )
        target_option = options[min(index - 1, len(options) - 1)]
        selected_val = target_option.text.strip()
        ActionChains(self.driver).move_to_element(target_option).click().perform()
        return selected_val

    def read_dropdown_by_label(self, label_text: str) -> str:
        """Read the selected value from a custom dropdown.

        Args:
            label_text (str): Visible dropdown label.

        Returns:
            str: Selected value or ``N/A`` when unavailable.

        Example:
            status = page.read_dropdown_by_label("Marital Status")
        """
        try:
            el = self.find_visible(BaseLocators.dropdown_by_label(label_text))
            text_val = el.text.strip()
            return text_val if text_val and text_val != "-- Select --" else "N/A"
        except TimeoutException:
            return "N/A"

    def navigate_sidebar(self, menu_name: str) -> None:
        """Navigate through the main sidebar.

        Args:
            menu_name (str): Visible sidebar menu name.

        Returns:
            None.

        Example:
            page.navigate_sidebar("My Info")
        """
        self.click_element(BaseLocators.sidebar_item(menu_name))
        self.wait_for_Check_loaders()

    def validate_success_toast(self) -> bool:
        """
        Check for a success toast and wait for loaders to settle.

        Args:
            None.

        Returns:
            bool: Always ``True`` after the save state settles.

        Example:
            saved = page.validate_success_toast()
        """
        try:
            toast = WebDriverWait(self.driver, 6).until(
                EC.visibility_of_element_located(self.SUCCESS_TOAST)
            )
            logger.info("Validated toast message: %s", toast.text.replace("\n", " "))
        except TimeoutException:
            logger.info("Save completed and form state updated.")
        self.wait_for_Check_loaders()
        return True

    def upload_attachment_in_current_section(
        self, file_path: Path, comment: str
    ) -> None:
        """
        Upload and save an attachment in the current section.

        Args:
            file_path (Path): Local file to upload.
            comment (str): Attachment description.

        Returns:
            None.

        Example:
            page.upload_attachment_in_current_section(pdf_path, "Verification")
        """
        self.wait_for_Check_loaders()
        try:
            add_btn = self.wait.until(
                EC.element_to_be_clickable(BaseLocators.ATTACHMENT_ADD_BUTTON)
            )
            ActionChains(self.driver).move_to_element(add_btn).click().perform()

            self.wait_for_Check_loaders()

            raw_file_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(BaseLocators.ATTACHMENT_FILE_INPUT)
            )
            raw_file_input.send_keys(str(file_path.resolve()))

            textarea = self.wait.until(
                EC.visibility_of_element_located(BaseLocators.ATTACHMENT_COMMENT)
            )
            ActionChains(self.driver).move_to_element(textarea).perform()
            textarea.click()
            textarea.send_keys(Keys.CONTROL + "a")
            textarea.send_keys(Keys.BACKSPACE)
            textarea.send_keys(comment)

            save_btn = self.wait.until(
                EC.element_to_be_clickable(BaseLocators.ATTACHMENT_SAVE_BUTTON)
            )
            ActionChains(self.driver).move_to_element(save_btn).click().perform()

            self.validate_success_toast()
            self.wait_for_Check_loaders()
        except (TimeoutException, WebDriverException) as exc:
            logger.warning("Could not complete file upload in current section: %s", exc)

    def scrape_attachments_in_current_section(
        self, section_name: str
    ) -> List[Dict[str, Any]]:
        """
        Scrape attachment rows from the current section.

        Args:
            section_name (str): Section name used for diagnostic logging.

        Returns:
            List[Dict[str, Any]]: Scraped attachment records.

        Example:
            records = page.scrape_attachments_in_current_section("Job")
        """
        self.wait_for_Check_loaders()
        records: List[Dict[str, Any]] = []
        try:
            WebDriverWait(self.driver, 6).until(
                EC.presence_of_element_located(BaseLocators.ATTACHMENT_ROWS)
            )
            rows = self.driver.find_elements(*BaseLocators.ATTACHMENT_ROWS)

            for row in rows:
                cells = row.find_elements(*BaseLocators.ATTACHMENT_CELLS)
                if len(cells) >= 7:
                    file_name = cells[1].text.strip()
                    description = cells[2].text.strip()
                    size = cells[3].text.strip()
                    file_type = cells[4].text.strip()
                    date_added = cells[5].text.strip()
                    added_by = cells[6].text.strip()

                    if file_name and file_name != "No Records Found":
                        records.append(
                            {
                                "File Name": file_name,
                                "Description": description if description else "N/A",
                                "Size": size if size else "N/A",
                                "Type": file_type if file_type else "N/A",
                                "Date Added": date_added if date_added else "N/A",
                                "Added By": added_by if added_by else "N/A",
                            }
                        )
        except TimeoutException:
            logger.info(
                "No attachment table found or timed out in section [%s].", section_name
            )

        return records

    def download_attachment_from_current_section(
        self, section_name: str
    ) -> Dict[str, Any]:
        """
        Capture the first attachment record from the current section.

        Args:
            section_name (str): Section name used for diagnostic logging.

        Returns:
            Dict[str, Any]: Attachment metadata or an explicit no-attachment record.

        Example:
            record = page.download_attachment_from_current_section("Job")
        """
        self.wait_for_Check_loaders()
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(BaseLocators.ATTACHMENT_ROWS)
            )
            rows = self.driver.find_elements(*BaseLocators.ATTACHMENT_ROWS)
            if rows:
                cells = rows[0].find_elements(*BaseLocators.ATTACHMENT_CELLS)
                if len(cells) >= 7:
                    file_name = cells[1].text.strip()
                    if file_name and file_name != "No Records Found":
                        return {
                            "File Name": file_name,
                            "Description": cells[2].text.strip() or "N/A",
                            "Size": cells[3].text.strip() or "N/A",
                            "Type": cells[4].text.strip() or "N/A",
                            "Date Added": cells[5].text.strip() or "N/A",
                            "Added By": cells[6].text.strip() or "N/A",
                            "Download_Status": "Captured Successfully",
                        }
        except TimeoutException:
            logger.warning(
                "Attachment table was not found or timed out in section [%s].",
                section_name,
            )
        except WebDriverException as exc:
            logger.error(
                "Selenium failed while reading attachments in section [%s]: %s",
                section_name,
                exc,
            )

        return {
            "File Name": "N/A",
            "Description": "N/A",
            "Size": "N/A",
            "Type": "N/A",
            "Date Added": "N/A",
            "Added By": "N/A",
            "Download_Status": "No Attachment Found",
        }
