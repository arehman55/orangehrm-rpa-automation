"""Unit tests for Thunderbird desktop mail dispatch."""

import unittest
from unittest.mock import Mock, patch

from src.services.thunderbird_mailer import ThunderbirdMailer


class ThunderbirdMailerTests(unittest.TestCase):
    def test_build_timesheet_html_escapes_html(self) -> None:
        html_body = ThunderbirdMailer._build_timesheet_html(
            [{"Project": "<script>alert(1)</script>"}]
        )

        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_body)
        self.assertNotIn("<script>alert(1)</script>", html_body)

    def test_thunderbird_dispatches_via_locator(self) -> None:
        desktop = Mock()
        desktop.wait_for_element.return_value = Mock()

        with (
            patch("src.services.thunderbird_mailer.Desktop", return_value=desktop),
            patch("src.services.thunderbird_mailer.subprocess.Popen") as popen,
        ):
            mailer = ThunderbirdMailer()
            mailer._compose_and_dispatch("to='team@example.com'")

        popen.assert_called_once()
        desktop.wait_for_element.assert_called_once_with("title:Write:", timeout=20)
        desktop.click.assert_any_call("name:Send")
        desktop.press_keys.assert_not_called()


if __name__ == "__main__":
    unittest.main()
