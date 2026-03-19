import streamlit as st
import pandas as pd
import io

# Set page configuration
st.set_page_config(page_title="Lab Referral Dashboard", page_icon="🏥", layout="wide")

st.title("🏥 Lab Referral Automation Dashboard")
st.markdown("Upload your daily or monthly referral data to instantly generate partner payout and revenue reports.")

# Sidebar for file upload
st.sidebar.header("📂 Data Import")
uploaded_file = st.sidebar.file_uploader("Upload Referral File (CSV or Excel)", type=["csv", "xlsx"])

# --- SMART DATA LOADER FUNCTION ---
@st.cache_data
def load_and_clean_data(file_bytes, file_name):
    # Convert bytes back to a file-like object
    file = io.BytesIO(file_bytes)
    
    # 1. Find the actual header row (Scan the first 15 rows)
    if file_name.endswith('.csv'):
        df_raw = pd.read_csv(file, header=None, nrows=15)
    else:
        df_raw = pd.read_excel(file, header=None, nrows=15)
        
    header_row_index = 0
    for i, row in df_raw.iterrows():
        # Look for our key columns to identify the true header row
        row_values = [str(val).strip() for val in row.values]
        if 'Other Lab Refer' in row_values or 'Work Order ID' in row_values:
            header_row_index = i
            break
            
    # 2. Reset file pointer and read properly starting from the found header
    file.seek(0)
    if file_name.endswith('.csv'):
        df = pd.read_csv(file, skiprows=header_row_index)
    else:
        df = pd.read_excel(file, skiprows=header_row_index)
        
    return df

# --- MAIN APP LOGIC ---
if uploaded_file:
    try:
        # We pass the file as bytes so Streamlit's cache feature works properly
        file_bytes = uploaded_file.getvalue()
        df = load_and_clean_data(file_bytes, uploaded_file.name)

        # Ensure the required column exists before proceeding
        if 'Other Lab Refer' in df.columns:
            
            # 3. Clean data: Remove empty referrals and 'N.A.' safely
            df_clean = df.dropna(subset=['Other Lab Refer']).copy()
            # Convert to string safely to avoid errors on mixed data types
            df_clean['Other Lab Refer'] = df_clean['Other Lab Refer'].astype(str).str.strip()
            # Filter out 'N.A.' and 'nan'
            df_clean = df_clean[~df_clean['Other Lab Refer'].isin(['N.A.', 'nan', ''])]
            
            if df_clean.empty:
                st.warning("File loaded successfully, but no valid external lab referrals were found.")
                st.stop()

            # Top-level KPIs
            st.header("📊 High-Level Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            total_tests = len(df_clean)
            unique_labs = df_clean['Other Lab Refer'].nunique()
            
            # Safely convert financial columns to numeric, forcing errors to 0
            for col in ['Gross Amount', 'Discount', 'Net Amount']:
                if col in df_clean.columns:
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)

            total_net_rev = df_clean['Net Amount'].sum() if 'Net Amount' in df_clean.columns else 0
            
            col1.metric("Total Referred Tests", total_tests)
            col2.metric("Active Partner Labs", unique_labs)
            col3.metric("Total Net Revenue (₹)", f"₹{total_net_rev:,.2f}")
            
            # Check if Payable column exists (from the Calculation Sheet)
            if 'Other Lab Refer Payable' in df_clean.columns:
                df_clean['Other Lab Refer Payable'] = pd.to_numeric(df_clean['Other Lab Refer Payable'], errors='coerce').fillna(0)
                total_payable = df_clean['Other Lab Refer Payable'].sum()
                col4.metric("Total Partner Payout (₹)", f"₹{total_payable:,.2f}")
            elif 'Gross Amount' in df_clean.columns:
                col4.metric("Total Gross (₹)", f"₹{df_clean['Gross Amount'].sum():,.2f}")
            else:
                col4.metric("Data Note", "No Revenue Data")

            st.divider()

            # Generate Aggregated Report
            st.header("📋 Partner Lab Performance Report")
            
            # Determine aggregation dictionary dynamically based on available columns
            agg_dict = {}
            if 'Work Order ID' in df_clean.columns: agg_dict['Work Order ID'] = 'count'
            if 'Pt. Name' in df_clean.columns: agg_dict['Pt. Name'] = 'nunique'
            if 'Gross Amount' in df_clean.columns: agg_dict['Gross Amount'] = 'sum'
            if 'Discount' in df_clean.columns: agg_dict['Discount'] = 'sum'
            if 'Net Amount' in df_clean.columns: agg_dict['Net Amount'] = 'sum'
            if 'Other Lab Refer Payable' in df_clean.columns: agg_dict['Other Lab Refer Payable'] = 'sum'

            # Grouping the data
            if agg_dict:
                report_df = df_clean.groupby('Other Lab Refer').agg(agg_dict).reset_index()
                
                # Renaming columns for clarity
                rename_dict = {
                    'Work Order ID': 'Total Tests',
                    'Pt. Name': 'Unique Patients',
                    'Gross Amount': 'Gross Revenue (₹)',
                    'Discount': 'Total Discount (₹)',
                    'Net Amount': 'Net Revenue (₹)',
                    'Other Lab Refer Payable': 'Partner Payout (₹)'
                }
                report_df.rename(columns=rename_dict, inplace=True)
                
                # Sort by Net Revenue if it exists, otherwise by Total Tests
                if 'Net Revenue (₹)' in report_df.columns:
                    report_df = report_df.sort_values(by='Net Revenue (₹)', ascending=False)
                elif 'Total Tests' in report_df.columns:
                    report_df = report_df.sort_values(by='Total Tests', ascending=False)
                
                # Display the interactive dataframe
                st.dataframe(report_df, use_container_width=True, hide_index=True)

                # Visualizations
                if 'Net Revenue (₹)' in report_df.columns:
                    st.header("📈 Top 10 Labs by Net Revenue")
                    chart_data = report_df.head(10)[['Other Lab Refer', 'Net Revenue (₹)']].set_index('Other Lab Refer')
                    st.bar_chart(chart_data)

                # Download Option
                st.subheader("📥 Export Report")
                csv_buffer = io.StringIO()
                report_df.to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="Download Summarized Report as CSV",
                    data=csv_buffer.getvalue(),
                    file_name="Referral_Automation_Report.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Could not find the necessary columns (Work Order ID, Gross Amount, etc.) to build the report.")

        else:
            st.error("The uploaded file does not contain the required 'Other Lab Refer' column. Please verify the file.")
            # Show the columns it DID find to help troubleshoot
            st.write("Columns found in your file:", list(df.columns))

    except Exception as e:
        st.error("An error occurred while processing the file.")
        st.exception(e) # This will print the exact error on the screen to help debug!
else:
    st.info("👈 Please upload a data file from the sidebar to begin.")
