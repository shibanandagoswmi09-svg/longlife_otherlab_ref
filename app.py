import streamlit as st
import pandas as pd
import io

# App er title ar layout
st.set_page_config(page_title="Lab Referral Report", layout="wide")
st.title("📊 Lab Referral Module - Final Report")
st.write("Niche raw file upload korun. Ekta sheet-ei apnar data ar commission amount toiri hoye jabe.")

# File uploader
uploaded_file = st.file_uploader("Raw Excel File (.xlsx) upload korun", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 1. Raw Data Load Kora (header=1 dewa holo jate 2nd row theke column name ney)
        df = pd.read_excel(uploaded_file, sheet_name='Sheet1', header=1)
        df.columns = df.columns.str.strip()
        
        with st.spinner('Report toiri hochhe...'):
            # 2. Data Cleaning
            if 'Other Lab Refer' in df.columns:
                df['Other Lab Refer'] = df['Other Lab Refer'].fillna('N.A.')
            else:
                st.error("❌ 'Other Lab Refer' column ti file e nei! Kono banan vul ache kina check korun.")
                st.stop()
            
            # 3. Calculation Logic (Original data-r sathe notun column jog hochhe)
            df['Discount Allowed'] = 0 
            df['Balance Discount'] = 0.25 
            df['Net Payable'] = df['Net Amount'] * df['Balance Discount']
            df['Other Lab Refer Payable'] = df.apply(lambda x: 0 if x['Other Lab Refer'] == 'N.A.' else (x['Net Amount'] * 0.10), axis=1)

        st.success("✅ Report successfully generate hoyeche!")

        # ---------------------------------------------------------
        # 4. SINGLE VIEW (Ektai Table Dekhabe)
        # ---------------------------------------------------------
        st.subheader("📋 Final Report (Full Data with Payable Amount)")
        st.dataframe(df, use_container_width=True)

        # ---------------------------------------------------------
        # 5. Download Button (Ektai Sheet thakbe Excel e)
        # ---------------------------------------------------------
        st.divider()
        st.write("Excel format e save korte chaile nicher button e click korun:")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Shudhu ektai sheet save hobe "Final Report" naame
            df.to_excel(writer, sheet_name='Final Report', index=False)
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 Download Excel Report",
            data=processed_data,
            file_name="Final_Report_Other_lab_Referral.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"Kono ekta somossa hoyeche. Error Details: {e}")
