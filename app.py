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

if uploaded_file:
    try:
        # Read the file
        if uploaded_file.name.endswith('.csv'):
            # Read first few lines to check if we need to skip the first row (like your specific files)
            df_preview = pd.read_csv(uploaded_file, nrows=2)
            uploaded_file.seek(0) # Reset file pointer
            
            if 'Other Lab Refer' not in df_preview.columns:
                df = pd.read_csv(uploaded_file, skiprows=1)
            else:
                df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Ensure the required column exists before proceeding
        if 'Other Lab Refer' in df.columns:
            # Clean data: Remove empty referrals and 'N.A.'
            df_clean = df.dropna(subset=['Other Lab Refer']).copy()
            df_clean = df_clean[df_clean['Other Lab Refer'].str.strip() != 'N.A.']
            
            # Top-level KPIs
            st.header("📊 High-Level Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            total_tests = len(df_clean)
            unique_labs = df_clean['Other Lab Refer'].nunique()
            total_net_rev = df_clean['Net Amount'].sum()
            
            col1.metric("Total Referred Tests", total_tests)
            col2.metric("Active Partner Labs", unique_labs)
            col3.metric("Total Net Revenue (₹)", f"₹{total_net_rev:,.2f}")
            
            # Check if Payable column exists (from the Calculation Sheet)
            if 'Other Lab Refer Payable' in df_clean.columns:
                total_payable = df_clean['Other Lab Refer Payable'].sum()
                col4.metric("Total Partner Payout (₹)", f"₹{total_payable:,.2f}")
            else:
                col4.metric("Total Gross (₹)", f"₹{df_clean['Gross Amount'].sum():,.2f}")

            st.divider()

            # Generate Aggregated Report
            st.header("📋 Partner Lab Performance Report")
            
            # Determine aggregation dictionary dynamically based on available columns
            agg_dict = {
                'Work Order ID': 'count',
                'Pt. Name': 'nunique',
                'Gross Amount': 'sum',
                'Discount': 'sum',
                'Net Amount': 'sum'
            }
            if 'Other Lab Refer Payable' in df_clean.columns:
                agg_dict['Other Lab Refer Payable'] = 'sum'

            # Grouping the data
            report_df = df_clean.groupby('Other Lab Refer').agg(agg_dict).reset_index()
            
            # Renaming columns for clarity
            rename_dict = {
                'Work Order ID': 'Total Tests',
                'Pt. Name': 'Unique Patients',
                'Gross Amount': 'Gross Revenue (₹)',
                'Discount': 'Total Discount (₹)',
                'Net Amount': 'Net Revenue (₹)'
            }
            if 'Other Lab Refer Payable' in df_clean.columns:
                rename_dict['Other Lab Refer Payable'] = 'Partner Payout (₹)'
                
            report_df.rename(columns=rename_dict, inplace=True)
            
            # Sort by Net Revenue by default
            report_df = report_df.sort_values(by='Net Revenue (₹)', ascending=False)
            
            # Display the interactive dataframe
            st.dataframe(report_df, use_container_width=True, hide_index=True)

            # Visualizations
            st.header("📈 Top 10 Labs by Net Revenue")
            chart_data = report_df.head(10)[['Other Lab Refer', 'Net Revenue (₹)']].set_index('Other Lab Refer')
            st.bar_chart(chart_data)

            # Download Option
            st.subheader("📥 Export Report")
            
            # Convert dataframe to CSV for download
            csv_buffer = io.StringIO()
            report_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="Download Summarized Report as CSV",
                data=csv_data,
                file_name="Referral_Automation_Report.csv",
                mime="text/csv",
            )

        else:
            st.error("The uploaded file does not contain the required 'Other Lab Refer' column. Please check the file format.")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("👈 Please upload a data file from the sidebar to begin.")
