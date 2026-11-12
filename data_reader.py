from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# PROJECT AND FILE PATHS
# ---------------------------------------------------------

PROJECT_FOLDER = Path(__file__).resolve().parent

DATA_FILE = (
    PROJECT_FOLDER
    / "data"
    / "Philippines_SFE_Dummy_Data.xlsx"
)

SHEET_NAME = "Weekly_Sales"


# ---------------------------------------------------------
# REQUIRED COLUMNS
# ---------------------------------------------------------

REQUIRED_COLUMNS = [
    "Week_Start",
    "Week_No",
    "Rep_ID",
    "Rep_Name",
    "Team",
    "District_Manager",
    "Region",
    "City",
    "Latitude",
    "Longitude",
    "Indication",
    "Product",
    "Unit_Price_PHP",
    "Gross_Units",
    "Returns",
    "Net_Sales_PHP",
    "Unit_Target",
    "Total_Calls",
    "Productive_Calls",
    "Unique_HCPs",
    "New_HCPs",
    "Samples_Distributed",
    "Data_Completeness_Pct",
    "Channel",
    "Transaction_ID",
]


NUMERIC_COLUMNS = [
    "Week_No",
    "Latitude",
    "Longitude",
    "Unit_Price_PHP",
    "Gross_Units",
    "Returns",
    "Net_Sales_PHP",
    "Unit_Target",
    "Total_Calls",
    "Productive_Calls",
    "Unique_HCPs",
    "New_HCPs",
    "Samples_Distributed",
    "Data_Completeness_Pct",
]


TEXT_COLUMNS = [
    "Rep_ID",
    "Rep_Name",
    "Team",
    "District_Manager",
    "Region",
    "City",
    "Indication",
    "Product",
    "Channel",
    "Transaction_ID",
]


# ---------------------------------------------------------
# CONVERT INCORRECT EXCEL DATE VALUES BACK TO NUMBERS
# ---------------------------------------------------------

def convert_excel_date_to_number(series):
    """
    Excel may incorrectly store a numeric sales column with a date format.

    Pandas then reads the number as a datetime. This function converts
    those dates back into their original Excel numeric serial values.
    """

    return (
        series - pd.Timestamp("1899-12-30")
    ) / pd.Timedelta(days=1)


# ---------------------------------------------------------
# VALIDATE COLUMNS
# ---------------------------------------------------------

def validate_columns(df):
    """
    Confirms that all required columns exist in the Excel sheet.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        missing_text = ", ".join(missing_columns)

        raise ValueError(
            "The Weekly_Sales sheet is missing these columns: "
            f"{missing_text}"
        )


# ---------------------------------------------------------
# CLEAN THE DATA
# ---------------------------------------------------------

def clean_sales_data(df):
    """
    Cleans dates, numeric fields and text fields.
    """

    df = df.copy()

    # Remove spaces from Excel column names
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    validate_columns(df)

    # Correct the reporting week
    df["Week_Start"] = pd.to_datetime(
        df["Week_Start"],
        errors="coerce",
    )

    # Convert numeric fields
    for column in NUMERIC_COLUMNS:

        if pd.api.types.is_datetime64_any_dtype(df[column]):

            print(
                f"Correcting Excel date formatting in: {column}"
            )

            df[column] = convert_excel_date_to_number(
                df[column]
            )

        else:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # Clean text columns
    for column in TEXT_COLUMNS:

        df[column] = (
            df[column]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
        )

    # Remove rows where the reporting week is missing
    df = df.dropna(
        subset=["Week_Start"]
    )

    # Replace missing numerical values
    for column in NUMERIC_COLUMNS:

        df[column] = df[column].fillna(0)

    # Avoid invalid geographic records
    df["Latitude"] = df["Latitude"].clip(
        lower=4,
        upper=22,
    )

    df["Longitude"] = df["Longitude"].clip(
        lower=116,
        upper=127,
    )

    # Calculated record-level metrics
    df["Net_Units"] = (
        df["Gross_Units"] - df["Returns"]
    ).clip(lower=0)

    df["Target_Attainment_Pct"] = (
        df["Gross_Units"]
        / df["Unit_Target"].replace(0, pd.NA)
        * 100
    ).fillna(0)

    df["Productive_Call_Rate_Pct"] = (
        df["Productive_Calls"]
        / df["Total_Calls"].replace(0, pd.NA)
        * 100
    ).fillna(0)

    df["Return_Rate_Pct"] = (
        df["Returns"]
        / df["Gross_Units"].replace(0, pd.NA)
        * 100
    ).fillna(0)

    # Sort data chronologically
    df = df.sort_values(
        by=[
            "Week_Start",
            "Region",
            "Team",
            "Rep_ID",
        ]
    ).reset_index(drop=True)

    return df


# ---------------------------------------------------------
# MAIN DATA-READING FUNCTION
# ---------------------------------------------------------

def load_sales_data():
    """
    Reads and cleans the Weekly_Sales sheet.
    """

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            "\nExcel file not found.\n\n"
            f"Expected location:\n{DATA_FILE}\n\n"
            "Check that:\n"
            "1. A folder named data exists.\n"
            "2. The Excel file is inside the data folder.\n"
            "3. The filename is exactly "
            "Philippines_SFE_Dummy_Data.xlsx"
        )

    df = pd.read_excel(
        DATA_FILE,
        sheet_name=SHEET_NAME,
        engine="openpyxl",
    )

    df = clean_sales_data(df)

    print("\nDATA LOADED SUCCESSFULLY")
    print(f"Excel file: {DATA_FILE}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")
    print(
        "Reporting period:",
        df["Week_Start"].min().date(),
        "to",
        df["Week_Start"].max().date(),
    )
    print(
        f"Total sales: PHP "
        f"{df['Net_Sales_PHP'].sum():,.0f}"
    )

    return df


# ---------------------------------------------------------
# TEST THIS MODULE DIRECTLY
# ---------------------------------------------------------

if __name__ == "__main__":

    sales_data = load_sales_data()

    print("\nDATA TYPES")
    print(sales_data.dtypes)

    print("\nFIRST FIVE RECORDS")
    print(sales_data.head())