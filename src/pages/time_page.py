"""
Phase 2: 'Time' Module Automation & Scraping Page Object Model.
Handles the exact OrangeHRM workflow using 100% Pure Python Selenium (ActionChains)
without any JavaScript injections:
1. Click Edit on /viewMyTimesheet
2. Click the '+' button next to 'Add Row' for each subsequent day (Mon -> Sun, 7 separate saves)
3. Select unique Project & Activity per row
4. Enter hours only for the target day column
5. Click Save -> Wait for redirect back to /viewMyTimesheet -> Validate Edit button
6. Scrape all 7 saved rows into structured Excel format.
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from src.base_page import BasePage
from src.exceptions import TimesheetAutomationError

logger = logging.getLogger(__name__)


class TimePage(BasePage):
    """Page Object for OrangeHRM Time & My Timesheets module using pure Python Selenium."""

    # Navigation Locators
    TIMESHEETS_TOP_MENU = (
        By.XPATH,
        "//nav[@aria-label='Topbar Menu']//span[contains(normalize-space(), 'Timesheets')]",
    )
    MY_TIMESHEETS_OPTION = (
        By.XPATH,
        "//ul[@class='oxd-dropdown-menu']//a[normalize-space()='My Timesheets']",
    )

    # View / Edit State Buttons
    EDIT_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Edit']",
    )
    CREATE_TIMESHEET_BUTTON = (
        By.XPATH,
        "//button[normalize-space()='Create Timesheet']",
    )
    SAVE_TIMESHEET_BUTTON = (
        By.XPATH,
        "//button[@type='submit' and normalize-space()='Save']",
    )

    # Only count actual data rows (rows containing a Project input), excluding the trailing 'Add Row' (+) row inside tbody!
    EDITABLE_DATA_ROWS = (
        By.XPATH,
        "//table[contains(@class, 'orangehrm-timesheet-table')]//tbody/tr[.//input[contains(@placeholder, 'Type for hints')]]",
    )

    # Exact locator for the '+' icon button next to 'Add Row'
    ADD_ROW_PLUS_BUTTON = (
        By.XPATH,
        "//table[contains(@class, 'orangehrm-timesheet-table')]//td[contains(normalize-space(), 'Add Row')]//button | //table[contains(@class, 'orangehrm-timesheet-table')]//button[.//i[contains(@class, 'bi-plus')]]",
    )

    DELETE_ROW_BUTTONS = (
        By.XPATH,
        "//table[contains(@class, 'orangehrm-timesheet-table')]//tbody//i[contains(@class, 'bi-trash')]/ancestor::button",
    )

    # Dropdown Option Locators (Active Listbox)
    AUTOCOMPLETE_VALID_OPTIONS = (
        By.XPATH,
        "//div[@role='listbox']//div[@role='option' and not(contains(normalize-space(), 'Searching')) and not(contains(normalize-space(), 'No Records Found'))]",
    )
    ACTIVITY_VALID_OPTIONS = (
        By.XPATH,
        "//div[@role='listbox']//div[@role='option' and not(contains(normalize-space(), '-- Select --')) and not(contains(normalize-space(), 'No Records Found'))]",
    )

    # Read-Only View Table Locators for Final Scraping
    SAVED_TABLE_HEADERS = (
        By.XPATH,
        "//table[contains(@class, 'orangehrm-timesheet-table')]//thead//th",
    )
    SAVED_TABLE_ROWS = (
        By.XPATH,
        "//table[contains(@class, 'orangehrm-timesheet-table')]//tbody//tr[not(contains(@class, '--total'))]",
    )

    def navigate_to_my_timesheets(self) -> None:
        """Navigates to Time -> Timesheets -> My Timesheets and waits for the view page."""
        logger.info("Navigating to Time -> Timesheets -> My Timesheets...")
        try:
            self.navigate_sidebar("Time")
            self.click_element(self.TIMESHEETS_TOP_MENU)
            self.click_element(self.MY_TIMESHEETS_OPTION)
            self.wait_for_Check_loaders()

            # If timesheet is not yet created for the current week, click 'Create Timesheet'
            try:
                create_btn = WebDriverWait(self.driver, 4).until(
                    EC.element_to_be_clickable(self.CREATE_TIMESHEET_BUTTON)
                )
                logger.info("Clicking 'Create Timesheet' for current period...")
                ActionChains(self.driver).move_to_element(create_btn).click().perform()
                self.wait_for_Check_loaders()
            except TimeoutException:
                pass

            # Ensure the 'Edit' button is visible on /viewMyTimesheet
            self.find_visible(self.EDIT_BUTTON)
            logger.info(
                "Successfully loaded My Timesheets view (%s).", self.driver.current_url
            )
        except Exception as exc:
            raise TimesheetAutomationError(
                f"Failed to navigate to My Timesheets: {exc}"
            ) from exc

    def enter_and_save_timesheet(self, timesheet_data: Dict[str, Any]) -> None:
        """
        Performs 7 separate save cycles (Monday through Sunday) using pure Selenium actions.
        """
        days_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hours_map = timesheet_data.get("hours", {})
        used_pairs: Set[Tuple[str, str]] = set()

        for day_idx, day_name in enumerate(days_order):
            row_num = day_idx + 1
            hour_val = hours_map.get(day_name, "08:00")
            if hour_val in ("00:00", "0", ""):
                hour_val = "04:00"

            logger.info(
                "========== [Timesheet Entry %d/7 | Day: %s | Hours: %s] ==========",
                row_num,
                day_name,
                hour_val,
            )

            try:
                # STEP 1: Click 'Edit' on /viewMyTimesheet to enter Edit mode
                self._enter_edit_mode()

                # STEP 2: Prepare the target row
                if day_idx == 0:
                    self._reset_to_single_clean_row()
                else:
                    self._click_add_row_plus_button(expected_data_rows=row_num)

                # STEP 3: Select a unique Project + Activity in the target data row
                self._populate_project_and_activity(row_num, used_pairs)

                # STEP 4: Enter hours ONLY in the current day's column
                self._input_hours_for_day(row_num, day_idx, hour_val)

                # STEP 5: Click Save and validate redirect back to /viewMyTimesheet
                self._save_and_confirm_redirect(row_num, day_name)

            except Exception as exc:
                logger.error(
                    "Failed during Timesheet Entry %d (%s) at URL '%s': %s",
                    row_num,
                    day_name,
                    self.driver.current_url,
                    exc,
                )
                raise TimesheetAutomationError(
                    f"Timesheet Entry {row_num} ({day_name}) failed: {exc}"
                ) from exc

        logger.info(
            "Successfully completed and validated all 7 separate daily Timesheet entries!"
        )

    def _enter_edit_mode(self) -> None:
        """
        Waits for the 'Edit' button on /viewMyTimesheet and clicks it using ActionChains.
        """
        self.wait_for_Check_loaders()
        edit_btn = self.wait.until(EC.element_to_be_clickable(self.EDIT_BUTTON))
        try:
            ActionChains(self.driver).move_to_element(edit_btn).click().perform()
        except ElementClickInterceptedException:
            self.wait_for_Check_loaders()
            ActionChains(self.driver).move_to_element(edit_btn).click().perform()

        self.wait_for_Check_loaders()
        self.wait.until(EC.visibility_of_element_located(self.SAVE_TIMESHEET_BUTTON))
        self.wait.until(EC.presence_of_element_located(self.ADD_ROW_PLUS_BUTTON))

    def _reset_to_single_clean_row(self) -> None:
        """Deletes all pre-existing rows in the timesheet using pure Selenium clicks."""
        self.wait_for_Check_loaders()
        delete_btns = self.driver.find_elements(*self.DELETE_ROW_BUTTONS)
        if delete_btns:
            logger.info(
                "Clearing %d pre-existing timesheet data row(s)...", len(delete_btns)
            )
            for _ in range(len(delete_btns)):
                current_del_btns = self.driver.find_elements(*self.DELETE_ROW_BUTTONS)
                if not current_del_btns:
                    break
                try:
                    ActionChains(self.driver).move_to_element(
                        current_del_btns[0]
                    ).click().perform()
                    self.wait_for_Check_loaders()
                except StaleElementReferenceException:
                    continue

        data_rows = self.driver.find_elements(*self.EDITABLE_DATA_ROWS)
        if len(data_rows) == 0:
            self._click_add_row_plus_button(expected_data_rows=1)

    def _click_add_row_plus_button(self, expected_data_rows: int) -> None:
        """Clicks the '+' button next to 'Add Row' using pure Selenium ActionChains."""
        self.wait_for_Check_loaders()
        current_data_rows = len(self.driver.find_elements(*self.EDITABLE_DATA_ROWS))

        while current_data_rows < expected_data_rows:
            logger.info(
                "Clicking '+' (Add Row) button (current data rows: %d -> target: %d)...",
                current_data_rows,
                expected_data_rows,
            )
            plus_btn = self.wait.until(
                EC.element_to_be_clickable(self.ADD_ROW_PLUS_BUTTON)
            )
            try:
                ActionChains(self.driver).move_to_element(plus_btn).click().perform()
            except ElementClickInterceptedException:
                ActionChains(self.driver).move_to_element(plus_btn).click().perform()

            WebDriverWait(self.driver, 10).until(
                lambda d: (
                    len(d.find_elements(*self.EDITABLE_DATA_ROWS)) > current_data_rows
                )
            )
            self.wait_for_Check_loaders()
            current_data_rows = len(self.driver.find_elements(*self.EDITABLE_DATA_ROWS))

    def _populate_project_and_activity(
        self, row_num: int, used_pairs: Set[Tuple[str, str]]
    ) -> None:
        """Fills the Project autocomplete and selects an Activity using pure Selenium."""
        data_row_xpath = f"(//table[contains(@class, 'orangehrm-timesheet-table')]//tbody/tr[.//input[contains(@placeholder, 'Type for hints')]])[{row_num}]"
        proj_input_locator = (
            By.XPATH,
            f"{data_row_xpath}//input[contains(@placeholder, 'Type for hints')]",
        )
        act_dropdown_locator = (
            By.XPATH,
            f"{data_row_xpath}//div[contains(@class, 'oxd-select-text-input')]",
        )

        search_hints = ["a", "e", "o", "i", "u", "c"]

        for hint in search_hints:
            self._type_project_hint(proj_input_locator, hint)

            try:
                WebDriverWait(self.driver, 6).until(
                    EC.visibility_of_all_elements_located(
                        self.AUTOCOMPLETE_VALID_OPTIONS
                    )
                )
            except TimeoutException:
                continue

            total_projects = len(
                self.driver.find_elements(*self.AUTOCOMPLETE_VALID_OPTIONS)
            )

            for p_idx in range(total_projects):
                if p_idx > 0:
                    self._type_project_hint(proj_input_locator, hint)
                    try:
                        WebDriverWait(self.driver, 6).until(
                            EC.visibility_of_all_elements_located(
                                self.AUTOCOMPLETE_VALID_OPTIONS
                            )
                        )
                    except TimeoutException:
                        break

                proj_els = self.driver.find_elements(*self.AUTOCOMPLETE_VALID_OPTIONS)
                if p_idx >= len(proj_els):
                    break

                proj_el = proj_els[p_idx]
                proj_name = proj_el.text.strip()
                ActionChains(self.driver).move_to_element(proj_el).click().perform()

                self.wait_for_Check_loaders()
                self.click_element(act_dropdown_locator)
                try:
                    WebDriverWait(self.driver, 6).until(
                        EC.visibility_of_all_elements_located(
                            self.ACTIVITY_VALID_OPTIONS
                        )
                    )
                except TimeoutException:
                    continue

                act_els = self.driver.find_elements(*self.ACTIVITY_VALID_OPTIONS)
                for act_el in act_els:
                    act_name = act_el.text.strip()
                    if (proj_name, act_name) not in used_pairs:
                        ActionChains(self.driver).move_to_element(
                            act_el
                        ).click().perform()
                        used_pairs.add((proj_name, act_name))
                        self.wait_for_Check_loaders()
                        logger.info(
                            "Row %d -> Selected Project: '%s' | Activity: '%s'",
                            row_num,
                            proj_name,
                            act_name,
                        )
                        return

                self.click_element(act_dropdown_locator)

        raise TimesheetAutomationError(
            f"Exhausted project suggestions without finding a unique Project+Activity for Row {row_num}."
        )

    def _type_project_hint(self, locator: Tuple[str, str], hint: str) -> None:
        """Safely clears the project autocomplete input and types search hint using pure Selenium."""
        proj_input = self.find_visible(locator)
        ActionChains(self.driver).move_to_element(proj_input).perform()
        proj_input.click()
        proj_input.send_keys(Keys.CONTROL + "a")
        proj_input.send_keys(Keys.BACKSPACE)
        proj_input.send_keys(hint)

    def _input_hours_for_day(self, row_num: int, day_idx: int, hour_val: str) -> None:
        """Enters hours into the target day column using pure Selenium."""
        data_row_inputs_xpath = f"(//table[contains(@class, 'orangehrm-timesheet-table')]//tbody/tr[.//input[contains(@placeholder, 'Type for hints')]])[{row_num}]//input"
        all_inputs = self.find_all_visible((By.XPATH, data_row_inputs_xpath))
        if len(all_inputs) < 8:
            raise TimesheetAutomationError(
                f"Expected at least 8 inputs in Row {row_num}, found {len(all_inputs)}."
            )

        day_inputs = all_inputs[-7:]
        target_day_input = day_inputs[day_idx]

        ActionChains(self.driver).move_to_element(target_day_input).perform()
        target_day_input.click()
        target_day_input.send_keys(Keys.CONTROL + "a")
        target_day_input.send_keys(Keys.BACKSPACE)
        target_day_input.send_keys(hour_val)
        target_day_input.send_keys(Keys.TAB)

    def _save_and_confirm_redirect(self, row_num: int, day_name: str) -> None:
        """Clicks Save and confirms redirect using pure Selenium."""
        logger.info("Clicking 'Save' for Row %d (%s)...", row_num, day_name)
        save_btn = self.wait.until(
            EC.element_to_be_clickable(self.SAVE_TIMESHEET_BUTTON)
        )
        try:
            ActionChains(self.driver).move_to_element(save_btn).click().perform()
        except ElementClickInterceptedException:
            ActionChains(self.driver).move_to_element(save_btn).click().perform()

        error_span_xpath = "//span[contains(@class, 'oxd-input-field-error-message')]"
        try:
            WebDriverWait(self.driver, 20).until(
                EC.any_of(
                    EC.visibility_of_element_located(self.EDIT_BUTTON),
                    EC.visibility_of_element_located((By.XPATH, error_span_xpath)),
                )
            )
        except TimeoutException as exc:
            raise TimesheetAutomationError(
                f"Timed out waiting for page redirect after saving Row {row_num} ({day_name})."
            ) from exc

        inline_errors = self.driver.find_elements(By.XPATH, error_span_xpath)
        if inline_errors:
            err_texts = [e.text.strip() for e in inline_errors if e.text.strip()]
            if err_texts:
                raise TimesheetAutomationError(
                    f"OrangeHRM rejected Timesheet Save on Row {row_num} ({day_name}) with UI error: {err_texts}"
                )

        self.wait_for_Check_loaders()
        self.wait.until(EC.element_to_be_clickable(self.EDIT_BUTTON))
        logger.info("Validated Row %d (%s) saved successfully!", row_num, day_name)

    def scrape_saved_timesheet(self) -> List[Dict[str, Any]]:
        """Scrapes the final saved 7-row read-only timesheet table."""
        self.wait_for_Check_loaders()
        self.find_visible(self.EDIT_BUTTON)

        headers_els = self.find_all_visible(self.SAVED_TABLE_HEADERS)
        clean_headers = [
            " ".join(h.text.strip().split()) or f"Column_{i}"
            for i, h in enumerate(headers_els)
        ]

        rows_els = self.find_all_visible(self.SAVED_TABLE_ROWS)
        scraped_data: List[Dict[str, Any]] = []

        for row_idx, row in enumerate(rows_els, start=1):
            cells = row.find_elements(By.XPATH, ".//td")
            row_dict: Dict[str, Any] = {"Entry_No": row_idx}
            for col_idx, cell in enumerate(cells):
                header_name = (
                    clean_headers[col_idx]
                    if col_idx < len(clean_headers)
                    else f"Col_{col_idx}"
                )
                val = cell.text.strip()
                row_dict[header_name] = val if val else "00:00"
            scraped_data.append(row_dict)

        logger.info(
            "Scraped %d saved timesheet rows from /viewMyTimesheet for Excel export.",
            len(scraped_data),
        )
        return scraped_data
