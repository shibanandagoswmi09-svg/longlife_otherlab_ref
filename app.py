import pandas as pd

def generate_referral_reports(calculation_sheet_path):
    print("Loading Calculation Sheet...")
    # Read the data (skipping the first empty/total row just like in your file)
    df = pd.read_csv(calculation_sheet_path, skiprows=1)

    # Clean the data: Filter out empty referrals and "N.A."
    df_clean = df.dropna(subset=['Other Lab Refer']).copy()
    df_clean = df_clean[df_clean['Other Lab Refer'].str.strip() != 'N.A.']

    # Define the values we are calculating (The "Values" area in an Excel Pivot Table)
    agg_columns = {
        'Gross Amount': 'sum',
        'Discount': 'sum',
        'Net Amount': 'sum',
        'Other Lab Refer Payable': 'sum'
    }

    print("Processing Option 1 (High-Level Summary)...")
    # OPTION 1: Group by Partner Lab only
    option_1 = df_clean.groupby('Other Lab Refer').agg(agg_columns).reset_index()

    print("Processing Option 2 (Patient/Work Order Level)...")
    # OPTION 2: Group by Lab -> Date -> Work Order -> Patient Name
    option_2 = df_clean.groupby(
        ['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name']
    ).agg(agg_columns).reset_index()

    print("Processing Option 3 (Investigation/Test Level)...")
    # OPTION 3: Group by Lab -> Date -> Work Order -> Patient -> Investigation Name
    option_3 = df_clean.groupby(
        ['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name', 'Investigation Name']
    ).agg(agg_columns).reset_index()

    # Rename the output columns to match your exact Excel format
    rename_mapping = {
        'Gross Amount': 'Sum of Gross Amount',
        'Discount': 'Sum of Discount',
        'Net Amount': 'Sum of Net Amount',
        'Other Lab Refer Payable': 'Sum of Other Lab Refer Payable'
    }
    
    option_1.rename(columns=rename_mapping, inplace=True)
    option_2.rename(columns=rename_mapping, inplace=True)
    option_3.rename(columns=rename_mapping, inplace=True)

    # Export all three options into a single Excel file with multiple tabs
    output_filename = "Automated_Referral_Display_Reports.xlsx"
    print(f"Exporting to {output_filename}...")
    
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        option_1.to_excel(writer, sheet_name='Display (Option-1)', index=False)
        option_2.to_excel(writer, sheet_name='Display (Option-2)', index=False)
        option_3.to_excel(writer, sheet_name='Display (Option-3)', index=False)

    print("✅ Automation Complete! Reports generated successfully.")

# --- Run the function ---
if __name__ == "__main__":
    # Ensure this matches the name of your calculation file
    file_path = "Other lab Referral Module-Result.xlsx - Calculation Sheet.csv" 
    generate_referral_reports(file_path)
