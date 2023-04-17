# This file was written by Carick Brandt on 4/2023
# This module will be used to scrape the https://officialrecords.broward.org/AcclaimWeb/search/SearchTypeDocType
# website for the relevant DocType and returns a list of FirstNames, and LastNames from the First Indirect Name column
# from the search results.

# Import the necessary modules
import os
import re
import sys
import time
import datetime
import numpy as np
import pandas as pd
import SetDates
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# dictionary of the DocTypes we want to search for
DocTypes = {
    "LP": "Lis Pendens (LP)",
    "DC": "Death Certificate (DC)",
    "PRO": "Probate (PRO)",
    "PALIE": "Property Tax Lien (PALIE)"
}

# This function will Initialize the Chrome Driver and return it
def InitDriver():
    # Create an Undetectable Chrome Driver
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
    driver = uc.Chrome(options=options)
    driver.get("https://google.com")
    time.sleep(2)
    driver.get("https://officialrecords.broward.org/AcclaimWeb/search/SearchTypeDocType")
    time.sleep(5)
    driver.find_element(By.ID, "btnButton").click()
    time.sleep(5)
    return driver


# This function will take a DocType, StartDate, and EndDate and Pull up Search Results for the DocType
def Search(driver, DocType, StartDate=None, EndDate=None):
    # Select the DocType from the dropdown
    dropdown = driver.find_element(By.ID, "DocTypesDisplay-input")
    time.sleep(2)
    dropdown.send_keys(Keys.CONTROL + "a")
    time.sleep(1)
    dropdown.send_keys(Keys.DELETE)
    time.sleep(1)
    # Enter the Doctype one character at a time
    for char in DocType:
        dropdown.send_keys(char)
        time.sleep(1)
    time.sleep(4)

    # If there is no StartDate or EndDate, use the default values
    if StartDate is None or EndDate is None:
        StartDate, EndDate = SetDates.NoDates()

    # Select the EndDateField
    EndDateField = driver.find_element(By.ID, "RecordDateTo")
    time.sleep(2)
    EndDateField.click()
    time.sleep(2)
    EndDateField.send_keys(Keys.CONTROL + "a")
    time.sleep(2)
    EndDateField.send_keys(Keys.DELETE)
    time.sleep(2)
    # Enter the EndDate one character at a time
    for char in EndDate:
        EndDateField.send_keys(char)
        time.sleep(1)
    time.sleep(4)

    # Select the StartDateField
    StartDateField = driver.find_element(By.ID, "RecordDateFrom")
    time.sleep(2)
    StartDateField.click()
    time.sleep(2)
    StartDateField.send_keys(Keys.CONTROL + "a")
    time.sleep(2)
    StartDateField.send_keys(Keys.DELETE)
    time.sleep(2)
    # Enter the StartDate one character at a time
    for char in StartDate:
        StartDateField.send_keys(char)
        time.sleep(1)
    time.sleep(2)
    StartDateField.send_keys(Keys.ENTER)
    time.sleep(2)

    return 0

# This Function will Scrape the Search Results and return a dataframe
def Scrape(driver, DocType):
    # Traverse the table and get the First Indirect Name column
    try:
        WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.ID, "SearchGridContainer")))
    except:
        print("No Results Found")
        return None
    time.sleep(2)
    # Grab the Number of rows from class "t-status-text"
    NumRows = driver.find_element(By.CLASS_NAME, "t-status-text").text.split(" ")[-1]
    print("Number of Rows: " + NumRows)

    # Divide the number of rows by 100 to get the number of pages. Then round up to the next hundred
    NumPages = int(np.ceil(int(NumRows) / 100))
    print("Number of Pages: " + str(NumPages))

    CaseNumber = []
    FirstIndirectName = []
    # for the number of pages loop through the pages
    for i in range(NumPages):
        time.sleep(2)
        print("Page: " + str(i+1))
        table = driver.find_element(By.ID, "SearchGridContainer")
        rows = table.find_elements(By.TAG_NAME, "tr")
        FirstIndirectNameIndex: int
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            # for the first row, we need to find the column index for the First Indirect Name column, count the number of newlines in the row till we get to the column with First Indirect Name
            if row.text.__contains__("Cart\nConsideration\nFirst Direct Name\nFirst Indirect Name"):
                # Find the Number of Newlines are before First Indirect Name
                FirstIndirectNameIndex = row.text.count("\n", 0, row.text.index("First Indirect Name"))
                # print("Found Indirect Name Index at pos: " + str(FirstIndirectNameIndex))
                continue
            else:
                FirstIndirectNameIndex = 3

            if DocType == DocTypes["LP"] or DocType == DocTypes["PALIE"]:
                # print the indirect name column and append it to the FirstIndirectName list
                print("IndirectName: " + columns[FirstIndirectNameIndex].text)
                FirstIndirectName.append(columns[FirstIndirectNameIndex].text)
            else:
                print("DirectName: " + columns[FirstIndirectNameIndex-1].text)
                FirstIndirectName.append(columns[FirstIndirectNameIndex-1].text)

            # If the DocType is not a Death Certificate or a Property Tax Lien, we need to get the Case Number
            if DocType is DocTypes["DC"] or DocType is DocTypes["PALIE"]:
                CaseNumber.append(np.nan)
            else:
                time.sleep(2)
                row.click()
                driver.switch_to.window(driver.window_handles[1])

                # Get the DocBlock from the classname "docBlock"
                NotLoaded = True
                attempts = 0
                while NotLoaded:
                    try:
                        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "docBlock")))
                        NotLoaded = False
                    except:
                        print("Page Did not load Cannot grab Case Number. Attempting to reopen page")
                        attempts += 1
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        row.click()
                        driver.switch_to.window(driver.window_handles[1])
                    if attempts > 5:
                        print("Page Did not load Cannot grab Case Number. Skipping")
                        CaseNumber.append(np.nan)
                        break
                time.sleep(2)

                DocBlock = driver.find_element(By.CLASS_NAME, "docBlock")
                Details = DocBlock.find_elements(By.CLASS_NAME, "detailLabel")
                ListDocDetails = DocBlock.find_elements(By.CLASS_NAME, "listDocDetails")

                # Find the Details that has the Text "Case Number:"
                for Detail in Details:
                    if Detail.text.__contains__("Case Number:"):
                        print("Case Number: " + ListDocDetails[Details.index(Detail)].text)
                        CaseNumber.append(ListDocDetails[Details.index(Detail)].text)
                # If a case number was not found, append a NaN
                if len(CaseNumber) < len(FirstIndirectName):
                    print("No Case Number Found")
                    CaseNumber.append(np.nan)

                # close the new window and switch back to the main window
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(6)
        # Click the t-icon t-arrow-next button
        if i < NumPages:
            print("Clicking Next Button")
            driver.find_element(By.CLASS_NAME, "t-icon.t-arrow-next").click()
            time.sleep(6)

    # print the list of case numbers
    print(CaseNumber)
    # Create a Dataframe from the FirstIndirectName and CaseNumber lists
    df = pd.DataFrame(list(zip(CaseNumber, FirstIndirectName)), columns=["CaseNumber", "FirstIndirectName"])

    # Add the DocType Column
    df["DocType"] = DocType

    # Reorder the Columns for DocType, CaseNumber, FirstIndirectName
    df = df[["DocType", "CaseNumber", "FirstIndirectName"]]
    return df


# This Function will take a dataframe and separate the First Indirect name column into First Name and Last Name columns
# and return the new dataframe
def SeparateNames(df):
    # Create new columns for First Name and Last Name
    FirstName = []
    LastName = []

    # if the FirstIndirectName column has a comma, then the First Name is the Word after the comma and before the space
    # and the Last Name is the word at the beginning of the string
    # loop through the dataframe and fill the First Name and Last Name columns
    for index, row in df.iterrows():
        if "," in row["FirstIndirectName"]:
            FirstName.append(row["FirstIndirectName"].split(",")[1].split(" ")[0])
            LastName.append(row["FirstIndirectName"].split(",")[0])
            df.at[index, "FirstIndirectName"] = np.nan
        else:
            FirstName.append(np.nan)
            LastName.append(np.nan)

    # Create new columns for First Name and Last Name and use the lists we created earlier
    df["FirstName"] = FirstName
    df["LastName"] = LastName
    # Rename FirstIndirectName to CompanyName
    df = df.rename(columns={"FirstIndirectName": "CompanyName"})
    return df

# Sets row to NAN if needed.
def SetNAN(index, df):
    df.at[index, "Address"] = np.nan
    df.at[index, "City"] = np.nan
    df.at[index, "State"] = np.nan
    df.at[index, "Zip"] = np.nan
    df.at[index, "MailingAddress"] = np.nan
    df.at[index, "MailingCity"] = np.nan
    df.at[index, "MailingState"] = np.nan
    df.at[index, "MailingZip"] = np.nan
    df.at[index, "JustMarketValue"] = np.nan
    df.at[index, "Taxes"] = np.nan
    df.at[index, "Bed"] = np.nan
    df.at[index, "Bath"] = np.nan
    df.at[index, "SqFt"] = np.nan
    return df


# This Function will Split a Mailing Address into house number, street direction, street name, street type, unit number (if applicable), City, State, Zip
def SplitMailingAddress(mailAddress):
    # Street Types
    StreetTypes = ["ALY", "AVE", "BND", "BLVD", "CSWY", "CIR", "CT", "CV", "DRIVE", "EXT", "HWY", "HOLW", "ISLE", "LN",
                   "LNDG", "MNR", "MILE", "PASS", "PATH", "PL", "PT", "ROAD", "ROW", "SQ", "ST", "TER", "TWP","TRCE",
                   "TRL", "VIEW", "WALK", "WAY", "RD", "PARK", "COURT", "DR"]

    # Create the Variables to hold the Mailing Address, City
    MailingAddr = ""
    Remaining = ""

    # Split the mailing address after an occurrence of StreetTypes
    for streetType in StreetTypes:
        if mailAddress.__contains__(streetType):
            # Need a Variable to hold the first part of the address which is just after the Street Type
            # and the second part of the address which is the rest of the address
            MailingAddr = mailAddress.split(streetType)[0] + streetType
            Remaining = mailAddress.split(streetType)[1]
            break

    # Use a regex to seperate a unit number from the Remaining. Unit numbers are in the format of #2. #210, #*/dA, UNIT #*/d.
    # Unit Numbers are optional but would be at the Beginning of the Remaining string
    # If there is a unit number, then the first part of the address is the unit number and the second part of the address is the rest of the address
    # If there is no unit number, then the first part of the address is the rest of the address and the second part of the address is empty
    if re.search(r"UNIT \d{1,4}", Remaining):
        UnitNumber = re.search(r"UNIT \d{1,4}", Remaining).group(0)
        MailingAddr = MailingAddr + " " + UnitNumber
        Remaining = Remaining.split(UnitNumber)[1]
    elif re.search(r"#\d{1,4}[A-Z]", Remaining):
        UnitNumber = re.search(r"#\d{1,4}[A-Z]", Remaining).group(0)
        MailingAddr = MailingAddr + " " + UnitNumber
        Remaining = Remaining.split(UnitNumber)[1]
    elif re.search(r"#\d{1,5}", Remaining):
        UnitNumber = re.search(r"\d{1,5}", Remaining).group(0)
        MailingAddr = MailingAddr + " " + UnitNumber
        Remaining = Remaining.split(UnitNumber)[1]
    elif re.search(r"#[A-Z]-\d{1,4}", Remaining):
        UnitNumber = re.search(r"#[A-Z]-\d{1,4}", Remaining).group(0)
        MailingAddr = MailingAddr + " " + UnitNumber
        Remaining = Remaining.split(UnitNumber)[1]
    else:
        Remaining = Remaining
    # print("Remaining: " + Remaining)

    # Split the Remaining into City, State, and Zip
    try:
        State = Remaining.split(" ")[-2]
        Zip = Remaining.split(" ")[-1]
        Zip = Zip[0:5]
        City = Remaining.split(State)[0]
        # print("City: " + City)
    except:
        City = ""
        State = ""
        Zip = ""
        # Print the error
        print("Exception: " + Remaining)
        print("error" + str(sys.exc_info()[0]))

    # Return the Mailing Address, Unit Number, City, State, Zip
    return MailingAddr, City, State, Zip


# This Function will take a dataframe and grab the address' from the Broward County Property Appraiser Website
def GetAddress(driver, df):
    # Create the Address, City, State, Zip, MailingAddress, MailingCity, MailingState, MailingZip columns,
    # Just Market Value, Taxes, Bed, Bath, SqFt
    df["Address"] = ""
    df["City"] = ""
    df["State"] = ""
    df["Zip"] = ""
    df["MailingAddress"] = ""
    df["MailingCity"] = ""
    df["MailingState"] = ""
    df["MailingZip"] = ""
    df["JustMarketValue"] = ""
    df["Taxes"] = ""
    df["Bed"] = ""
    df["Bath"] = ""
    df["SqFt"] = ""

    # Loop through the dataframe and grab the address for each row
    for index, row in df.iterrows():
        # Open the Broward County Property Appraiser Website and wait for the name field to load
        driver.get("https://bcpa.net/RecName.asp")
        try:
            WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.ID, "Name")))
        except:
            print("Website did not load")
            continue
        time.sleep(2)

        # Enter the Name into the name field and press entDCer
        try:
            Name = df.at[index, "LastName"] + ", " + df.at[index, "FirstName"]
            NameField = driver.find_element(By.ID, "Name")
            NameField.send_keys(Name)
            NameField.send_keys(Keys.ENTER)
            time.sleep(3)
        except:
            # print the error and skip this row
            print("Error: " + str(sys.exc_info()[0]))
            df = SetNAN(index, df)
            df.at[index, "CompanyName"] = np.nan
            continue

        # Check the url to see if the search returned any results
        if driver.current_url.__contains__("RecSearch.asp"):
            # If the search returned multiple results, then skip this row
            print("Multiple Results Found/No Results Found")
            df = SetNAN(index, df)
            continue
        else:
            # If the Search returned one result, then grab the address
            try:
                # Wait for element with class="BodyCopyBold9" to load
                WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.CLASS_NAME, "BodyCopyBold9")))
            except:
                print("Website did not load")
                df = SetNAN(index, df)
                continue
            time.sleep(2)

        # Grab the address from the google maps link
        Address = driver.find_element(By.CLASS_NAME, "BodyCopyBold9").find_element(By.TAG_NAME, "a").text
        City = Address.split(",")[1].split("FL")[0]
        State = Address.split(" ")[-2].split(" ")[0]
        Zip = Address.split(",")[1].split("FL")[1].split(" ")[1]

        # Remove the extra spaces at the beginning and end of the City, State, and Zip
        City = City.strip()
        State = State.strip()
        Zip = Zip.strip()[0:5]

        # Add to the dataframe
        df.at[index, "Address"] = Address.split(",")[0]
        df.at[index, "City"] = City
        df.at[index, "State"] = State
        df.at[index, "Zip"] = Zip

        # Grab the Mailing address 2 BodyCopyBold9 elements down
        MailingAddress = driver.find_elements(By.CLASS_NAME, "BodyCopyBold9")[2].text
        # print("Mailing Address Before Split: " + MailingAddress)

        # Create a struct to hold the Mailing Address, City, State, Zip
        MailingAddressStruct = SplitMailingAddress(MailingAddress)
        # print("Mailing Address: " + MailingAddressStruct[0])
        # print("Mailing City: " + MailingAddressStruct[1])
        # print("Mailing State: " + MailingAddressStruct[2])
        # print("Mailing Zip: " + MailingAddressStruct[3])
        df.at[index, "MailingAddress"] = MailingAddressStruct[0]
        df.at[index, "MailingCity"] = MailingAddressStruct[1]
        df.at[index, "MailingState"] = MailingAddressStruct[2]
        df.at[index, "MailingZip"] = MailingAddressStruct[3]

        # Grab the Just Market Value, Taxes, Bed, Bath, SqFt
        # The Just Market Value is at the 49th td element
        JustMarketValue = driver.find_elements(By.TAG_NAME, "td")[47].text
        # print("Just Market Value: " + JustMarketValue)
        df.at[index, "JustMarketValue"] = JustMarketValue

        # Weird check to see if current year has tax info
        try:
            Taxes = driver.find_elements(By.TAG_NAME, "td")[49].text
            # find if the string contains a $ sign
            if Taxes.__contains__(" "):
                Taxes = driver.find_elements(By.TAG_NAME, "td")[55].text
        except:
            Taxes = driver.find_elements(By.TAG_NAME, "td")[55].text

        # print("Taxes: " + Taxes)
        df.at[index, "Taxes"] = Taxes

        BedBath = driver.find_elements(By.TAG_NAME, "td")[160].text
        if BedBath.__contains__("its"):
            BedBath = driver.find_elements(By.TAG_NAME, "td")[161].text
        if BedBath.__contains__("/"):
            # remove the first 2 characters from the string and split the string by "/"
            Bed = BedBath[2:].split("/")[0]
            Bath = BedBath[2:].split("/")[1]
            # print("Bed: " + Bed)
            # print("Bath: " + Bath)
            df.at[index, "Bed"] = Bed
            df.at[index, "Bath"] = Bath
        else:
            df.at[index, "Bed"] = np.nan
            df.at[index, "Bath"] = np.nan

        SqFt = driver.find_elements(By.TAG_NAME, "td")[158].text
        if SqFt.__contains__("Adj. Bldg. S.F."):
            SqFt = driver.find_elements(By.TAG_NAME, "td")[159].text
        # print("SqFt: " + SqFt)
        df.at[index, "SqFt"] = SqFt
    return df


# Testing the functions
def Run(CurrentDocType, StartDate=None, EndDate=None):
    # Init the Driver
    driver = InitDriver()

    # Search for the document type and scrape the results
    Search(driver, DocTypes[CurrentDocType], StartDate, EndDate)
    df = Scrape(driver, DocTypes[CurrentDocType])
    print(df)

    # Separate the Names
    df = SeparateNames(df)

    # Temporarily save the dataframe to a csv file
    # SaveTo = "Pre-" + str(CurrentDocType) + ".csv"
    # df.to_csv(SaveTo, index=False)
    print(df)

    # Read the csv file back into a dataframe and call the GetAddress function
    df = GetAddress(driver, df)

    # Drop any row with a NAN value in the address column
    df = df.dropna(subset=["Address"])

    # If there are no company names then drop the column from the dataframe
    if df["CompanyName"].isnull().all():
        df = df.drop(columns=["CompanyName"])

    # If there are no CaseNumbers then drop the column from the dataframe
    if df["CaseNumber"].isnull().all():
        df = df.drop(columns=["CaseNumber"])

    # If there is no Mailing City or Mailing Zip then drop the row

    # Add Date and Save
    if StartDate is None or EndDate is None:
        print("No StartDate or EndDate given")
        Yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        # make yesterday's date a string and replace the slashes with dashes
        Yesterday = str(Yesterday).split(" ")[0].replace("/", "-")
        SaveTo = str(DocTypes[CurrentDocType]) + str(Yesterday) + ".csv"
        print(SaveTo)
    else:
        print("Saving as yesterday")
        # Make StartDate a string and replace the slashes with dashes
        EndDate = str(EndDate).split(" ")[0].replace("/", "-")
        SaveTo = str(DocTypes[CurrentDocType]) + "-" + str(EndDate) + ".csv"
        print(SaveTo)

    df.to_csv(SaveTo, index=False)
    driver.quit()
    return print("Finished Scraping " + str(DocTypes[CurrentDocType]))


# Run("DC")
# time.sleep(2)
# Run("LP", "04/13/2023", "04/14/2023")
# time.sleep(5)
# Run("PRO", "04/13/2023", "04/14/2023")
# time.sleep(5)
# Run("PALIE", "03/01/2023", "04/14/2023")
