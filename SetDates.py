# This file was written by Carick brandt on 4/2023
# This file will handle the dates for the program

# Import the necessary libraries
import datetime

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
    # Set the StartDate to yesterday and the EndDate to the day before yesterday
    Yesterday = datetime.date.today() - datetime.timedelta(days=1)
    DayBeforeYesterDay = datetime.date.today() - datetime.timedelta(days=2)

    # Convert the dates to strings
    StartDate = DayBeforeYesterDay.strftime("%m/%d/%Y")
    EndDate = Yesterday.strftime("%m/%d/%Y")
    return StartDate, EndDate
