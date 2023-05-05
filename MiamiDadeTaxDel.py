# This file was writen by Carick Brandt in 5/2023

# Import the needed modules
import os
import pandas as pd

# Check if the end of a string is " LE" with nothing after it
def CheckLE(Name: str):
    try:
        if Name.endswith(" LE"):
            return Name[:-3]
        elif Name.endswith(" (LE)"):
            return Name[:-5]
    except:
        print("Error in CheckLE. Just Returning the Name: " + Name)
        return Name
    return Name

# Check if the Name has a " &". If it is we want what comes before " &".
def CheckAnd(Name: str):
    if " &" in Name:
        # Check if there is a first and last name before the " &", If there is then return the first name
        if len(Name.split(" &")[0].split(" ")) > 1:
            return Name.split(" &")[0]
        # Else return the First string before a space and the last string after a space
        else:
            return Name.split(" ")[0] + " " + Name.split(" ")[-1]
    else:
        return Name

# Check for Common Suffices For a persons Name and remove them from the name
def CheckSuffices(Name: str):
    # Create a list of common suffices
    Suffices = [" JR", " SR", " II", " III", " IV"]

    # Check if the Name has " LE" at the end of it.
    Name = CheckLE(Name)

    # Check if the Name has " &" in it.
    Name = CheckAnd(Name)

    # Loop through the suffices and check if they are in the name
    for Suffix in Suffices:
        if Name.endswith(Suffix):
            return Name.replace(Suffix, "")

    # If the name does not have a suffix then return the name
    return Name

# Use a list of SplitInfo to find out if the Row is a company/Esate.
def CheckCompany(Name: str):
    # SplitInfo is a list of lists that will hold the information for the split names. An issue might occur while trying to see if LE is at the very end of the name.
    SplitInfo = ["EST OF", " LLC", " (EST OF)", " (TR)", " LP", " INC", " JTRS", " TRUST", " LIV", " ARENAS", " INVESTMENTS", "SETTLES", "INTERNATIONAL", "INVESTMENT"]
    # Loop through the SplitInfo and check if it is in the name
    Name = CheckAnd(Name)
    for Split in SplitInfo:
        if Split in Name:
            return True
    return False


# This function will the dataframe into two dataframes, one for the Companies or Esstates and one for the individuals.
# For the Individuals it will also split the names into firstName, MiddleName, LastName.
def SplitNames(Filepath: str):
    # Open the file and read it into a dataframe
    df = pd.read_csv(Filepath)

    # Change the Column Name for "Owner Name 1" to "First Name" on the original dataframe
    df.rename(columns={"Owner Name 1": "First Name"}, inplace=True)
    # Add a new column right next to the "Owner Name 1" column name Last Name
    df.insert(df.columns.get_loc("First Name") + 1, "Last Name", "")
    df.insert(df.columns.get_loc("First Name") + 1, "Middle Name", "")

    # Create two new dataframes one for the Individuals and one for the Companies. Using the Same Column Names as the original dataframe
    Individuals = pd.DataFrame(columns=df.columns)
    Companies = pd.DataFrame(columns=df.columns)

    # Loop through the Dataframe by row only looking at the Owner Name 1 column
    for index, row in df.iterrows():
        # Check if the row is a company or estate
        if CheckCompany(row["First Name"]):
            # Add the row to the Companies Dataframe with the new column title for the Owner Name 1
            Companies.loc[index] = row
        # Since the row is not a company or estate then it is an individual, so we need to split the name
        else:
            Individuals.loc[index] = row
            # Check if the name has a suffix and remove it
            Name = CheckSuffices(row["First Name"])
            # If we are left with a name that has two substrings seperated by a space then we can split the name into first and last name
            if len(Name.split(" ")) == 2:
                # Split the name into first and last name and add them to the Individuals Dataframe
                Individuals.loc[index, "First Name"] = Name.split(" ")[0]
                Individuals.loc[index, "Last Name"] = Name.split(" ")[1]
            # If we are left with a name that has 3 substrings seperated by a space then we can split the name into First, Middle, and Last Name
            elif len(Name.split(" ")) == 3:
                # Split the name into first, middle, and last name and add them to the Individuals Dataframe
                Individuals.loc[index, "First Name"] = Name.split(" ")[0]
                Individuals.loc[index, "Middle Name"] = Name.split(" ")[1]
                Individuals.loc[index, "Last Name"] = Name.split(" ")[2]
            # If we are left with a name that has more than 3 substrings seperated by a space then we can split the name into First, Middle, and Last Name.
            # With the Last Name being the complete substring after the second space
            elif len(Name.split(" ")) > 3:
                # Split the name into first, middle, and last name and add them to the Individuals Dataframe
                Individuals.loc[index, "First Name"] = Name.split(" ")[0]
                # Middle Name should be the Two Substrings after the first space and before the last space
                Individuals.loc[index, "Middle Name"] = Name.split(" ")[1] + " " + Name.split(" ")[2]
                Individuals.loc[index, "Last Name"] = Name.split(" ")[3]

    # Remove the "Last Name" column from the Companies Dataframe and rename the "First Name" Column to "Company/Estate/Trust"
    Companies.drop(columns=["Last Name", "Middle Name"], inplace=True)
    Companies.rename(columns={"First Name": "Company/Estate/Trust"}, inplace=True)

    # Reset the index for both the Individuals and Companies Dataframes
    Individuals.reset_index(drop=True, inplace=True)
    Companies.reset_index(drop=True, inplace=True)

    return Individuals, Companies


# Main call
if __name__ == "__main__":
    file = os.getcwd() + "\\TaxDel.csv"
    People, Trust = SplitNames(file)
    PeopleSave = os.getcwd() + "\\MiamiDadeTaxDelIndividuals.csv"
    People.to_csv(PeopleSave, index=False)
    TrustSave = os.getcwd() + "\\MiamiDadeTaxDelTrusts.csv"
    Trust.to_csv(TrustSave, index=False)
    print("Completed!")
