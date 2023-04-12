# This file was written by Carick Brandt on 4/2023
# This module will be used to scrape the https://officialrecords.broward.org/AcclaimWeb/search/SearchTypeDocType
# website for the relevant DocType and returns a list of FirstNames, and LastNames from the First Indirect Name column
# from the search results.

# Import the necessary modules
import os
import time
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

# dictionary of the DocTypes we want to search for
DocTypes = {
    "LP": "Lis Pendens (LP)",
    "DC": "Death Certificate (DC)",
    "PRO": "Probate (PRO)",
    "PALIE": "Property Tax Lien (PALIE)"
}

# This function will take inputs for the start date and end date and return both varibles
def GetDates():
    # Get the Start Date
    print("Enter the Start Date for the ")
    StartDate: str = input("Start Date needs to be in the format of MM/DD/YYYY: ")
    print("Enter the End Date for the ")
    EndDate: str = input("End Date needs to be in the format of MM/DD/YYYY: ")
    return StartDate, EndDate

# This Function will handle if there is no inputs for StartDate and EndDate and return the default values
def NoDates():
    # Set the StartDate to yesterday and the EndDate to today
    Yesterday = datetime.date.today() - datetime.timedelta(days=1)
    Today = datetime.date.today()

    # Convert the dates to strings
    StartDate = Yesterday.strftime("%m/%d/%Y")
    EndDate = Today.strftime("%m/%d/%Y")
    return StartDate, EndDate

# This function will Initialize the Chrome Driver and return it
def InitDriver():
    # Create an Undetectable Chrome Driver
    driver = uc.Chrome()
    driver.get("https://officialrecords.broward.org/AcclaimWeb/search/SearchTypeDocType")
    driver.find_element(By.ID, "btnButton").click()
    time.sleep(2)
    return driver


# This function will take a DocType, StartDate, and EndDate and return a list of FirstNames and LastNames from the website
# StartDate should be yesterday's date and EndDate should be today's date as defaults
def Search(DocType, StartDate=None, EndDate=None):
    # Initialize the Chrome Driver
    driver = InitDriver()

    # Select the DocType from the dropdown
    dropdown = driver.find_element(By.ID, "DocTypesDisplay-input")
    dropdown.send_keys(Keys.CONTROL + "a")
    dropdown.send_keys(Keys.DELETE)
    dropdown.send_keys(DocType)
    time.sleep(2)

    # If there is no StartDate or EndDate, use the default values
    if StartDate is None or EndDate is None:
        StartDate, EndDate = NoDates()

    # Select the EndDateField
    EndDateField = driver.find_element(By.ID, "RecordDateTo")
    EndDateField.click()
    EndDateField.send_keys(Keys.CONTROL + "a")
    EndDateField.send_keys(Keys.DELETE)
    EndDateField.send_keys(EndDate)
    time.sleep(2)

    # Select the StartDateField
    StartDateField = driver.find_element(By.ID, "RecordDateFrom")
    StartDateField.click()
    StartDateField.send_keys(Keys.CONTROL + "a")
    StartDateField.send_keys(Keys.DELETE)
    StartDateField.send_keys(StartDate)
    StartDateField.send_keys(Keys.ENTER)
    time.sleep(5)

    # Traverse the table and get the First Inderect Name column
    table = driver.find_element(By.ID, "SearchGridContainer")
    rows = table.find_elements(By.TAG_NAME, "tr")
    FirstIndirectName = []
    for row in rows:
        row.click()
        time.sleep(100)

    return 0


Search(DocTypes["LP"])
