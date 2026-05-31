import streamlit as st
import pandas as pd
import re
import io
from PIL import Image

# Page Setup & Styling
st.set_page_config(page_title="Multi-Utility Automation Tool", page_icon="🚗", layout="wide")

# Custom CSS for Professional UI Design
st.markdown("""
    <style>
    .main-title {
        font-size: 36px;
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
        font-size: 38px;
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
        "CORRESPONDENCE ADDRESS", "CORRESPONDENCE", "PERMANENT:", ":", "-", ";", "#"
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

    # --- CLEAR BUTTON  ---
    # if uber_file is not None or master_file is not None:
    #     st.markdown("---")
    #     if st.button("Clear Dashboard & Reset Files", use_container_width=True):
    #         st.cache_data.clear()
    #         st.rerun()

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

                final['Priority'] = ""

                #  Pin Code Fallback 
                missing_mask = (final['City'] == 'NA') & ((final['Pin_Code'] == '') | (final['Pin_Code'].isna()))
                final.loc[missing_mask, 'City'] = '8440'

                # Remove illegal characters from final structure
                final = final.map(remove_illegal_chars)

            st.success("Process Completed Successfully!")
            
            # Show live preview of processed data
            st.subheader("Preview of Processed Output (Top 5 Rows)")
            st.dataframe(final.head(5))

            # setup for CSV stable download
            csv_buffer = io.StringIO()
            final.to_csv(csv_buffer, index=False)
            csv_output = csv_buffer.getvalue()
            
            # Stable Download 
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

# ================= PAGE 2: IMAGE & DOCS CONVERTED =================
elif page == "Image Converted":
    st.markdown('<p class="main-title">PDF Converter Hub </p>', unsafe_allow_html=True)
    st.write("Convert single images, merge multiple images, or transform Word files (.docx) into professional PDFs.")

    # Three different core types to process other tasks
    tab1, tab2, tab3 = st.tabs(["Single Image to PDF", "Bulk Merge to One PDF", "Word Docs to PDF"])

    # ----------------- TAB 1: SINGLE IMAGE TO SINGLE PDF -----------------
    with tab1:
        st.subheader("Convert Individual Images to Separate PDFs")
        single_images = st.file_uploader("Upload Images (Each file will be created as a separate PDF.)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="single_key")
        
        if single_images:
            st.info(f"Total {len(single_images)} images uploaded.")
            for idx, uploaded_img in enumerate(single_images):
                try:
                    # BytesIO will handle corrupted file crashes
                    img_data = io.BytesIO(uploaded_img.read())
                    img = Image.open(img_data)
                    img = img.convert('RGB')
                    
                    pdf_buffer = io.BytesIO()
                    img.save(pdf_buffer, format="PDF")
                    pdf_bytes = pdf_buffer.getvalue()
                    
                    # Each file has its own download button    
                    st.download_button(
                        label=f"Download PDF: {uploaded_img.name}.pdf",
                        data=pdf_bytes,
                        file_name=f"{uploaded_img.name.split('.')[0]}.pdf",
                        mime="application/pdf",
                        key=f"btn_single_{idx}"
                    )
                except Exception as e:
                    st.error(f"File {uploaded_img.name} convert nahi ho payi: {e}")

    # ----------------- TAB 2: MULTIPLE IMAGES TO ONE MERGE PDF -----------------
    with tab2:
        st.subheader("Compile Multiple Images into a Single Candidate PDF Report")
        bulk_images = st.file_uploader("Upload Multiple Images (All are merged into single pdf)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="bulk_key")
        
        if bulk_images:
            st.success(f"Total {len(bulk_images)} images uploaded for merging.")
            if st.button("⚙️ Merge All Images into 1 PDF", key="merge_btn"):
                try:
                    with st.spinner("Compiling all images..."):
                        img_list = []
                        for uploaded_img in bulk_images:
                            img_data = io.BytesIO(uploaded_img.read())
                            img = Image.open(img_data)
                            img = img.convert('RGB')
                            img_list.append(img)
                        
                        if img_list:
                            pdf_buffer = io.BytesIO()
                            img_list[0].save(pdf_buffer, format="PDF", save_all=True, append_images=img_list[1:])
                            pdf_data = pdf_buffer.getvalue()
                            
                            st.success("Multi-page Candidate PDF Compiled!")
                            st.download_button(
                                label="Download Compiled Candidate PDF",
                                data=pdf_data,
                                file_name="Candidate_Merged_Report.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                except Exception as e:
                    st.error(f"Merge failed: {e}. Return a corrupted image file.")

    # ----------------- TAB 3: WORD DOCS TO PDF (CLOUD FRIENDLY) -----------------
    with tab3:
        st.subheader("Direct Word Document (.docx) to PDF Converter")
        word_files = st.file_uploader("Upload Word Documents (.docx)", type=["docx"], accept_multiple_files=True, key="word_key")
        
        if word_files:
            from docx import Document
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            st.info(f"Total {len(word_files)} Word document(s) uploaded.")
            
            for idx, doc_file in enumerate(word_files):
                if st.button(f"Convert {doc_file.name} to PDF", key=f"word_btn_{idx}"):
                    try:
                        with st.spinner("Converting Document..."):
                            # Read DOCX text
                            doc = Document(doc_file)
                            pdf_buffer = io.BytesIO()
                            
                            # ReportLab Setup to build PDF dynamically on Cloud
                            doc_template = SimpleDocTemplate(pdf_buffer, pagesize=letter)
                            styles = getSampleStyleSheet()
                            story = []
                            
                            for para in doc.paragraphs:
                                if para.text.strip():
                                    # Normal clean body text conversion
                                    p = Paragraph(para.text, styles['Normal'])
                                    story.append(p)
                                    story.append(Spacer(1, 10))
                            
                            if not story:
                                story.append(Paragraph("Empty Document Text", styles['Normal']))
                                
                            doc_template.build(story)
                            pdf_bytes = pdf_buffer.getvalue()
                            
                            st.success(f"{doc_file.name} converted successfully!")
                            st.download_button(
                                label=f"Download PDF from {doc_file.name}",
                                data=pdf_bytes,
                                file_name=f"{doc_file.name.split('.')[0]}.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Docx conversion failed: {e}")
                        
# PLACEHOLDERS FOR FUTURE WORK 
elif page == "msg conversion":
    st.markdown('<p class="main-title">Message Conversion Dashboard</p>', unsafe_allow_html=True)
    st.info("Work in progress...This route will be used for message formatting and log conversion.")

elif page == "ARS Check updation":
    st.markdown('<p class="main-title"> ARS Check Updation</p>', unsafe_allow_html=True)
    st.info("Work in progress... This route is a placeholder for the background verification portal automation.")




elif page == "About Tool":
    st.markdown('<p class="main-title"> About Automation Utility Tool</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ###  Overview
    This central automation hub replaces slow, manual Excel workflows and legacy VBA macros with high-speed, secure **Python Streamlit & Pandas cloud pipelines**.
    It is custom-built to optimize day-to-day background verification (BGV) and data processing pipelines.

    ---

    ###  Key Modules & Features

    #### 1.  Uber Data CleanUp Dashboard
    - **Exact Portal Schema Mapping:** Columns are dynamically structured and ordered to match system ingestion layouts precisely.
    - **Advanced Text Sanitization:** Automatically strips illegal non-printable characters, fixes punctuation, and applies proper Title Case to candidate and father names.
    - **Address Deep-Cleaning:** Uses regular expressions (Regex) to purge junk strings like *"Aadhar Address:"*, *"Rent Agreement:"*, *"DL"*, and *":"* from applicant files.
    - **Smart Regex PIN Extraction:** Isolates 6-digit postal codes instantly, even when compressed inside stuck text blocks (e.g., *Coimbatore641006*).
    - **Automated Pincode VLOOKUP:** Performs an optimized memory merge against your Master Pincode file to auto-populate City names and Flow City IDs.
    - **Smart Fallback Engine:** Automatically detects rows where both Pincode is missing and City is mapped as 'NA', over-writing them with the system fallback code **`8440`**.

    #### 2.  Image to PDF Converter
    - **Multi-File Batch Processing:** Upload multiple formats (`.png`, `.jpg`, `.jpeg`) concurrently.
    - **Single-File Compilation:** Automatically flattens and groups separate document scans into a single, clean, and chronologically compiled PDF report.
    - **RGBA Transparency Fix:** Built-in Pillow conversion handles alpha-channels and transparent images seamlessly to prevent engine crashes.

    #### 3.  Future Pipeline Modules
    - **msg conversion & ARS Check updation:** Dedicated pipelines currently reserved as placeholders for downstream integration of communication logs and portals mapping.
    """)
