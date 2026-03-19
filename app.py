import streamlit as st
import pandas as pd
import numpy as np
import io

# Streamlit Page Config
st.set_page_config(page_title="Lab Referral Automation", page_icon="🏥", layout="centered")

st.title("🏥 Lab Referral Full Automation")
st.markdown("আপনার মূল **Raw Data (Excel)** ফাইলটি আপলোড করুন। অ্যাপটি স্বয়ংক্রিয়ভাবে কমিশন হিসাব করে এবং 3 টি অপশনের রিপোর্ট তৈরি করে একটি মাস্টার রেজাল্ট ফাইল আপনাকে ডাউনলোডের জন্য দেবে।")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload Raw Data (Excel File)", type=["xlsx", "xls"])

if uploaded_file:
    try:
        with st.spinner("অটোমেশন চলছে... দয়া করে অপেক্ষা করুন..."):
            
            # 1. Read the raw data (skipping the first empty row)
            df = pd.read_excel(uploaded_file, skiprows=1)

            # 2. ADD CALCULATION COLUMNS 
            # (নিচের লজিকগুলো আপনার Result ফাইলের মতো করে সাজানো)
            
            # Discount Allowed = Discount / Gross Amount
            df['Discount Allowed'] = np.where(df['Gross Amount'] > 0, df['Discount'] / df['Gross Amount'], 0)
            
            # Balance Discount = 0.25 (25%) by default
            df['Balance Discount'] = 0.25 
            
            # Net Payable = Net Amount * Balance Discount
            df['Net Payable'] = (df['Net Amount'] * df['Balance Discount']).fillna(0)

            # Other Lab Refer Payable Calculation (কমিশনের লজিক)
            def calculate_commission(row):
                referral = str(row['Other Lab Refer']).strip()
                # যদি referral না থাকে, কমিশন 0
                if referral in ['N.A.', 'nan', '', 'None']:
                    return 0
                else:
                    # এখানে 15% (0.15) কমিশন ধরা হয়েছে। 
                    # আপনার যদি অন্য রেট থাকে, তাহলে 0.15 এর জায়গায় সেটা বসিয়ে দেবেন।
                    return row['Net Amount'] * 0.15 

            df['Other Lab Refer Payable'] = df.apply(calculate_commission, axis=1)

            # Round off the columns to avoid decimals
            df['Net Payable'] = df['Net Payable'].round(0)
            df['Other Lab Refer Payable'] = df['Other Lab Refer Payable'].round(0)

            # 3. CLEAN DATA FOR DISPLAY OPTIONS
            df_clean = df.copy()
            df_clean['Other Lab Refer'] = df_clean['Other Lab Refer'].astype(str).str.strip()
            df_clean = df_clean[~df_clean['Other Lab Refer'].isin(['N.A.', 'nan', '', 'None'])]

            agg_columns = {
                'Gross Amount': 'sum',
                'Discount': 'sum',
                'Net Amount': 'sum',
                'Other Lab Refer Payable': 'sum'
            }

            # Generate Option 1, 2, 3
            option_1 = df_clean.groupby('Other Lab Refer').agg(agg_columns).reset_index()
            option_2 = df_clean.groupby(['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name']).agg(agg_columns).reset_index()
            
            if 'Investigation Name' in df_clean.columns:
                option_3 = df_clean.groupby(['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name', 'Investigation Name']).agg(agg_columns).reset_index()
            else:
                option_3 = pd.DataFrame()

            # Rename columns to match exact pivot table format
            rename_mapping = {
                'Gross Amount': 'Sum of Gross Amount',
                'Discount': 'Sum of Discount',
                'Net Amount': 'Sum of Net Amount',
                'Other Lab Refer Payable': 'Sum of Other Lab Refer Payable'
            }
            option_1.rename(columns=rename_mapping, inplace=True)
            option_2.rename(columns=rename_mapping, inplace=True)
            option_3.rename(columns=rename_mapping, inplace=True)

            # 4. EXPORT ALL DATA TO A SINGLE IN-MEMORY EXCEL FILE
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                # Main sheet with new calculated columns
                df.to_excel(writer, sheet_name='Calculation Sheet', index=False)
                # Pivot report sheets
                option_1.to_excel(writer, sheet_name='Display (Option-1)', index=False)
                option_2.to_excel(writer, sheet_name='Display (Option-2)', index=False)
                if not option_3.empty:
                    option_3.to_excel(writer, sheet_name='Display (Option-3)', index=False)

            st.success("✅ ক্যালকুলেশন এবং রিপোর্ট তৈরি সফল হয়েছে!")

            # 5. Download Button for the final Result file
            st.download_button(
                label="📥 Download Master Result File",
                data=excel_buffer.getvalue(),
                file_name="Automated_Result_File.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"দুঃখিত, একটি সমস্যা হয়েছে: {e}")
