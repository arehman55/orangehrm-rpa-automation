"""
Phase 1: Authentication Page Object Model.
Handles portal login and dashboard verification with custom exceptions.
"""

import logging
from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from src.base_page import BasePage
from src.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Page Object for OrangeHRM Login Module."""

    USERNAME_FIELD = (By.NAME, "username")
    PASSWORD_FIELD = (By.NAME, "password")
    LOGIN_BTN = (By.XPATH, "//button[@type='submit']")
    DASHBOARD_HEADER = (By.XPATH, "//h6[normalize-space()='Dashboard']")

    def login(self, base_url: str, username: str, password: str) -> None:
        """Navigates to URL, fills credentials, submits, and verifies dashboard."""
        logger.info("Navigating to login portal: %s", base_url)
        self.driver.get(base_url)
        self.wait_for_Check_loaders()

        try:
            logger.info("Entering credentials...")
            self.clear_and_type(self.USERNAME_FIELD, username)
            self.clear_and_type(self.PASSWORD_FIELD, password)
            self.click_element(self.LOGIN_BTN)

            logger.info("Verifying Dashboard arrival...")
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located(self.DASHBOARD_HEADER)
            )
            logger.info("Authentication successful and Dashboard loaded.")
        except Exception as exc:
            raise AuthenticationError(
                f"Failed to authenticate with OrangeHRM portal: {exc}"
            ) from exc
