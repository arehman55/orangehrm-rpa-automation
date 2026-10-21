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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("CentralizedRunner")


def run_robot_suite() -> int:
    """Initiates the complete automation suite via Robot Framework orchestrator."""
    project_root = Path(__file__).resolve().parent.parent
    tasks_file = project_root / "tasks.robot"
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Initiating Full RPA Suite via Robot Framework (%s)...", tasks_file.name)
    return_code = robot_run(
        str(tasks_file),
        outputdir=str(output_dir),
        pythonpath=[str(project_root), str(project_root / "src")],
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