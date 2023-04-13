# This file was written by Carick Brandt on 4/2023
# This module will be used to scrape the https://officialrecords.broward.org/AcclaimWeb/search/SearchTypeDocType
# website for the relevant DocType and returns a list of FirstNames, and LastNames from the First Indirect Name column
# from the search results.

# Import the necessary modules
import os
import re
import time
import datetime
import pandas as pd
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
    driver.get("https://google.com")
    time.sleep(2)
    driver.get("https://officialrecords.broward.org/AcclaimWeb/search/SearchTypeDocType")
    driver.find_element(By.ID, "btnButton").click()
    time.sleep(2)
    return driver


# This function will take a DocType, StartDate, and EndDate and Pull up Search Results for the DocType
def Search(driver, DocType, StartDate=None, EndDate=None):

    # Select the DocType from the dropdown
    dropdown = driver.find_element(By.ID, "DocTypesDisplay-input")
    dropdown.send_keys(Keys.CONTROL + "a")
    dropdown.send_keys(Keys.DELETE)
    dropdown.send_keys(DocType)
    time.sleep(4)

    # If there is no StartDate or EndDate, use the default values
    if StartDate is None or EndDate is None:
        StartDate, EndDate = NoDates()

    # Select the EndDateField
    EndDateField = driver.find_element(By.ID, "RecordDateTo")
    EndDateField.click()
    EndDateField.send_keys(Keys.CONTROL + "a")
    EndDateField.send_keys(Keys.DELETE)
    EndDateField.send_keys(EndDate)
    time.sleep(4)

    # Select the StartDateField
    StartDateField = driver.find_element(By.ID, "RecordDateFrom")
    StartDateField.click()
    StartDateField.send_keys(Keys.CONTROL + "a")
    StartDateField.send_keys(Keys.DELETE)
    StartDateField.send_keys(StartDate)
    StartDateField.send_keys(Keys.ENTER)

    return 0

# This Function will Scrape the Search Results and return a dataframe
def Scrape(driver, DocType):
    # Traverse the table and get the First Inderect Name column
    try:
        WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.ID, "SearchGridContainer")))
    except:
        print("No Results Found")
        return None
    time.sleep(2)
    table = driver.find_element(By.ID, "SearchGridContainer")
    rows = table.find_elements(By.TAG_NAME, "tr")
    FirstIndirectName = []
    FirstIndirectNameIndex: int
    CaseNumber = []
    for row in rows:
        columns = row.find_elements(By.TAG_NAME, "td")
        # for the first row, we need to find the column index for the First Indirect Name column, count the number of newlines in the row till we get to the column with First Indirect Name
        if row.text.__contains__("Cart\nConsideration\nFirst Direct Name\nFirst Indirect Name"):
            # Find the Number of Newlines are before First Indirect Name
            FirstIndirectNameIndex = row.text.count("\n", 0, row.text.index("First Indirect Name"))
            print("Found Indirect Name Index at pos: " + str(FirstIndirectNameIndex))
            continue
        else:
            FirstIndirectNameIndex = 3

        # print the indirect name column and append it to the FirstIndirectName list
        print("IndirectName: " + columns[FirstIndirectNameIndex].text)
        FirstIndirectName.append(columns[FirstIndirectNameIndex].text)

        # Open the new window and switch to it
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
                CaseNumber.append("NAN")
                break

        DocBlock = driver.find_element(By.CLASS_NAME, "docBlock")
        Details = DocBlock.find_elements(By.CLASS_NAME, "detailLabel")
        ListDocDetails = DocBlock.find_elements(By.CLASS_NAME, "listDocDetails")

        # Find the Details that has the Text "Case Number:"
        for Detail in Details:
            if Detail.text.__contains__("Case Number:"):
                print("Case Number: " + ListDocDetails[Details.index(Detail)].text)
                CaseNumber.append(ListDocDetails[Details.index(Detail)].text)
        time.sleep(2)

        # close the new window and switch back to the main window
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(6)

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
    # Create the First Name and Last Name columns
    df["FirstName"] = ""
    df["LastName"] = ""

    # if the FirstIndirectName column has a comma, then the First Name is the Word after the comma and before the space
    # and the Last Name is the word at the beginning of the string
    # loop through the dataframe and fill the First Name and Last Name columns
    for index, row in df.iterrows():
        if "," in row["FirstIndirectName"]:
            df.at[index, "FirstName"] = row["FirstIndirectName"].split(",")[1].split(" ")[0]
            df.at[index, "LastName"] = row["FirstIndirectName"].split(",")[0]
            df.at[index, "FirstIndirectName"] = "NAN"
        else:
            df.at[index, "FirstName"] = "NAN"
            df.at[index, "LastName"] = "NAN"

    # Rename FirstIndirectName to CompanyName
    df = df.rename(columns={"FirstIndirectName": "CompanyName"})
    return df

# Sets row to NAN if needed.
def SetNAN(index, df):
    df.at[index, "Address"] = "NAN"
    df.at[index, "City"] = "NAN"
    df.at[index, "State"] = "NAN"
    df.at[index, "Zip"] = "NAN"
    df.at[index, "MailingAddress"] = "NAN"
    df.at[index, "MailingCity"] = "NAN"
    df.at[index, "MailingState"] = "NAN"
    df.at[index, "MailingZip"] = "NAN"
    df.at[index, "JustMarketValue"] = "NAN"
    df.at[index, "Taxes"] = "NAN"
    df.at[index, "Bed"] = "NAN"
    df.at[index, "Bath"] = "NAN"
    df.at[index, "SqFt"] = "NAN"
    return df


# This Function will Split a Mailing Address into house number, street direction, street name, street type, unit number (if applicable), City, State, Zip
def SplitMailingAddress(mailAddress):
    # Street Types
    StreetTypes = ["ALY", "AVE", "BND", "BLVD", "CSWY", "CIR", "CT", "CV", "DR", "EXT", "HWY", "HOLW", "ISLE", "LN",
                   "LNDG", "MNR", "MILE", "PARK", "PASS", "PATH", "PL", "PT", "RD", "ROW", "SQ", "ST", "TER", "TWP",
                   "TRCE", "TRL", "VIEW", "WALK", "WAY"]
    # City Names
    CityNames = ["COCONUT CREEK", "COOPER CITY", " CORAL SPRINGS", "DANIA BEACH", "DAVIE", "DEERFIELD BEACH",
                 "FORT LAUDERDALE", "HALLANDALE BEACH", "HILLSBORO BEACH", "HOLLYWOOD", "LAUDERDALE BY THE SEA",
                 "LAUDERDALE LAKES", "LAUDERHILL", "LAZY LAKE", "LIGHTHOUST POINT", "MARGATE", "MIRAMAR",
                 "NORTH LAUDERDALE", "OAKLAND PARK", "PARKLAND", "PEMBROKE PARK", "PEMBROKE PINES", "PLANTATION",
                 "POMPANO BEACH", "SEA RANCH LAKES", "SOUTHWEST RANCHES", "SUNRISE", "TAMARAC", "UNINCORPORATED",
                 "WEST PARK", "WILTON MANORS"]

    # Create the Variables to hold the Mailing Address, City
    MailingAddr = ""
    UnitNumber = ""
    City = ""
    Remaining = ""

    # Split the mailing address after an occurance of StreetTypes
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
    if re.search(r"UNIT \d+", Remaining):
        UnitNumber = re.search(r"UNIT \d+", Remaining).group(0)
        MailingAddr = MailingAddr + " " + UnitNumber
        Remaining = Remaining.split(UnitNumber)[1]
    elif re.search(r"#\d+", Remaining):
        UnitNumber = re.search(r"\d+", Remaining).group(0)
        MailingAddr = MailingAddr + " #" + UnitNumber
        Remaining = Remaining.split(UnitNumber)[1]
    elif re.search(r"#\d+[A-Z]", Remaining):
        UnitNumber = re.search(r"#\d+[A-Z]", Remaining).group(0)
        MailingAddr = MailingAddr + " #" + UnitNumber
        Remaining = Remaining.split(UnitNumber)[1]
    else:
        Remaining = Remaining

    # use City Names to find the City in the Remaining string
    for cityName in CityNames:
        if Remaining.__contains__(cityName):
            City = cityName
            Remaining = Remaining.split(cityName)[1]
            break

    # The Remaining String should now only contain the State and Zip Code
    State = Remaining.split(" ")[-2]
    Zip = Remaining.split(" ")[-1]
    Zip = Zip[0:5]

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
        Name = df.at[index, "LastName"] + ", " + df.at[index, "FirstName"]
        NameField = driver.find_element(By.ID, "Name")
        NameField.send_keys(Name)
        NameField.send_keys(Keys.ENTER)
        time.sleep(3)

        # Check the url to see if the search returned any results
        if driver.current_url.__contains__("RecSearch.asp"):
            # If the search returned multiple results, then skip this row
            print("Multiple Results Found")
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


        # print("Site: " + df.at[index, "Address"] + ", City: " + df.at[index, "City"] + ", State:" + df.at[index, "State"] + ", Zip: " + df.at[index, "Zip"])

        # Grab the Mailing address 2 BodyCopyBold9 elements down
        MailingAddress = driver.find_elements(By.CLASS_NAME, "BodyCopyBold9")[2].text
        print("Mailing Address Before Split: " + MailingAddress)

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
    return df



# Testing the functions
driver = InitDriver()
# Search(driver, DocTypes["LP"])
# df = Scrape(driver, DocTypes["LP"])
# df = SeparateNames(df)
# df.to_csv("Test.csv", index=False)
# print(df)
df = pd.read_csv("Test.csv")
df = GetAddress(driver, df)
df.to_csv("Test1.csv", index=False)
