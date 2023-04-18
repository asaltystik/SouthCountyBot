# This file was written by: Carick Brandt on 4/2023
# This file will pull records from the Miami-Dade County Clerks website and run them against the property appraiser's website
import math
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

# Asks the user what dates they want to search
def GetDates():
    StartDate, EndDate = SetDates.GetDates()
    return StartDate, EndDate

# Handles if the user doesn't input any dates
def NoDates():
    StartDate, EndDate = SetDates.NoDates()
    return StartDate, EndDate

# Inits Driver and passes options into it
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


# This Function will split the Parties from "First Party (Code)  Second Party (Code)"
def SplitParties(df):
    # Loop through the Dataframe and look at the "First Party (Code)  Second Party (Code)" column
    for index, row in df.iterrows():
        # Split the First Half of the String by the ")  " delimiter
        Party = row["First Party (Code)  Second Party (Code)"].split(")  ")[0]

        # if Misc Ref is "WILL" then we skip the row
        if row["Misc Ref"] == "WILL":
            df.at[index, "First Party (Code)  Second Party (Code)"] = np.nan
            continue

        # Split the string by the " (" delimiter
        Party = Party.split(" (")[0]
        # print("Party:", Party)

        # Count the number of spaces in the string
        Spaces = Party.count(" ")
        # print("Spaces:", Spaces)
        # print("is Spaces <=2:", int(Spaces) <= 2)
        # if there are at most 3 spaces before the first " (" then we only keep that part of the string
        if int(Spaces) <= 2:
            # print("First Party:", Party)
            # replace what's in "First Party (Code) Second Party (Code)" with the new Party
            df.at[index, "First Party (Code)  Second Party (Code)"] = Party
        else:
            df.at[index, "First Party (Code)  Second Party (Code)"] = np.nan

    # Drop the rows with NaN values
    df.dropna(subset=["First Party (Code)  Second Party (Code)"], inplace=True)
    # Rename the Column to Party
    df.rename(columns={"First Party (Code)  Second Party (Code)": "Party"}, inplace=True)
    # Drop any rows that have "INC", "BANK", "Trust", "LLC"
    df = df[~df["Party"].str.contains("INC", na=False)]
    df = df[~df["Party"].str.contains("BANK", na=False)]
    df = df[~df["Party"].str.contains("TRUST", na=False)]
    df = df[~df["Party"].str.contains("LLC", na=False)]
    # Drop and Duplicate Clerk's Numbers
    df.drop_duplicates(subset=["Clerk's File No"], inplace=True)
    # Reset the Index
    df.reset_index(drop=True, inplace=True)
    return df


# This Function will grab a dataframe from the tables on the Miami-Dade County Clerk's website
def GetTable(driver):
    # Get the text of the element with ID="lblResults"
    Results = driver.find_element(By.ID, "lblResults").text
    # print("Total Records for Search: " + Results)

    # Divide the total Results by 50 to get the number of pages. Round up to the nearest 50
    Pages: int = math.ceil(int(Results) / 50)
    # print("Number of Pages: " + str(Pages))

    # After the search is complete, we need to send the page_source to pandas
    df = pd.DataFrame(pd.read_html(driver.page_source)[0])
    # print("First Page")
    # print(df)
    time.sleep(3)
    dfList = [df]
    # If there are multiple pages we need to loop through them and add them to the dataframe
    if Pages > 1:
        for i in range(1, Pages):
            # print("Going to Next Page: " + str(i+1))
            # Scroll to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            # Loop through the links starting at index 1
            driver.find_element(By.LINK_TEXT, str(i+1)).click()
            time.sleep(10)
            # Send the page_source to pandas to parse the data
            tDf = pd.DataFrame(pd.read_html(driver.page_source)[0])
            dfList.append(tDf)
            # print(str(i) + " Page")
            # print(tDf)

    # print("Number of Lists: " + str(len(dfList)))
    Complete = pd.concat(dfList, ignore_index=True)
    return Complete


# This function will Login to the Clerks site
def Login(driver):
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

    driver.get("https://onlineservices.miamidadeclerk.gov/officialrecords/StandardSearch.aspx")
    time.sleep(5)
    return 0


# This Function will Search the Clerks Site using the given Dates
def Search(driver, DocType, StartDate: str, EndDate: str):
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
    time.sleep(5)
    return 0


# Grabs the Records from the Clerk Site
def GetRecords(driver, DocType, StartDate: str = None, EndDate: str = None):
    # Login to the Clerks Site
    Login(driver)

    # if StartDate and EndDate are not None, then we need to enter them into the search
    if StartDate is None:
        StartDate, EndDate = NoDates()

    # Search the Clerks Site using the Given info
    Search(driver, DocType, StartDate, EndDate)

    # Get the Table using the GetTable function
    df = GetTable(driver)

    # Drop Rec Book/Page, Plat Book/Page, Blk, Legal
    df.drop(columns=["Rec Book/Page", "Plat Book/Page", "Blk", "Legal", "Doc Type"], inplace=True)

    # Split the Parties from "First Party (Code)  Second Party (Code)" and Rename
    df = SplitParties(df)
    df.drop(columns="Misc Ref", inplace=True)

    # Rename Clerk's File No to "Case #"
    df.rename(columns={"Clerk's File No": "Case #"}, inplace=True)

    # Reorder the columns as "Doc Type", "Rec Date", "Case #", "Party"
    df = df[["Rec Date", "Case #", "Party"]]

    # Print and Save
    print(df)
    SaveTo = os.getcwd() + "\\MiamiDadeRecordsTest-" + DocType + ".csv"
    df.to_csv(SaveTo, index=False)
    driver.quit()

    return 0


driver = InitDriver()
GetRecords(driver, DocTypes["PAD"])
driver = InitDriver()
GetRecords(driver, DocTypes["DCE"])
driver = InitDriver()
GetRecords(driver, DocTypes["Lis"])
