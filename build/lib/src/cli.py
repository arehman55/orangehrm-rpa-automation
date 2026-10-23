"""
Centralized Entry Point for the OrangeHRM & Thunderbird RPA Automation Package.
Allows initiating the complete end-to-end Robot Framework suite, Pure Python workflow,
or isolated Phase 4 Email Automation directly from the command line.
"""

import argparse
import logging
import sys
from pathlib import Path
from robot import run as robot_run
from src.keywords.orangehrm_keywords import OrangeHRMKeywords

# Yahan humne config se dynamic paths import kar liye hain
from src.config import ROBOT_FILE, OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("CentralizedRunner")


def run_robot_suite() -> int:
    """Initiates the complete automation suite via Robot Framework orchestrator."""
    logger.info("Initiating Full RPA Suite via Robot Framework (%s)...", ROBOT_FILE.name)
    
    # FIX: Yahan direct ROBOT_FILE aur OUTPUT_DIR use kiya hai jo config.py se aayega
    return_code = robot_run(
        str(ROBOT_FILE),
        outputdir=str(OUTPUT_DIR),
        pythonpath=[str(ROBOT_FILE.parent)],
    )
    return int(return_code)


def run_pure_python_workflow(mode: str) -> None:
    """Initiates the automation phases directly via Pure Python Keyword class."""
    rpa = OrangeHRMKeywords()

    if mode == "email-only":
        logger.info("Initiating Phase 4: Thunderbird Email Automation Only...")
        rpa.execute_phase_4_email_reporting()
        logger.info("Phase 4 Email Automation completed successfully!")
        return

    logger.info("Initiating Complete 4-Phase Pure Python Execution...")
    try:
        rpa.initialize_automation_session()
        rpa.execute_phase_1_authentication()
        rpa.execute_phase_2_time_module_automation()
        rpa.execute_phase_3_my_info_module_automation()
        rpa.execute_phase_4_email_reporting()
        logger.info("All 4 Phases completed successfully!")
    finally:
        rpa.teardown_automation_session()


def main() -> None:
    """Main CLI handler parsed when running `run-rpa` or `python -m src.cli`."""
    parser = argparse.ArgumentParser(
        description="OrangeHRM Enterprise RPA Centralized Runner"
    )
    parser.add_argument(
        "--mode",
        choices=["robot", "python", "email-only"],
        default="robot",
        help=(
            "'robot': Run full suite via tasks.robot (default) | "
            "'python': Run all 4 phases directly via Python | "
            "'email-only': Run only Phase 4 Thunderbird email automation"
        ),
    )
    args = parser.parse_args()

    try:
        if args.mode == "robot":
            exit_code = run_robot_suite()
            sys.exit(exit_code)
        else:
            run_pure_python_workflow(args.mode)
    except Exception as exc:
        logger.error("Execution failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()