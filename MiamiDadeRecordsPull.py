# This file was written by: Carick Brandt on 4/2023
# This file will pull records from the Miami-Dade County Clerks website and run them against the property appraiser's website

# Import the necessary libraries
import os
import re
import sys
import time
import datetime
import SetDates
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_recaptcha_solver import RecaptchaSolver, StandardDelayConfig
import undetected_chromedriver as uc

# List of Document Types to pull
DocTypes = {
    "PAD": "Probate & Administration (PAD)",
    "DCE": "Death Certificate (DCE)",
    "Lis": "Lis Pendens (Lis)"
}

def GetDates():
    StartDate, EndDate = SetDates.GetDates()
    return StartDate, EndDate

def NoDates():
    StartDate, EndDate = SetDates.NoDates()
    return StartDate, EndDate

def InitDriver():
    testUA = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
    options = uc.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f'user-agent={testUA}')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = uc.Chrome(options=options)
    return driver

def GetRecords(driver, DocType, StartDate: str = None, EndDate: str = None):
    # Open the Miami-Dade County Clerk's website and login
    driver.get("https://www2.miamidadeclerk.gov/PremierServices/login.aspx")
    time.sleep(5)
    UsernameField = driver.find_element(By.ID, "ctl00_cphPage_txtUserName")
    for char in "Cjbrandt10":
        UsernameField.send_keys(char)
        time.sleep(.15)
    PasswordField = driver.find_element(By.ID, "ctl00_cphPage_txtPassword")
    for char in "Livelife1!":
        PasswordField.send_keys(char)
        time.sleep(.15)
    PasswordField.send_keys(Keys.ENTER)
    time.sleep(5)


    driver.get("https://onlineservices.4-4miamidadeclerk.gov/officialrecords/StandardSearch.aspx")
    time.sleep(5)

    # if StartDate and EndDate are not None, then we need to enter them into the search
    if StartDate is None:
        StartDate, EndDate = NoDates()
    # Input the Start Date into the field with the ID of "prec_date_from"
    StartDateField = driver.find_element(By.ID, "prec_date_from")
    StartDateField.click()
    StartDateField.clear()
    for char in StartDate:
        StartDateField.send_keys(char)
        time.sleep(.15)

    # Input the End Date into the field with the ID of "prec_date_to"
    EndDateField = driver.find_element(By.ID, "prec_date_to")
    EndDateField.click()
    EndDateField.clear()
    for char in EndDate:
        EndDateField.send_keys(char)
        time.sleep(.15)

    # Click the Document Type dropdown with ID "pdoc_type"
    DocTypeDropdown = driver.find_element(By.ID, "pdoc_type")
    DocTypeDropdown.click()
    DocTypeDropdown.send_keys(DocType)
    time.sleep(2)

    # Click the Search button with ID "btnNameSearch"
    SearchButton = driver.find_element(By.ID, "btnNameSearch")
    SearchButton.click()
    time.sleep(500)


driver = InitDriver()
GetRecords(driver, DocTypes["PAD"], StartDate="04/13/2023", EndDate="04/14/2023")
