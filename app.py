import streamlit as st
import pandas as pd
import io

# App er title ar layout
st.set_page_config(page_title="Lab Referral Report Dashboard", layout="wide")
st.title("📊 Lab Referral Module - Live Report")
st.write("Niche raw file upload korle report gulo ekhanei toiri hoye jabe.")

# File uploader
uploaded_file = st.file_uploader("Raw Excel File (.xlsx) upload korun", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 1. Raw Data Load Kora (header=1 dewa holo jate 2nd row theke column name ney)
        df = pd.read_excel(uploaded_file, sheet_name='Sheet1', header=1)
        
        # Column name er aage-piche kono space thakle seta muche felar jonno (Safety)
        df.columns = df.columns.str.strip()
        
        with st.spinner('Report toiri hochhe...'):
            # 2. Data Cleaning
            if 'Other Lab Refer' in df.columns:
                df['Other Lab Refer'] = df['Other Lab Refer'].fillna('N.A.')
            else:
                st.error("❌ 'Other Lab Refer' column ti file e nei! Kono banan vul ache kina check korun.")
                st.write("Apnar file e ei column gulo pawa geche:", df.columns.tolist()) # Error hole theek column naam gulo dekhabe
                st.stop()
            
            # 3. Calculation Logic 
            df['Discount Allowed'] = 0 
            df['Balance Discount'] = 0.25 
            df['Net Payable'] = df['Net Amount'] * df['Balance Discount']
            df['Other Lab Refer Payable'] = df.apply(lambda x: 0 if x['Other Lab Refer'] == 'N.A.' else (x['Net Amount'] * 0.10), axis=1)

            # 4. Display Options (Pivot Tables Toiri Kora)
            pivot_option_1 = pd.pivot_table(df, 
                                            index=['Other Lab Refer'], 
                                            values=['Gross Amount', 'Discount', 'Net Amount', 'Other Lab Refer Payable'], 
                                            aggfunc='sum').reset_index()

            pivot_option_2 = pd.pivot_table(df, 
                                            index=['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name'], 
                                            values=['Gross Amount', 'Discount', 'Net Amount', 'Other Lab Refer Payable'], 
                                            aggfunc='sum').reset_index()

            pivot_option_3 = pd.pivot_table(df, 
                                            index=['Other Lab Refer', 'DATE', 'Work Order ID', 'Pt. Name', 'Investigation Name'], 
                                            values=['Gross Amount', 'Discount', 'Net Amount', 'Other Lab Refer Payable'], 
                                            aggfunc='sum').reset_index()

        st.success("✅ Report successfully generate hoyeche! Nicher tab gulo theke data dekhun.")

        # ---------------------------------------------------------
        # 5. DASHBOARD VIEW (TABS TOIRI KORA)
        # ---------------------------------------------------------
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Option-1 (Summary)", 
            "📅 Option-2 (Date & Patient)", 
            "🔬 Option-3 (Investigation)", 
            "⚙️ Calculation Sheet (Full Data)"
        ])

        with tab1:
            st.subheader("Lab Refer Summary")
            st.dataframe(pivot_option_1, use_container_width=True)

        with tab2:
            st.subheader("Patient & Date wise Report")
            st.dataframe(pivot_option_2, use_container_width=True)

        with tab3:
            st.subheader("Detailed Investigation Report")
            st.dataframe(pivot_option_3, use_container_width=True)

        with tab4:
            st.subheader("Full Data with Calculations")
            st.dataframe(df, use_container_width=True)

        # ---------------------------------------------------------
        # 6. Optional Download Button
        # ---------------------------------------------------------
        st.divider()
        st.write("Jodi Excel format e save korte chan:")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Calculation Sheet', index=False)
            pivot_option_1.to_excel(writer, sheet_name='Display (Option-1)', index=False)
            pivot_option_2.to_excel(writer, sheet_name='Display (Option-2)', index=False)
            pivot_option_3.to_excel(writer, sheet_name='Display (Option-3)', index=False)
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 Download Excel Report",
            data=processed_data,
            file_name="Live_Report_Other_lab_Referral.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"Kono ekta somossa hoyeche. Error Details: {e}")
