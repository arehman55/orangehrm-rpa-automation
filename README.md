# Enterprise RPA Automation Suite: OrangeHRM & Thunderbird

This project is an end-to-end Enterprise Robotic Process Automation (RPA) suite built with Python, Robot Framework, Selenium, and RPA.Desktop. It seamlessly automates web scraping, dynamic Excel report generation, and cross-platform desktop email dispatch.

## Automation Workflow (The 4 Phases)
When initiated, the bot autonomously executes the following 4 phases:
1. **Phase 1: Secure Authentication:** Automates the login process into the OrangeHRM portal using Selenium.
2. **Phase 2: Timesheet Data Extraction:** Navigates to the Time module, scrapes employee timesheet records, and structures the data for reporting.
3. **Phase 3: Employee Data & Excel Generation:** Navigates to the My Info module, extracts data across 10 different sections, and dynamically generates highly formatted Excel workbooks (`OrangeHRM_Data.xlsx` and `Details.xlsx`).
4. **Phase 4: Desktop Email Automation:** Utilizes cross-platform UI locators (keyboard shortcuts & CLI) to take control of Mozilla Thunderbird. It dispatches the Timesheet data as an HTML table in the primary email and sends the `Details.xlsx` workbook as a threaded reply.

---

## Prerequisites
Ensure the following are installed and configured on your system before running the bot:
1. **Python 3.9+**
2. **Mozilla Thunderbird** (Logged in with the sender's email account)
3. **Google Chrome** (For Selenium web automation)
4. **Operating System:** Windows 10/11 or Linux

---

## Installation & Setup

This project is professionally packaged using the `pyproject.toml` (PEP 621) standard. It is designed to be fully portable and self-contained.

### Option A: Install from Source (Recommended for Development/Testing)
Navigate to the root directory of the project where `pyproject.toml` is located:

```bash
# 1. Create and activate a fresh virtual environment
python -m venv rpa-env
source rpa-env/bin/activate  # On Windows use: rpa-env\Scripts\activate

# 2. Install the package and its dependencies
pip install .
```

### Option B: Install via Wheel (.whl) Release
If you have been provided with the pre-compiled `.whl` distribution file:
```bash
pip install orangehrm_rpa_automation-1.0.0-py3-none-any.whl
```

---

## Execution (CLI Commands)

Once installed, the package registers a global command-line interface (CLI) command `run-rpa`. You can execute this command from **any directory**, and the bot will dynamically create an `output` folder in your current working directory.

**To run the complete 4-Phase Automation Suite via Pure Python:**
```bash
run-rpa --mode python
```

**To run the suite via Robot Framework (Default):**
```bash
run-rpa --mode robot
```

**To test specific components (e.g., Email Dispatch Only):**
```bash
run-rpa --mode email-only
```

---

## Development & Architecture

This project strictly adheres to Enterprise Software Architecture principles. 

* **Page Object Model (POM):** All Selenium locators (XPaths/CSS) are centralized in `src/pages/locators.py` to ensure maintainability.
* **Environment Isolation:** UI automation tools handle OS-level library conflicts natively (e.g., isolating Conda variables from Snap packages on Ubuntu).

### Running Unit Tests
To verify core logic, exception handling, and mock executions without launching a browser, run the built-in test suite:
```bash
python -m unittest discover -s tests
```

### Automated Build Pipeline
An automated build script is provided to cleanly generate the `.whl` package. It safely purges old `build/` and `dist/` artifacts before building a fresh release:
```bash
python build_script.py
```
*The newly generated `.whl` file will be located in the `dist/` directory.*

---

## Project Outputs
Upon successful execution, the bot generates a dynamic `output/` directory in the terminal's current path containing:
- `OrangeHRM_Data.xlsx` (Phase 2 Scraped Data)
- `Details.xlsx` (Phase 3 Comprehensive Employee Data with internal PDF hyperlinks)
- Temporary HTML bodies for Thunderbird dispatch.