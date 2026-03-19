import streamlit as st
import pandas as pd
import io

# App er title ar layout
st.set_page_config(page_title="Lab Referral Automation", layout="wide")
st.title("📊 Other Lab Referral Module - Automation")
st.write("Nicher chhok-e apnar raw excel file (unsolved) upload korun ar autometic solved result download korun.")

# File uploader (Jekhane user raw file upload korbe)
uploaded_file = st.file_uploader("Raw Excel File (.xlsx) upload korun", type=["xlsx"])

if uploaded_file is not None:
    try:
        # 1. Raw Data Load Kora
        df = pd.read_excel(uploaded_file, sheet_name='Sheet1')
        
        st.write("### Raw Data Preview:")
        st.dataframe(df.head()) # Upload kora data r kichu ongsho dekhabe
        
        with st.spinner('Data process hochhe... Ektu opekha korun...'):
            # 2. Data Cleaning
            if 'Other Lab Refer' in df.columns:
                df['Other Lab Refer'] = df['Other Lab Refer'].fillna('N.A.')
            
            # 3. Calculation Logic (Ei percentage gulo apnar dorkar moto change korte paren)
            df['Discount Allowed'] = 0 
            df['Balance Discount'] = 0.25 # 25% balance discount er jonno
            df['Net Payable'] = df['Net Amount'] * df['Balance Discount']
            
            # Other Lab Refer Payable er basic logic (Commission)
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

            # 5. Virtual Memory te Excel toiri kora (jate user direct download korte pare)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Calculation Sheet', index=False)
                pivot_option_1.to_excel(writer, sheet_name='Display (Option-1)', index=False)
                pivot_option_2.to_excel(writer, sheet_name='Display (Option-2)', index=False)
                pivot_option_3.to_excel(writer, sheet_name='Display (Option-3)', index=False)
            
            processed_data = output.getvalue()
            
        st.success("✅ File successfully solved hoye geche!")
        
        # 6. Download Button
        st.download_button(
            label="📥 Download Solved File",
            data=processed_data,
            file_name="Solved_Other_lab_Referral_Result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"Kono ekta somossa hoyeche, apnar data theek format e ache kina check korun. Error Details: {e}")
