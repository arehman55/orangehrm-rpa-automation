*** Settings ***
Documentation       Enterprise RPA & Web Scraping Suite for OrangeHRM Demo Portal.
...                 Automates Phase 1 (Authentication), Phase 2 (Time Module 7-Day Timesheet),
...                 and Phase 3 (My Info 10 Sections + Attachments) using strict Explicit Waits.
Library             src.keywords.orangehrm_keywords.OrangeHRMKeywords
Suite Teardown      Close Browser Safely


*** Variables ***
${HEADLESS_MODE}    ${False}


*** Tasks ***
Run OrangeHRM Enterprise Automation
    [Documentation]    Executes the complete 3-phase automation and multi-workbook Excel export pipeline.
    Initialize Browser Session    headless=${HEADLESS_MODE}

    Log To Console    \n[Phase 1] Authenticating with OrangeHRM Portal...
    Execute Phase 1 Authentication

    Log To Console    [Phase 2] Automating and Scraping 'Time -> My Timesheets' (7 Separate Daily Entries)...
    Execute Phase 2 Time Module Automation And Scraping

    Log To Console    [Phase 3] Automating and Scraping all 10 'My Info' Sections & Attachments...
    Execute Phase 3 My Info Automation And Scraping

    Log To Console    \n[Success] All Excel artifacts generated in 'output/' folder!