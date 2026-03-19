import pandas as pd
import numpy as np

def process_lab_referrals(input_file, output_file):
    print(f"Reading raw data from: {input_file}...")
    
    # 1. Read the raw data (skip header row if necessary)
    df = pd.read_excel(input_file, skiprows=1)

    # 2. ADD CALCULATION COLUMNS (Mimicking your Calculation Sheet)
    # Niche hospital er logic onujayi percentage gulo calculate kora hoyeche. 
    # Apnar jodi kono nirdishto % rule thake, apni ekhane change korte paren.
    
    # Example logic for Discount Allowed (Discount / Gross Amount)
    df['Discount Allowed'] = np.where(df['Gross Amount'] > 0, df['Discount'] / df['Gross Amount'], 0)
    
    # Balance Discount (As seen in your file, often 0.25 ba 25% thake)
    df['Balance Discount'] = 0.25 
    
    # Net Payable calculation
    df['Net Payable'] = df['Net Amount'] * df['Balance Discount']

    # Other Lab Refer Payable Calculation Logic
    def calculate_commission(row):
        referral = str(row['Other Lab Refer']).strip()
        # Jodi referral na thake
        if referral in ['N.A.', 'nan', '', 'None']:
            return 0
        else:
            # Ekhane apni apnar hospital er actual commission rate (e.g., 10% ba 15%) boshabo
            # Udahoron: Net Amount er 15% dicchen (Change 0.15 to your actual rate)
            # Apni chaile department onujayi alada rule o likhte paren ekhane.
            return row['Net Amount'] * 0.15 

    df['Other Lab Refer Payable'] = df.apply(calculate_commission, axis=1)

    # Round off the calculated columns
    df['Net Payable'] = df['Net Payable'].round(0)
    df['Other Lab Refer Payable'] = df['Other Lab Refer Payable'].round(0)

    print("Calculations complete. Now generating Display Options...")

    # 3. CLEAN DATA FOR DISPLAY OPTIONS (Remove N.A. referrals)
    df_clean = df.copy()
    df_clean['Other Lab Refer'] = df_clean['Other Lab Refer'].astype(str).str.strip()
    df_clean = df_clean[~df_clean['Other Lab Refer'].isin(['N.A.', 'nan', '', 'None'])]

    # Aggregation columns for Pivot Tables
    agg_columns = {
        'Gross Amount': 'sum',
        'Discount': 'sum',
        'Net Amount': 'sum',
        'Other Lab Refer Payable': 'sum'
    }

    # Generate Option 1 (Lab Level)
    option_1 = df_clean.groupby('Other Lab Refer').agg(agg_columns).reset_index()

    # Generate Option 2 (Patient & Work Order Level)
    option_2 = df_clean.groupby(['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name']).agg(agg_columns).reset_index()

    # Generate Option 3 (Investigation Level)
    if 'Investigation Name' in df_clean.columns:
        option_3 = df_clean.groupby(['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name', 'Investigation Name']).agg(agg_columns).reset_index()
    else:
        option_3 = pd.DataFrame()

    # Rename columns to match the Result Excel Pivot Tables exactly
    rename_mapping = {
        'Gross Amount': 'Sum of Gross Amount',
        'Discount': 'Sum of Discount',
        'Net Amount': 'Sum of Net Amount',
        'Other Lab Refer Payable': 'Sum of Other Lab Refer Payable'
    }
    option_1.rename(columns=rename_mapping, inplace=True)
    option_2.rename(columns=rename_mapping, inplace=True)
    option_3.rename(columns=rename_mapping, inplace=True)

    # 4. EXPORT ALL DATA TO A SINGLE EXCEL FILE WITH 4 TABS
    print(f"Exporting all reports to {output_file}...")
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Pothom tab hobe main calculation sheet
        df.to_excel(writer, sheet_name='Calculation Sheet', index=False)
        # Baki tab gulo hobe pivot reports
        option_1.to_excel(writer, sheet_name='Display (Option-1)', index=False)
        option_2.to_excel(writer, sheet_name='Display (Option-2)', index=False)
        if not option_3.empty:
            option_3.to_excel(writer, sheet_name='Display (Option-3)', index=False)

    print("✅ Automation Successful! Master file created.")

# --- Run the function ---
if __name__ == "__main__":
    # Apnar input raw file er naam
    input_file_name = "Other lab Referral Module.xlsx" 
    # Je notun file ta toiri hobe tar naam
    output_file_name = "Final_Automated_Result_File.xlsx" 
    
    process_lab_referrals(input_file_name, output_file_name)
