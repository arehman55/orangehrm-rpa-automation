# Enterprise RPA Automation Suite: Execution Guide

This document provides the exact steps required to run the OrangeHRM and Mozilla Thunderbird Desktop Email Automation project.

## Prerequisites
Ensure the following are installed and configured on your system before running the bot:
1. **Python 3.9+**
2. **Mozilla Thunderbird** (Logged in with the sender's email account)
3. **Google Chrome** (For Selenium web automation)
4. The project dependencies must be installed in your virtual environment.

---

## How to Run the Project

Follow these steps to execute the complete end-to-end automation workflow:

### Step 1: Open the Project
Open your project folder (`orangehrm-rpa-automation`) in **Visual Studio Code (VS Code)** or your preferred terminal.

### Step 2: Activate the Virtual Environment
Activate the Conda virtual environment that contains all the required libraries (RPA Framework, Selenium, Pandas, etc.):
```powershell
conda activate orangehrm-env
```
*(If you are using a standard Python virtual environment, use `.\orangehrm-env\Scripts\activate` instead).*

### Step 3: Run the Automation Bot
Execute the Robot Framework orchestrator file (`tasks.robot`). This will sequentially run Phase 1 (Login), Phase 2 (Timesheet scraping), Phase 3 (My Info automation), and Phase 4 (Thunderbird Email dispatch).

Run the following command in your terminal:
```powershell
python -m robot --pythonpath .:src --outputdir output tasks.robot
```

### Step 4: Review the Output
Once the execution is successfully completed, you can check the results:
1. **Excel Reports:** Go to the `output/` folder in your project directory. You will find the strictly formatted `OrangeHRM_Data.xlsx` and `Details.xlsx` workbooks.
2. **Execution Logs:** In the same `output/` folder, open `log.html` or `report.html` in any web browser to view the detailed step-by-step execution logs, success status, and any diagnostic screenshots.
3. **Emails:** Check your Mozilla Thunderbird **Sent** folder to verify that Email 1 (Timesheet HTML) and Email 2 (Details.xlsx threaded reply) were dispatched successfully.