# This File was written in 4/2023 By Carick Brandt

# Import the needed modules
import os
import re
import sys
import time
import datetime
import SetDates
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# Set the Download Directory to the current directory  + \Downloads
DownloadDirectory = os.getcwd() + "\\Downloads"

# Initialize the Chrome Driver
def InitDriver():
    # Create a Chrome Options object to set the download directory
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": DownloadDirectory,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    # Create a Chrome Driver object
    driver = uc.Chrome(options=chrome_options)
    return driver


# This function will handle checking if an element is present on the page, and if there is not then it will attempt to reload the page up to 3 times
def CheckElement(driver, ElementID):
    # Try to find the element with the given ID
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, ElementID)))
    # If the element is not found then reload the page and try again up to 3 times
    except:
        for i in range(3):
            driver.refresh()
            time.sleep(15)
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, ElementID)))
                break
            except:
                if i == 3:
                    print("Page did not load correctly")
                    return False
    return True


# This Function will write in whatever string a character at a time into a given input box
def WriteSlowly(driver, InputBoxID, InputString):
    # Find the input box
    InputBox = driver.find_element(By.ID, InputBoxID)
    # Clear the input box
    InputBox.send_keys(Keys.CONTROL + "a")
    InputBox.send_keys(Keys.BACKSPACE)
    # Make Sure it's at the beginning of the input box
    InputBox.send_keys(Keys.HOME)
    # Loop through the string and write it in one character at a time
    for i in range(len(InputString)):
        InputBox.send_keys(InputString[i])
        time.sleep(0.24)
    # Un-focus the input box
    InputBox.send_keys(Keys.TAB)
    return 0


# This Function wil go to the website https://www8.miamidade.gov/Apps/RER/RegulationSupportWebViewer/Home/Reports
# the case type is supposed to be set to "All Case Types" and we just need a start Date to complete a search
# Downloads the Excel file and returns the path to the file
def Search(driver, StartDate):
    # Go to the website
    driver.get("https://www8.miamidade.gov/Apps/RER/RegulationSupportWebViewer/Home/Reports")
    # Wait for the page to load, give it a couple of seconds to be safe
    time.sleep(5)

    # Check if the page loaded Correctly, if it did not then leave the function
    if CheckElement(driver, "txtCaseType") is False:
        return False

    # Click the Case Type dropdown
    CaseTypeDropDown = driver.find_element(By.ID, "txtCaseType")
    CaseTypeDropDown.click()
    # Wait for the dropdown to load
    time.sleep(.5)
    WriteSlowly(driver, "txtCaseType", "All Case Types")

    # Click the Start Date input with the id="startDate"
    StartDateInput = driver.find_element(By.ID, "startDate")
    StartDateInput.click()
    time.sleep(.4)
    StartDateInput.send_keys(Keys.CONTROL + "a")
    StartDateInput.send_keys(Keys.BACKSPACE)
    StartDateInput.send_keys(StartDate.split("/")[2])
    time.sleep(.4)
    StartDateInput.send_keys(Keys.TAB)
    StartDateInput.send_keys(StartDate.split("/")[0])
    time.sleep(.4)
    StartDateInput.send_keys(StartDate.split("/")[1])

    # Click the Submit Button with class="btn btn-primary"
    SubmitButton = driver.find_element(By.CLASS_NAME, "btn.btn-primary")
    SubmitButton.click()
    # Wait for the page to load
    time.sleep(5)

    # Read the table into a pandas data frame
    df = pd.read_html(driver.page_source)[0]
    # Drop the un-needed columns
    df = df.drop(columns=["COUNT", "LAST INSPECTION ACTIVITY", "ACTIVITY DATE",
                          "DISTRICT NUMBER", "INSPECTOR", "OWNER NAME and ADDRESS"])

    # Close the driver and return the dataframe
    driver.close()
    return df


# This is the testing function
def Test():
    df = Search(InitDriver(), "01/01/2023")
    df.to_csv("Test.csv", index=False)
    return print("Test Successful!")


Test()
