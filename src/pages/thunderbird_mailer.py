"""
Phase 4: Mozilla Thunderbird Desktop Email Automation Page Object Model.
Uses Pure Python, cross-platform RPA.Desktop (keyboard shortcuts),
CLI compose commands, and OS detection for Windows & Ubuntu compatibility.
"""

import logging
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

import pandas as pd
from RPA.Desktop import Desktop

from src.config import EMAIL_1_SUBJECT, OUTPUT_DIR, TEAM_LEAD_EMAIL, THUNDERBIRD_PATHS
from src.exceptions import EmailAutomationError

logger = logging.getLogger(__name__)


class ThunderbirdMailer:
    """Page Object for automating Mozilla Thunderbird using cross-platform CLI and Keyboard shortcuts."""

    def __init__(self, timeout: int = 20) -> None:
        """Initialize the desktop adapter and Thunderbird executable.

        Args:
            timeout (int): Maximum compose-window startup wait in seconds.

        Returns:
            None.

        Example:
            mailer = ThunderbirdMailer(timeout=10)
        """
        self.desktop = Desktop()
        self.timeout = timeout
        self.tb_exe = self._resolve_thunderbird_executable()

    def _resolve_thunderbird_executable(self) -> str:
        """Resolve the Thunderbird executable for the current operating system.

        Args:
            None.

        Returns:
            str: Executable command or path.

        Example:
            executable = mailer._resolve_thunderbird_executable()
        """
        current_os = platform.system()

        if current_os == "Linux":
            # On Ubuntu/Linux, Thunderbird is universally accessible via terminal command
            return "thunderbird"

        elif current_os == "Windows":
            for path in THUNDERBIRD_PATHS:
                if path.exists():
                    return str(path)

        raise EmailAutomationError(
            f"Mozilla Thunderbird executable not found for OS: {current_os}"
        )

    def send_timesheet_html_email(self, timesheet_excel_path: Path) -> None:
        """
        Send the timesheet workbook as an HTML email through Thunderbird.

        Args:
            timesheet_excel_path (Path): Timesheet workbook to attach.

        Returns:
            None.

        Example:
            mailer.send_timesheet_html_email(Path("output/OrangeHRM_Data.xlsx"))
        """
        if not timesheet_excel_path.exists():
            raise EmailAutomationError(
                f"Timesheet Excel file not found at: {timesheet_excel_path}"
            )

        logger.info(
            "Building HTML tabular body from '%s'...", timesheet_excel_path.name
        )
        df = pd.read_excel(timesheet_excel_path)
        records = df.to_dict(orient="records")

        html_body = self._build_timesheet_html(records)

        # FIX: Using OUTPUT_DIR instead of tempfile
        temp_html = OUTPUT_DIR / "orangehrm_email1_body.html"
        temp_html.write_text(html_body, encoding="utf-8")

        attachment_path = os.path.abspath(timesheet_excel_path)
        compose_arg = (
            f"to='{TEAM_LEAD_EMAIL}',"
            f"subject='{EMAIL_1_SUBJECT}',"
            f"format='html',"
            f"message='{temp_html.resolve()}',"
            f"attachment='{attachment_path}'"
        )

        logger.info("Launching Thunderbird Compose window for Email 1 (Timesheet)...")
        self._compose_and_dispatch(compose_arg)
        logger.info("Email 1 (Timesheet HTML Report) sent successfully!")

    def send_reply_with_details_excel(self, details_excel_path: Path) -> None:
        """
        Send the details workbook as a threaded Thunderbird reply.

        Args:
            details_excel_path (Path): Details workbook to attach.

        Returns:
            None.

        Example:
            mailer.send_reply_with_details_excel(Path("output/Details.xlsx"))
        """
        if not details_excel_path.exists():
            raise EmailAutomationError(
                f"Details Excel file not found at: {details_excel_path}"
            )

        logger.info("Preparing Email 2 (Reply with Details.xlsx attached)...")
        reply_html = self._build_details_reply_html()

        # FIX: Using OUTPUT_DIR instead of tempfile
        temp_reply_html = OUTPUT_DIR / "orangehrm_email2_reply.html"
        temp_reply_html.write_text(reply_html, encoding="utf-8")

        # Prepends 'Re:' to thread it visually in the recipient's inbox
        reply_subject = f"Re: {EMAIL_1_SUBJECT}"
        attachment_path = os.path.abspath(details_excel_path)

        compose_arg = (
            f"to='{TEAM_LEAD_EMAIL}',"
            f"subject='{reply_subject}',"
            f"format='html',"
            f"message='{temp_reply_html.resolve()}',"
            f"attachment='{attachment_path}'"
        )

        logger.info("Launching Thunderbird Compose window for Email 2 (Reply)...")
        self._compose_and_dispatch(compose_arg)
        logger.info("Email 2 (Reply with Details.xlsx) sent successfully!")

    def _compose_and_dispatch(self, compose_arg: str) -> None:
        """
        Open a Thunderbird compose window and dispatch the message.

        Args:
            compose_arg (str): Thunderbird compose argument string.

        Returns:
            None.

        Example:
            mailer._compose_and_dispatch("to='team@example.com'")
        """
        try:
            # Remove Conda and Snap-injected library/module paths before launch.
            clean_env = os.environ.copy()
            for key in [
                "LD_LIBRARY_PATH",
                "LD_PRELOAD",
                "PYTHONPATH",
                "PYTHONHOME",
                "GIO_MODULE_DIR",
                "GIO_LAUNCHED_DESKTOP_FILE",
                "GIO_LAUNCHED_DESKTOP_FILE_PID",
                "GTK_PATH",
                "GTK_EXE_PREFIX",
                "GTK_IM_MODULE_FILE",
            ]:
                clean_env.pop(key, None)

            # 1. Trigger the Compose window via OS terminal with isolated env
            subprocess.Popen(
                [self.tb_exe, "-compose", compose_arg],
                env=clean_env,
            )

            # 2. Allow Thunderbird time to render and focus the compose window.
            time.sleep(5)

            # 3. Dispatch using Universal Keyboard Shortcut (Ctrl + Enter)
            logger.info("Dispatching email via Ctrl+Enter shortcut...")
            self.desktop.press_keys("ctrl", "enter")

        except (OSError, RuntimeError, ValueError) as exc:
            raise EmailAutomationError(
                f"Failed during Thunderbird email dispatch: {exc}"
            ) from exc

    @staticmethod
    def _build_timesheet_html(records: list[dict[str, Any]]) -> str:
        """Build an HTML table for timesheet records.

        Args:
            records (list[dict[str, Any]]): Timesheet rows.

        Returns:
            str: Rendered HTML email body.

        Example:
            html = ThunderbirdMailer._build_timesheet_html(records)
        """
        if not records:
            return "<p>No timesheet records available.</p>"

        headers = list(records[0].keys())
        header_cells_html = "".join(
            f"<th style='background-color:#F2F2F2; color:#000000; padding:8px 10px; "
            f"border:1px solid #CCCCCC; text-align:center; font-family:Calibri,sans-serif; font-size:12px; font-weight:bold;'>{h}</th>"
            for h in headers
        )

        rows_html = ""
        for idx, row in enumerate(records):
            bg_color = "#F9F9F9" if idx % 2 == 1 else "#FFFFFF"
            row_cells = ""
            active_day_label = "N/A"

            for col_name in headers:
                val_str = str(row.get(col_name, "")).strip()
                if col_name not in (
                    "Entry_No",
                    "Project",
                    "Activity",
                    "Total",
                ) and val_str not in ("00:00", "0", "", "N/A"):
                    active_day_label = col_name

            for col_name in headers:
                val_str = str(row.get(col_name, "00:00")).strip()

                if col_name == "Project":
                    cell_style = f"background-color:{bg_color}; color:#000000; font-weight:bold; padding:8px 10px; border:1px solid #CCCCCC;"
                elif col_name == "Activity":
                    cell_style = f"background-color:{bg_color}; color:#333333; font-weight:normal; padding:8px 10px; border:1px solid #CCCCCC;"
                elif col_name == active_day_label:
                    cell_style = "background-color:#EAEAEA; color:#000000; font-weight:bold; text-align:center; padding:8px 10px; border:1.5px solid #000000;"
                    val_str = f"{val_str} *"
                else:
                    cell_style = f"background-color:{bg_color}; color:#555555; text-align:center; padding:8px 10px; border:1px solid #CCCCCC;"

                row_cells += f"<td style='{cell_style}'>{val_str}</td>"

            rows_html += f"<tr>{row_cells}</tr>"

        return f"""
        <html>
        <body style="font-family: Calibri, Arial, sans-serif; color: #111111; line-height: 1.5; font-size: 13px;">
            <p>Dear Team Lead,</p>
            <p>The automated RPA bot has successfully executed the 7-day timesheet entries on the OrangeHRM portal. Below is the tabular summary of the weekly activities:</p>
            
            <table style="border-collapse: collapse; width: 100%; margin-top: 15px; margin-bottom: 15px; font-size: 12px;">
                <thead>
                    <tr>{header_cells_html}</tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <p>The exported workbook <strong>OrangeHRM_Data.xlsx</strong> is attached to this email. A follow-up reply containing the complete 10-section My Info Details workbook will follow shortly.</p>
            <p style="margin-top: 20px;">Best regards,<br><strong>Abdul Rehman</strong><br><em>Enterprise RPA Automation Suite</em></p>
        </body>
        </html>
        """

    @staticmethod
    def _build_details_reply_html() -> str:
        """Build the HTML body for the details workbook reply.

        Args:
            None.

        Returns:
            str: Rendered HTML email body.

        Example:
            html = ThunderbirdMailer._build_details_reply_html()
        """
        sections = [
            ("1. Personal Details", "Completed + PDF Hyperlink"),
            ("2. Contact Details", "Completed + PDF Hyperlink"),
            ("3. Emergency Contacts", "Completed + PDF Hyperlink"),
            ("4. Dependents", "Completed + PDF Hyperlink"),
            ("5. Immigration", "Completed + PDF Hyperlink"),
            ("6. Job", "Completed + Attachments Block"),
            ("7. Salary", "Completed + Attachments Block"),
            ("8. Report-to", "Completed + Attachments Block"),
            ("9. Qualifications", "Completed + PDF Hyperlink"),
            ("10. Memberships", "Completed + PDF Hyperlink"),
        ]

        rows_html = "".join(
            f"<tr>"
            f"<td style='padding:7px 10px; border:1px solid #CCCCCC; font-weight:bold; color:#000000;'>{sec}</td>"
            f"<td style='padding:7px 10px; border:1px solid #CCCCCC; color:#333333; background-color:#FAFAFA;'>{status}</td>"
            f"</tr>"
            for sec, status in sections
        )

        return f"""
        <html>
        <body style="font-family: Calibri, Arial, sans-serif; color: #111111; line-height: 1.5; font-size: 13px;">
            <p>Dear Team Lead,</p>
            <p>In continuation of the previous report, please find attached the consolidated <strong>Details.xlsx</strong> workbook generated from Phase 3 (My Info Module).</p>
            <p>Each worksheet contains primary records followed by an ATTACHMENTS block with clickable local PDF hyperlinks:</p>

            <table style="border-collapse: collapse; width: 100%; margin: 15px 0; font-size: 12px;">
                <thead>
                    <tr>
                        <th style="background-color:#F2F2F2; color:#000000; padding:8px 10px; border:1px solid #CCCCCC; text-align:left;">Worksheet / Section</th>
                        <th style="background-color:#F2F2F2; color:#000000; padding:8px 10px; border:1px solid #CCCCCC; text-align:left;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <p>Best regards,<br><strong>Abdul Rehman</strong><br><em>Enterprise RPA Automation Suite</em></p>
        </body>
        </html>
        """
