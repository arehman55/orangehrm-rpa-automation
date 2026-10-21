"""
Phase 4: Mozilla Thunderbird Desktop Email Automation Page Object Model.
Uses Pure Python, cross-platform RPA.Desktop (keyboard shortcuts), 
CLI compose commands, and OS detection for Windows & Ubuntu compatibility.
"""

import logging
import subprocess
import tempfile
import platform
from time import sleep
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from RPA.Desktop import Desktop
from src.config import TEAM_LEAD_EMAIL, EMAIL_1_SUBJECT, THUNDERBIRD_PATHS
from src.exceptions import EmailAutomationError

logger = logging.getLogger(__name__)


class ThunderbirdMailer:
    """Page Object for automating Mozilla Thunderbird using cross-platform CLI and Keyboard shortcuts."""

    def __init__(self, timeout: int = 20) -> None:
        self.desktop = Desktop()
        self.timeout = timeout
        self.tb_exe = self._resolve_thunderbird_executable()

    def _resolve_thunderbird_executable(self) -> str:
        """Locates Thunderbird executable based on the operating system (Windows/Linux)."""
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
        Email 1: Reads scraped timesheet Excel, builds HTML table,
        attaches OrangeHRM_Data.xlsx, and sends via Thunderbird.
        """
        if not timesheet_excel_path.exists():
            raise EmailAutomationError(
                f"Timesheet Excel file not found at: {timesheet_excel_path}"
            )

        logger.info("Building HTML tabular body from '%s'...", timesheet_excel_path.name)
        df = pd.read_excel(timesheet_excel_path)
        records = df.to_dict(orient="records")

        html_body = self._build_timesheet_html(records)
        temp_html = Path(tempfile.gettempdir()) / "orangehrm_email1_body.html"
        temp_html.write_text(html_body, encoding="utf-8")

        file_uri = timesheet_excel_path.resolve().as_uri()
        compose_arg = (
            f"to='{TEAM_LEAD_EMAIL}',"
            f"subject='{EMAIL_1_SUBJECT}',"
            f"format='html',"
            f"message='{temp_html.resolve()}',"
            f"attachment='{file_uri}'"
        )

        logger.info("Launching Thunderbird Compose window for Email 1 (Timesheet)...")
        self._compose_and_dispatch(compose_arg)
        logger.info("Email 1 (Timesheet HTML Report) sent successfully!")

    def send_reply_with_details_excel(self, details_excel_path: Path) -> None:
        """
        Email 2: Dispatches the Details.xlsx as a threaded reply using CLI compose 
        to ensure cross-platform stability on both Ubuntu and Windows.
        """
        if not details_excel_path.exists():
            raise EmailAutomationError(
                f"Details Excel file not found at: {details_excel_path}"
            )

        logger.info("Preparing Email 2 (Reply with Details.xlsx attached)...")
        reply_html = self._build_details_reply_html()

        temp_reply_html = Path(tempfile.gettempdir()) / "orangehrm_email2_reply.html"
        temp_reply_html.write_text(reply_html, encoding="utf-8")

        # Prepends 'Re:' to thread it visually in the recipient's inbox
        reply_subject = f"Re: {EMAIL_1_SUBJECT}"
        file_uri = details_excel_path.resolve().as_uri()

        compose_arg = (
            f"to='{TEAM_LEAD_EMAIL}',"
            f"subject='{reply_subject}',"
            f"format='html',"
            f"message='{temp_reply_html.resolve()}',"
            f"attachment='{file_uri}'"
        )
        
        logger.info("Launching Thunderbird Compose window for Email 2 (Reply)...")
        self._compose_and_dispatch(compose_arg)
        logger.info("Email 2 (Reply with Details.xlsx) sent successfully!")

    def _compose_and_dispatch(self, compose_arg: str) -> None:
        """
        Executes `thunderbird -compose` cross-platform, waits for UI to render, 
        and uses universal Ctrl+Enter shortcut to dispatch.
        """
        try:
            # 1. Trigger the Compose window via OS terminal
            subprocess.Popen([self.tb_exe, "-compose", compose_arg])

            # 2. Wait for the Compose UI to render (Cross-platform explicit wait)
            sleep(5)

            # 3. Dispatch using Universal Keyboard Shortcut (Ctrl + Enter)
            logger.info("Dispatching email via Ctrl+Enter shortcut...")
            self.desktop.press_keys("ctrl", "enter")
            
            # Brief pause to allow Thunderbird to process the send action
            sleep(2)

        except Exception as exc:
            raise EmailAutomationError(
                f"Failed during Thunderbird email dispatch: {exc}"
            ) from exc

    @staticmethod
    def _build_timesheet_html(records: List[Dict[str, Any]]) -> str:
        """Generates a clean, professional black-and-white HTML email body with an inline CSS table."""
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
                if col_name not in ("Entry_No", "Project", "Activity", "Total") and val_str not in ("00:00", "0", "", "N/A"):
                    active_day_label = col_name

            for col_name in headers:
                val_str = str(row.get(col_name, "00:00")).strip()

                if col_name == "Project":
                    cell_style = f"background-color:{bg_color}; color:#000000; font-weight:bold; padding:8px 10px; border:1px solid #CCCCCC;"
                elif col_name == "Activity":
                    cell_style = f"background-color:{bg_color}; color:#333333; font-weight:normal; padding:8px 10px; border:1px solid #CCCCCC;"
                elif col_name == active_day_label:
                    cell_style = f"background-color:#EAEAEA; color:#000000; font-weight:bold; text-align:center; padding:8px 10px; border:1.5px solid #000000;"
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
        """Generates a clean, professional black-and-white HTML body for Email 2 reply."""
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