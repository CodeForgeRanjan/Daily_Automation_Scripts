import streamlit as st
import pandas as pd
import re
import io

# Page Setup & Styling
st.set_page_config(page_title="Uber Data CleanUp Tool", page_icon="🚗", layout="wide")

# Custom CSS for Professional UI Design
st.markdown("""
    <style>
    .main-title {
        font-size: 44px;
        font-weight: bold;
        color: #111111;
        text-align: center;
        padding: 10px;
        background: linear-gradient(90deg, #F9D423 0%, #FF4E50 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
        border-bottom: 3px solid #FF4E50;
    }
    .sidebar-heading {
        font-size: 22px;
        font-weight: bold;
        color: #00ffff;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- CLEANING FUNCTIONS -----------------
def clean_text_proper(text):
    if pd.isna(text) or str(text).strip() == "": 
        return ""
    cleaned = re.sub(r'[-+%,]', '', str(text)).strip()
    return cleaned.title()

def clean_address(text):
    if pd.isna(text) or str(text).strip() == "": 
        return ""
    
    text = "".join(ch for ch in str(text).strip() if ch.isprintable())
    
    unwanted = [
        "Aadhar Address", "address", "Rent agreement Address", "agreement Address", 
        "AGREEMENT", "Aadhar", "AADHAR", "Aadhaar", "AADHAAR",
        "DL-", "CARD", "card", "Adhar-", "Adhar No.", "DL", "Driving License", 
        "Driving Licence", "Driving Lic", "ADD","Driving Lc", "Licence", "License", 
        "Address", "Permanent Address", "Present Address", 
        "CORRESPONDENCE ADDRESS", "CORRESPONDENCE", "PERMANENT:", ":"
    ]
    for word in unwanted:
        text = re.sub(word, '', text, flags=re.IGNORECASE)
        
    return text.title().strip()

def extract_pin(text):
    if pd.isna(text): 
        return ""
    match = re.search(r'\d{6}', str(text))
    return match.group(0) if match else ""

def split_name(name):
    parts = str(name).split()
    if len(parts) == 1: return parts[0], "", ""
    if len(parts) == 2: return parts[0], "", parts[1]
    return parts[0], " ".join(parts[1:-1]), parts[-1]

def format_id(val):
    try:
        if pd.isna(val) or str(val).strip() == "" or str(val).lower() == 'nan':
            return "NA"
        return str(int(float(val)))
    except: 
        return "NA"

def format_dob(val):
    try:
        if pd.isna(val) or str(val).strip() == "": 
            return ""
        return pd.to_datetime(val).strftime('%Y-%m-%d')
    except: 
        return str(val).replace('/', '-') 

def remove_illegal_chars(val):
    if pd.isna(val): 
        return ""
    return "".join(ch for ch in str(val) if ch.isprintable())

# ----------------- SIDEBAR NAVIGATION -----------------
st.sidebar.markdown('<p class="sidebar-heading">🚗 Navigation Menu</p>', unsafe_allow_html=True)
page = st.sidebar.radio("Go to:", ["Uber Data Upload", "Image Converted", "msg conversion", "ARS Check updation" ,"About Tool"])

if page == "Uber Data Upload":
    st.markdown('<p class="main-title">Uber Data CleanUp Dashboard</p>', unsafe_allow_html=True)
    st.write("Upload your raw Uber CSV file and Pincode Master file to instantly generate clean data.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Uber Raw Data")
        uber_file = st.file_uploader("Upload Uber CSV File", type=["csv"], key="uber_file")
        
    with col2:
        st.subheader("2. Pincode Master Data")
        master_file = st.file_uploader("Upload Pincode Master File", type=["xlsx", "xls"], key="master_file")

    if uber_file is not None and master_file is not None:
        try:
            with st.spinner("Processing your data... Please wait..."):
                # Load Files
                df = pd.read_csv(uber_file, encoding="latin1")
                master_df = pd.read_excel(master_file, sheet_name='Sheet1')
                master_df.columns = master_df.columns.str.strip()

                # --- APPLY CLEANING ---
                df['Candidate Name'] = df.iloc[:, 1].apply(clean_text_proper)
                df['Father Name'] = df.iloc[:, 2].apply(clean_text_proper)
                df['Cleaned_Address'] = df.iloc[:, 4].apply(clean_address)
                df['PIN_Extracted'] = df['Cleaned_Address'].apply(extract_pin)

                # Name Split logic
                df[['First', 'Middle', 'Last']] = df['Candidate Name'].apply(lambda x: pd.Series(split_name(x)))

                # --- MAPPING & VLOOKUP ---
                df['PIN_Extracted'] = df['PIN_Extracted'].astype(str).str.strip()
                master_df['PIN CODE'] = master_df['PIN CODE'].astype(str).str.strip()
                master_unique = master_df.drop_duplicates(subset=['PIN CODE'])

                df = df.merge(
                    master_unique[['PIN CODE', 'DISTRICT', 'City ID/District ID']], 
                    left_on='PIN_Extracted', right_on='PIN CODE', how='left'
                )

                # --- EXACT FINAL OUTPUT STRUCTURE ---
                final = pd.DataFrame()
                final['First_Name'] = df['First']
                final['Middle_Name'] = df['Middle']
                final['Last_Name'] = df['Last']
                final['Father_Name'] = df['Father Name']
                final['Mobile_No'] = ""
                final['DOB'] = df.iloc[:, 3].apply(format_dob)
                final['Location'] = "496380"
                final['Case_Insuff'] = ""
                final['Case_Comment'] = ""
                final['Car_No'] = "NOT MENTIONED"
                final['DL_NO'] = "NOT MENTIONED"
                final['Product'] = "NOT MENTIONED"
                final['UUID'] = df.iloc[:, 0]
                final['Special_ID'] = "FT_FORM"
                final['Channel'] = "OFFLINE"
                final['Permanent_Insufficiency'] = ""
                final['Name'] = ""
                final['Type'] = ""
                final['Complete_Address'] = df['Cleaned_Address']
                final['Pin_Code'] = df['PIN_Extracted']
                final['Insuff'] = ""
                final['City'] = df['DISTRICT'].fillna('NA')
                
                if 'City ID/District ID' in df.columns:
                    final['City'] = df['City ID/District ID'].apply(format_id)
                else:
                    final['City'] = "NA"
                    
                # final['Priority'] = ""

                final['Priority'] = ""

                # --- NEW LOGIC: Missing City & Pin Fallback to 8440 ---
                # Agar City == 'NA' hai aur Pin_Code khali hai, toh City ko '8440' set karein
                missing_mask = (final['City'] == 'NA') & ((final['Pin_Code'] == '') | (final['Pin_Code'].isna()))
                final.loc[missing_mask, 'City'] = '8440'

                # Remove illegal characters from final structure
                final = final.map(remove_illegal_chars)

                # Remove illegal characters from final structure
                final = final.map(remove_illegal_chars)

            st.success("Process Completed Successfully!")
            
            # Show live preview of processed data
            st.subheader("Preview of Processed Output (Top 5 Rows)")
            st.dataframe(final.head(5))

            # Memory string buffer setup for CSV stable download
            csv_buffer = io.StringIO()
            final.to_csv(csv_buffer, index=False)
            csv_output = csv_buffer.getvalue()
            
            # Stable Download Button for CSV Output
            st.download_button(
                label=" Download Processed CSV File",
                data=csv_output,
                file_name="Uber csv (1).csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"error encountered during setup: {e}")
            
    elif uber_file is not None and master_file is None:
        st.info(" Please upload the Pincode Master file to process automatic City & City ID mapping.")

elif page == "About Tool":
    st.markdown('<p class="main-title">About Uber Cleanup Automation</p>', unsafe_allow_html=True)
    st.write("""
        This tool replaces the older Excel VBA Macros approach with a modern, fast, and secure Python Pandas workflow.
        - **Exact Portal Schema:** Columns are strictly mapped according to system requirements.
        - **Data Cleaning:** Removes unwanted keywords like labels, types, and formatting anomalies.
        - **Smart Regex:** Captures 6-digit Pincodes even if they are merged directly into text (e.g., Coimbatore641006).
        - **Automated VLOOKUP:** Automatically matches pincodes with district databases to output clear City Names and system ID codes.
    """)
