import SetDates
import MiamiDadeRecordsPull
import BrowardRecordsPull

def CountyMenu():
    active = True
    while active:
        # Create a menu for MiamiDade Records Pull and Broward Records Pull
        print("Welcome to the South Florida Records Pull Program")
        print("Please select the county you would like to pull records from")
        print("1. Miami-Dade County")
        print("2. Broward County")
        print("3. Palm Beach County")
        print("4. Exit the Program")
        # Get the user input
        UserInput = input("Please enter the number of the county you would like to pull records from: ")
        # if the user enters 1 then run the MiamiDadeMenu function
        if UserInput == "1":
            MiamiDadeMenu()
        # if the user enters 2 then run the BrowardMenu function
        elif UserInput == "2":
            BrowardMenu()
        # if the user enters 3 then print a message saying that this county is not available yet
        elif UserInput == "3":
            print("Still working on this one")
        # if the user enters 4 then exit the program
        elif UserInput == "4":
            active = False
        # if the user enters anything else then print an error message
        else:
            print("Please enter a valid option")
    return 0


def MiamiDadeMenu():
    active = True
    while active:
        # Create a menu for the Miami-Dade Records Pull
        print("Welcome to the Miami-Dade Records Pull Program")
        print("Please select the type of records you would like to pull")
        print("1. Lis Pendens")
        print("2. Death Certificates")
        print("3. Probates")
        print("4. Code Violations")
        print("5. Public unpaid accts")
        print("6. Evictions")
        print("7. Exit the Program")
        # Get the user input
        UserInput = input("Please enter the number of the records you would like to pull: ")
        # if the user enters 1 then get the dates and run the LisPendens function
        if UserInput == "1":
            StartDate, EndDate = SetDates.GetDates()
            MiamiDadeRecordsPull.Run("LIS", StartDate, EndDate)
        # if the user enters 2 then get the dates and run the DeathCertificates function
        elif UserInput == "2":
            StartDate, EndDate = SetDates.GetDates()
            MiamiDadeRecordsPull.Run("DCE", StartDate, EndDate)
        # if the user enters 3 then get the dates and run the Probates function
        elif UserInput == "3":
            StartDate, EndDate = SetDates.GetDates()
            MiamiDadeRecordsPull.Run("PAD", StartDate, EndDate)
        # if the user enters 4 then get the dates and run the CodeViolations function
        elif UserInput == "4":
            print("Still working on this one")
        # if the user enters 5 then get the dates and run the PublicUnpaidAccts function
        elif UserInput == "5":
            print("Still working on this one")
        # if the user enters 6 then get the dates and run the Evictions function
        elif UserInput == "6":
            print("Still working on this one")
        # if the user enters 7 then exit the program
        elif UserInput == "7":
            active = False
        # if the user enters anything else then print an error message
        else:
            print("Please enter a valid option")
    return 0


def BrowardMenu():
    Active = True
    while Active:
        # Create a menu for the Broward Records Pull
        print("Welcome to the Broward Records Pull Program")
        print("Please select the type of records you would like to pull")
        print("1. Lis Pendens")
        print("2. Death Certificates")
        print("3. Probates")
        print("4. Property Tax Lien")
        print("5. Evictions")
        print("6. Code Violations")
        print("7. Exit the Program")
        # Get the user input
        UserInput = input("Please enter the number of the records you would like to pull: ")
        # if the user enters 1 then get the dates and run the LisPendens function
        if UserInput == "1":
            StartDate, EndDate = SetDates.GetDates()
            BrowardRecordsPull.Run("LP", StartDate, EndDate)
        # if the user enters 2 then get the dates and run the DeathCertificates function
        elif UserInput == "2":
            StartDate, EndDate = SetDates.GetDates()
            BrowardRecordsPull.Run("DC", StartDate, EndDate)
        # if the user enters 3 then get the dates and run the Probates function
        elif UserInput == "3":
            StartDate, EndDate = SetDates.GetDates()
            BrowardRecordsPull.Run("PRO", StartDate, EndDate)
        # if the user enters 4 then get the dates and run the PropertyTaxLien function
        elif UserInput == "4":
            StartDate, EndDate = SetDates.GetDates()
            BrowardRecordsPull.Run("PALIE", StartDate, EndDate)
        # if the user enters 5 then get the dates and run the Evictions function
        elif UserInput == "5":
            print("Still working on this one")
        # if the user enters 6 then get the dates and run the CodeViolations function
        elif UserInput == "6":
            print("Still working on this one")
        # if the user enters 7 then exit the program
        elif UserInput == "7":
            Active = False
        # if the user enters anything else then print an error message
        else:
            print("Please enter a valid option")
    return 0

if __name__ == "__main__":
    CountyMenu()