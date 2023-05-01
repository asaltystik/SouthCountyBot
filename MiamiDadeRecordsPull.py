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
import undetected_chromedriver as uc

# List of Document Types to pull
DocTypes = {
    "PAD": "Probate & Administration (PAD)",
    "DCE": "Death Certificate (DCE)",
    "LIS": "Lis Pendens (Lis)"
}


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
    df["First Name"] = ''
    df["Middle Name"] = ''
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
            if int(Spaces) == 2:
                # Split the string by the " " delimiter
                Party = Party.split(" ")
                df.at[index, "First Name"] = Party[1]
                df.at[index, "Middle Name"] = Party[2]
                df.at[index, "First Party (Code)  Second Party (Code)"] = Party[0]
            if int(Spaces) == 1:
                # Split the string by the " " delimiter
                Party = Party.split(" ")
                df.at[index, "First Name"] = Party[1]
                df.at[index, "First Party (Code)  Second Party (Code)"] = Party[0]
            if int(Spaces) == 0:
                df.at[index, "First Party (Code)  Second Party (Code)"] = np.nan
        else:
            df.at[index, "First Party (Code)  Second Party (Code)"] = np.nan

    # Drop the rows with NaN values
    df.dropna(subset=["First Party (Code)  Second Party (Code)"], inplace=True)
    # Rename the Column to Party
    df.rename(columns={"First Party (Code)  Second Party (Code)": "Last Name"}, inplace=True)
    # Drop any rows that have "INC", "BANK", "Trust", "LLC"
    df = df[~df["Last Name"].str.contains("INC", na=False)]
    df = df[~df["Last Name"].str.contains("BANK", na=False)]
    df = df[~df["Last Name"].str.contains("TRUST", na=False)]
    df = df[~df["Last Name"].str.contains("LLC", na=False)]
    # Drop and Duplicate Clerk's Numbers
    df.drop_duplicates(subset=["Clerk's File No"], inplace=True)
    # Reset the Index
    df.reset_index(drop=True, inplace=True)
    return df


# This Function will grab a dataframe from the tables on the Miami-Dade County Clerk's website
def GetTable(driver):
    time.sleep(2)
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
        StartDate, EndDate = SetDates.NoDates()

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
    df = df[["Rec Date", "Case #", "First Name", "Middle Name", "Last Name"]]

    print(df)

    # Search the Property Appraiser's website for the Property Address
    df = GetPropertyAddress(driver, df)

    # Drop any rows that have a property address of "Not Found"
    df = df[df["Property Address"] != "Not Found"]

    # Print and Save
    print(df)
    Date1 = StartDate.replace("/", "-")
    Date2 = EndDate.replace("/", "-")
    SaveTo = os.getcwd() + "\\MiamiDadeRecordsTest-" + DocType + "-" + Date1 + "to" + Date2 + ".csv"
    df.to_csv(SaveTo, index=False)
    driver.quit()

    return 0

# This function will grab the Property Address from the miami-dade county property appraiser's website
def GetPropertyAddress(driver, df):
    # Add a Property Address, Property City, Property Zip, Mailing Address, Mailing City, Mailing Zip, Zoning, Land Use, Beds, Bath, SqFt
    df["Folio"] = ""
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

    # Loop through the rows in the dataframe
    for index, row in df.iterrows():
        # Open the Property Appraiser's website at https://www.miamidade.gov/Apps/PA/propertysearch/#/
        driver.get("https://www.miamidade.gov/Apps/PA/propertysearch/#/")
        time.sleep(5)

        # Click Owner Name button
        driver.find_element(By.ID, "t-owner").click()
        time.sleep(2)

        # Input the owner name into the field with class="form-control owner-box ng-pristine ng-valid"
        OwnerNameField = driver.find_element(By.NAME, "ownerName")
        OwnerNameField.click()
        OwnerNameField.clear()

        # Type name as humanly as possible
        # print("Searching Next Name")
        for char in row["First Name"]:
            OwnerNameField.send_keys(char)
            time.sleep(.15)
        OwnerNameField.send_keys(" ")
        if row["Middle Name"] != "":
            for char in row["Middle Name"]:
                OwnerNameField.send_keys(char)
                time.sleep(.15)
            OwnerNameField.send_keys(" ")
        for char in row["Last Name"]:
            OwnerNameField.send_keys(char)
            time.sleep(.15)
        OwnerNameField.send_keys(Keys.ENTER)
        time.sleep(10)

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
                    time.sleep(1)
                    driver.find_element(By.CSS_SELECTOR, ".ng-scope:nth-child(4) > .ng-pristine").click()
                    time.sleep(1)
                    driver.find_element(By.CSS_SELECTOR, ".ng-scope:nth-child(5) > .ng-pristine").click()
                    time.sleep(2.5)
                    # Info is City, and Zip
                    Info = driver.find_element(By.CSS_SELECTOR, ".active-layers").text
                    # Split the Info String based on newlines
                    City = Info.split("MUNICIPALITY: ")[1].split("ZIP: ")[0]
                    Zip = Info.split("MUNICIPALITY: ")[1].split("ZIP: ")[1]

                    # Get the table
                    df2 = pd.read_html(driver.page_source)[0]
                    # print(df2)

                    Folio = df2.iloc[0, 1].split("Folio:  ")[1]
                    # print(Folio)

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
                                break
                            else:
                                MailingCity = MailingAddress.split(",")[0].split(" ")[-2]
                        MailingAddress = MailingAddress.split(MailingCity)[0]
                        # print("Mailing Address: " + MailingAddress)
                        # print("Mailing City: " + MailingCity)
                        # print("Mailing State: " + MailingState)
                        # print("Mailing Zip: " + MailingZip)

                    # Set the info in the dataframe
                    df.loc[index, "Folio"] = Folio
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
                    df.loc[index, "Bath"] = df2.iloc[7, 1].split("/")[1].split("/")[0]  # Take the First Number and the Number after the first "/". Nothing else
                    df.loc[index, "SqFt"] = df2.iloc[11, 1].split("Sq.Ft")[0]  # row 11 is the Sqft
                    df.loc[index, "Year Built"] = df2.iloc[14, 1]  # row 14 is the Year Built
            except:
                print("Multiple Results for Search")
                df.loc[index, "Folio"] = np.nan
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
                time.sleep(1.5)
    return df


def Run(DocType, StartDate, EndDate):
    driver = InitDriver()
    df = GetRecords(driver, DocTypes[DocType], StartDate, EndDate)
    return 0

# driver = InitDriver()
# df = GetRecords(driver, DocTypes["LIS"], "03/01/2023", "04/01/2023")
# driver = InitDriver()
# df = GetRecords(driver, DocTypes["PAD"], "03/01/2023", "04/01/2023")
# driver = InitDriver()
# df = GetRecords(driver, DocTypes["DCE"], "03/01/2023", "04/01/2023")
# driver = InitDriver()
# df = GetRecords(driver, DocTypes["LIS"], "04/01/2023", "04/27/2023")
# driver = InitDriver()
# df = GetRecords(driver, DocTypes["PAD"], "04/01/2023", "04/27/2023")
# driver = InitDriver()
# df = GetRecords(driver, DocTypes["DCE"], "04/01/2023", "04/27/2023")
