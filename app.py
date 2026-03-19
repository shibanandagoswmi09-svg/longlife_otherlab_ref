import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Lab Referral Report Generator", page_icon="🏥", layout="centered")

st.title("🏥 Lab Referral Report Generator")
st.markdown("Upload your **Calculation Sheet (CSV)** below to instantly generate the 3 Display Option Pivot tables.")

# 1. The File Uploader
uploaded_file = st.file_uploader("Upload Calculation Sheet", type=["csv"])

if uploaded_file:
    try:
        with st.spinner("Generating reports..."):
            # 2. Read the uploaded file directly (skipping the blank top row)
            df = pd.read_csv(uploaded_file, skiprows=1)

            # 3. Clean the data
            df_clean = df.dropna(subset=['Other Lab Refer']).copy()
            df_clean['Other Lab Refer'] = df_clean['Other Lab Refer'].astype(str).str.strip()
            df_clean = df_clean[~df_clean['Other Lab Refer'].isin(['N.A.', 'nan', ''])]

            # Ensure we have the right columns
            agg_columns = {
                'Gross Amount': 'sum',
                'Discount': 'sum',
                'Net Amount': 'sum',
                'Other Lab Refer Payable': 'sum'
            }

            # Safely convert to numeric
            for col in agg_columns.keys():
                if col in df_clean.columns:
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)

            # 4. Generate the 3 Options
            # OPTION 1
            option_1 = df_clean.groupby('Other Lab Refer').agg(agg_columns).reset_index()
            
            # OPTION 2
            option_2 = df_clean.groupby(['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name']).agg(agg_columns).reset_index()
            
            # OPTION 3
            if 'Investigation Name' in df_clean.columns:
                option_3 = df_clean.groupby(['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name', 'Investigation Name']).agg(agg_columns).reset_index()
            else:
                option_3 = pd.DataFrame() # Fallback if column is missing

            # Rename columns
            rename_mapping = {
                'Gross Amount': 'Sum of Gross Amount',
                'Discount': 'Sum of Discount',
                'Net Amount': 'Sum of Net Amount',
                'Other Lab Refer Payable': 'Sum of Other Lab Refer Payable'
            }
            option_1.rename(columns=rename_mapping, inplace=True)
            option_2.rename(columns=rename_mapping, inplace=True)
            option_3.rename(columns=rename_mapping, inplace=True)

            # 5. Create an in-memory Excel file (Required for Streamlit Cloud)
            excel_buffer = io.BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                option_1.to_excel(writer, sheet_name='Display (Option-1)', index=False)
                option_2.to_excel(writer, sheet_name='Display (Option-2)', index=False)
                if not option_3.empty:
                    option_3.to_excel(writer, sheet_name='Display (Option-3)', index=False)

            st.success("✅ Reports generated successfully!")

            # 6. Provide the Download Button
            st.download_button(
                label="📥 Download Excel Reports (All 3 Options)",
                data=excel_buffer.getvalue(),
                file_name="Automated_Referral_Display_Reports.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
