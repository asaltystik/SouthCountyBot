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
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import threading

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
def Search(driver, StartDate, EndDate):
    # list of violations to search for
    Violations = ["Unsafe Structures", "All Other Code Violations"]
    dfList = []

    # loop through the violations and add them both to a final dataframe
    for Violation in Violations:
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
        WriteSlowly(driver, "txtCaseType", str(Violation))

        # Click the Radio Button for id="radios-1"
        CaseTypeRadio = driver.find_element(By.ID, "radios-1")
        CaseTypeRadio.click()

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

        #Click the End Date input with the id="endDate"
        EndDateInput = driver.find_element(By.ID, "endDate")
        EndDateInput.click()
        time.sleep(.4)
        EndDateInput.send_keys(Keys.CONTROL + "a")
        EndDateInput.send_keys(Keys.BACKSPACE)
        EndDateInput.send_keys(EndDate.split("/")[2])
        time.sleep(.4)
        EndDateInput.send_keys(Keys.TAB)
        EndDateInput.send_keys(EndDate.split("/")[0])
        time.sleep(.4)
        EndDateInput.send_keys(EndDate.split("/")[1])


        # Click the Submit Button with class="btn btn-primary"
        SubmitButton = driver.find_element(By.CLASS_NAME, "btn.btn-primary")
        SubmitButton.click()
        # Wait for the page to load
        time.sleep(5)

        # Read the table into a pandas data frame
        tempdf = pd.read_html(driver.page_source)[0]
        # Drop the rows that have a blank folio number
        tempdf = tempdf[tempdf["FOLIO NUMBER"] != "---"]
        # Drop the Rows that have "EXEMPT FROM PUBLIC RECORDS, Florida Statues 119.071" in the folio number
        tempdf = tempdf[tempdf["FOLIO NUMBER"] != "EXEMPT FROM PUBLIC RECORDS, Florida Statues 119.071"]

        # add temp df to list
        dfList.append(tempdf)

    # add all the dataframes together
    df = pd.concat(dfList, ignore_index=True)

    # Every Date Opened needs to be within 2 years prior to the start date
    # Convert the Date Opened column to a datetime object
    df["DATE OPENED"] = pd.to_datetime(df["DATE OPENED"])
    # Filter out the dates that are not within 2 years of the start date
    df = df[df["DATE OPENED"] >= pd.to_datetime(StartDate) - pd.DateOffset(years=2)]

    df = df.drop(columns=["COUNT", "LAST INSPECTION ACTIVITY", "ACTIVITY DATE",
                                      "DISTRICT NUMBER", "INSPECTOR", "OWNER NAME and ADDRESS",
                                      "VIOLATION", "PERMIT NUMBER"])

    # Reset the index
    df.reset_index(drop=True, inplace=True)
    print(df)

    # Close the driver and return the dataframe
    driver.close()
    return df


# This Function will take in the driver, and dataframe.
# It will navigate to the website: https://www.miamidade.gov/Apps/PA/propertysearch/#/ Where using the folio number it
# will pull the property information and return a dataframe with the new information
def GetPropertyInfo(driver, df: pd.DataFrame):
    # Add a Property Address, Property City, Property Zip, Mailing Address, Mailing City, Mailing Zip, Zoning, Land Use, Beds, Bath, SqFt
    df["Name"] = ""
    df["Property Address"] = ""
    df["Property City"] = ""
    df["Property State"] = "FL"
    df["Property Zip"] = ""
    df["Mailing Address"] = ""
    df["Mailing City"] = ""
    df["Mailing State"] = ""
    df["Mailing Zip"] = ""
    df["Zoning"] = ""
    df["Land Use"] = ""
    df["Beds"] = ""
    df["Bath"] = ""
    df["SqFt"] = ""
    df["Year Built"] = ""

    # Loop through the dataframe
    for index, row in df.iterrows():
        # Completely clear the console
        print("\033")
        # Print the row number and folio number
        print("Row: " + str(index) + " of " + str(len(df.index)) + " Folio: " + row["FOLIO NUMBER"])
        # go to the website
        driver.get("https://www.miamidade.gov/Apps/PA/propertysearch/#/")
        # if the driver is not maximized, maximize it
        if driver.get_window_size()["width"] != 1920:
            # Set window size to 1920X1080
            driver.set_window_size(1920, 1080)

        # Wait for the page to load
        time.sleep(3)

        # Check if the page loaded Correctly, if it did not then leave the function
        if CheckElement(driver, "t-folio") is False:
            return False

        # Click the folio button
        FolioButton = driver.find_element(By.ID, "t-folio")
        FolioButton.click()
        time.sleep(1)

        # click the search box
        SearchBox = driver.find_element(By.CSS_SELECTOR, "#folio #search_box")
        SearchBox.click()
        SearchBox.send_keys(Keys.CONTROL + "a")
        SearchBox.send_keys(Keys.BACKSPACE)
        SearchBox.send_keys(row["FOLIO NUMBER"])
        SearchBox.send_keys(Keys.ENTER)
        time.sleep(.5)

        # if the "close" button is present, click it. if not, gra
        try:
            driver.find_element(By.CLASS_NAME, "close").click()
            # Set the Property Address to "Not Found"
            df.at[index, "Property Address"] = "Not Found"
        except:
            # if class="property_info tabular_data" is present, grab the html source and send it to a pandas dataframe
            try:
                # if a link with text Comparable Sales is present
                if driver.find_element(By.LINK_TEXT, "Comparable Sales"):
                    driver.find_element(By.CLASS_NAME, "layers-list").click()
                    time.sleep(.25)
                    driver.find_element(By.CSS_SELECTOR, ".ng-scope:nth-child(4) > .ng-pristine").click()
                    time.sleep(.25)
                    driver.find_element(By.CSS_SELECTOR, ".ng-scope:nth-child(5) > .ng-pristine").click()
                    time.sleep(1.8)
                    # Split the Info String based on newlines
                    City = driver.find_element(By.ID, "layer-muni").text.split("MUNICIPALITY: ")[1]
                    Zip = driver.find_element(By.ID, "layer-zip").text.split("ZIP: ")[1]
                    # Get the table
                    df2 = pd.read_html(driver.page_source)[0]
                    # print(df2)

                    Name = df2.iloc[3, 1].split("Owner  ")[1]

                    # Split Property if it contains duplications
                    Property = df2.iloc[2, 1].split("Address  ")[1]  # row 2 is Property Address:
                    DupeTest = Property.split(" ")[0]
                    for substring in Property.split(" ")[1:]:
                        if substring == DupeTest:
                            Property = DupeTest + Property.split(substring)[1]
                            break

                    # Set List of Street Types
                    StreetTypes = ["ALY", "AVE", "BND", "BLVD", "CSWY", "CIR", "CT", "CV", "DRIVE", "EXT", "HWY",
                                   "HOLW", "ISLE", "LN",
                                   "LNDG", "MNR", "MILE", "PASS", "PATH", "PL", "PT", "ROAD", "ROW", "SQ", "ST", "TER",
                                   "TWP", "TRCE",
                                   "TRL", "VIEW", "WALK", "WAY", "RD", "PARK", "COURT", "DR"]

                    # Split the Mailing Address
                    MailingAddress = df2.iloc[4, 1].split("Address  ")[1]  # row 4 is the mailing address:
                    # print(MailingAddress)
                    # if the last part of the String is USA,

                    if MailingAddress.split("  ")[-1] == "USA":
                        MailingZip = MailingAddress.split("  ")[-2]
                        MailingState = MailingAddress.split("  ")[-3]
                        #  Find the First instance of a street type
                        for streetType in StreetTypes:
                            if streetType in MailingAddress:
                                # print("Street Type Found: " + streetType)
                                # if there is a number after the street type, add it the the street type with a space
                                if MailingAddress.split(streetType)[1].split(",")[0][1].isdigit():
                                    streetType = streetType + " " + MailingAddress.split(streetType)[1].split(" ")[1]
                                MailingCity = MailingAddress.split(streetType)[1].split(",")[0]
                                break
                            else:
                                # make mailing city the two words before the comma
                                MailingCity = MailingAddress.split(",")[0].split(" ")[-2]
                        MailingAddress = MailingAddress.split(MailingCity)[0]
                        # print("Mailing Address: " + MailingAddress)
                        # print("Mailing City: " + MailingCity)
                        # print("Mailing State: " + MailingState)
                        # print("Mailing Zip: " + MailingZip)
                    else:
                        MailingZip = MailingAddress.split("  ")[-1]
                        MailingState = MailingAddress.split("  ")[-2]
                        #  Find the First instance of a street type
                        for streetType in StreetTypes:
                            if streetType in MailingAddress:
                                # print("Street Type Found: " + streetType)
                                if MailingAddress.split(streetType)[1].split(",")[0][1].isdigit():
                                    streetType = streetType + " " + MailingAddress.split(streetType)[1].split(" ")[1]
                                MailingCity = MailingAddress.split(streetType)[1].split(",")[0]
                                break
                            else:
                                MailingCity = MailingAddress.split(",")[0].split(" ")[-2]
                        MailingAddress = MailingAddress.split(MailingCity)[0]
                        # print("Mailing Address: " + MailingAddress)
                        # print("Mailing City: " + MailingCity)
                        # print("Mailing State: " + MailingState)
                        # print("Mailing Zip: " + MailingZip)

                    # Set the info in the dataframe
                    df.loc[index, "Name"] = Name
                    df.loc[index, "Property Address"] = Property
                    df.loc[index, "Property City"] = City
                    df.loc[index, "Property Zip"] = Zip
                    df.loc[index, "Mailing Address"] = MailingAddress
                    df.loc[index, "Mailing City"] = MailingCity
                    df.loc[index, "Mailing State"] = MailingState
                    df.loc[index, "Mailing Zip"] = MailingZip
                    df.loc[index, "Zoning"] = df2.iloc[5, 1].split("Zone")[1]  # row 5 is the Zoning
                    df.loc[index, "Land Use"] = df2.iloc[6, 1].split("Use")[1]  # row 6 is the Land Use
                    df.loc[index, "Beds"] = df2.iloc[7, 1].split("/")[0]  # row 7 is the beds / baths.
                    df.loc[index, "Bath"] = df2.iloc[7, 1].split("/")[1].split("/")[
                        0]  # Take the First Number and the Number after the first "/". Nothing else
                    df.loc[index, "SqFt"] = df2.iloc[11, 1].split("Sq.Ft")[0]  # row 11 is the Sqft
                    df.loc[index, "Year Built"] = df2.iloc[14, 1]  # row 14 is the Year Built
                    # Print the row
                    print(df.loc[index])
            except:
                print("Multiple Results for Search")
                df.loc[index, "Name"] = np.nan
                df.loc[index, "Property Address"] = "Not Found"
                df.loc[index, "Property City"] = np.nan
                df.loc[index, "Property Zip"] = np.nan
                df.loc[index, "Mailing Address"] = np.nan
                df.loc[index, "Mailing City"] = np.nan
                df.loc[index, "Mailing State"] = np.nan
                df.loc[index, "Mailing Zip"] = np.nan
                df.loc[index, "Zoning"] = np.nan
                df.loc[index, "Land Use"] = np.nan
                df.loc[index, "Beds"] = np.nan
                df.loc[index, "Bath"] = np.nan
                df.loc[index, "SqFt"] = np.nan
                df.loc[index, "Year Built"] = np.nan
    # Drop any rows that have Property Address = Not Found
    df = df[df["Property Address"] != "Not Found"]
    return df

# This is the testing function
def Test():
    df = Search(InitDriver(), "01/01/2023", "05/03/2023")
    df = GetPropertyInfo(InitDriver(), df)
    df.to_csv("Test.csv", index=False)
    return print("Test Successful!")


Test()
