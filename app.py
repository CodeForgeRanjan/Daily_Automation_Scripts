import streamlit as st
import pandas as pd
import re
import io
from PIL import Image
from rapidfuzz import process, utils # Fast Fuzzy matching

# Page Setup & Styling
st.set_page_config(page_title="Multi-Utility Automation Tool", page_icon="🚗", layout="wide")

# Custom CSS for Professional UI Design
st.markdown("""
    <style>
    .main-title {
        font-size: 40px;
        font-weight: bold;
        color: #111111;
        text-align: center;
        padding: 10px;
        background: linear-gradient(90deg, #F9D423 0%, #FF4E50 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
        border-bottom: 3px solid #FF4E50;
        border-radius: 5px;
    }
    .sidebar-heading {
        font-size: 24px;
        font-weight: bold;
        color: #00ffff;
        margin-bottom: 20px;
        text-shadow: 0px 0px 10px rgba(0,255,255,0.5);
    }
    .section-header{
        font-size: 20px;
        font-weight: 600;
        color: #F9D423;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# CLEANING FUNCTIONS
def clean_text_proper(text):
    if pd.isna(text) or str(text).strip() == "": 
        return ""
    cleaned = re.sub(r'[-+%,]', '', str(text)).strip()
    return cleaned.title()

def clean_address(text):
    if pd.isna(text) or str(text).strip() == "": 
        return ""
    
    text = "".join(ch for ch in str(text).strip() if ch.isprintable())


    # --- NEW ADVANCED HYPERLINK / DRIVE LINK REMOVAL LAYER ---
    # 1. Kisi bhi tarah ki Google Drive, http, https, ya www wali link ko completely saaf karo
    # Yeh pattern handle karega: http://..., https://..., www...., aur bina protocol ke drive.google.com...
    url_pattern = r'(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)|(www\.[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)|(drive\.google\.com\/[^\s]*)'
    text = re.sub(url_pattern, '', text, flags=re.IGNORECASE)
    
    # 2. Agar link ke aage "Drive link", "Link:", "URL" jaisa text bacha reh jaye, use bhi hatao
    text = re.sub(r'\b(?:drive\s*link|link|url)[:.-]?\s*_*', '', text, flags=re.IGNORECASE)
    # ---------------------------------------------------------

    # --- NEW ADVANCED MOBILE NUMBER REMOVAL LAYER ---
    # 1. Pehle agar address me 10-digit ka lagatar number hai (ya beech me space/dash hai), use saaf karo
    # Yeh pattern handle karega: 9876543210, 98765-43210, 98765 43210
    text = re.sub(r'\b\d{5}[-\s]?\d{5}\b', '', text)
    
    # 2. Agar mobile number ke sath text bhi likha ho (E.g. Mobile: 9876543210 ya Mob No- 9876543210)
    unwanted_mobile_patterns = [
        r'mobile\s*no(?:umber)?[:.-]?\s*\d*',
        r'mob(?:ile)?[:.-]?\s*\d*',
        r'ph(?:one)?\s*no(?:umber)?[:.-]?\s*\d*'
    ]
    for pattern in unwanted_mobile_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    
    unwanted = [
        "Aadhar Address", "address", "Rent agreement Address", "agreement Address", 
        "AGREEMENT", "Aadhar", "AADHAR", "Aadhaar", "AADHAAR",
        "DL-", "CARD", "card", "Adhar-", "Adhar No.", "DL", "Driving License", 
        "Driving Licence", "Driving Lic", "ADD","Driving Lc", "Licence", "License", 
        "Address", "Permanent Address", "Present Address", 
        "CORRESPONDENCE ADDRESS", "CORRESPONDENCE", "PERMANENT:", ":", "-", ";", "#","mobile","Mobile","mobileno","mobile_no."
    ]
    for word in unwanted:
        text = re.sub(word, '', text, flags=re.IGNORECASE)
        
    return text.title().strip()

def extract_pin(text):
    if pd.isna(text) or str(text).strip() == "": 
        return ""
    
    # 1. Pure address se saare 6-digit ke numbers ki list nikaalo
    all_matches = re.findall(r'\d{6}', str(text))
    
    # 2. Agar matches mile, toh hamesha sabse LAST wala (index -1) pick karo
    return all_matches[-1] if all_matches else ""

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

# --- FUZZY MATCHING HELPER ENGINE ---
def find_closest_city_id(detected_district, master_unique_df):
    """Sari unique districts list me se string comparison karke closest match ki ID layega"""
    if not detected_district or detected_district == "NA":
        return "NA"
    
    # Master file ke unique district choices uthana
    master_districts = master_unique_df['DISTRICT'].dropna().astype(str).tolist()
    
    # RapidFuzz engine se top closest string match dhundhna
    match_result = process.extractOne(
        detected_district, 
        master_districts, 
        processor=utils.default_process,
        score_cutoff=70.0 # 70% se zyada similarity hone par hi accept karega
    )
    if match_result:
        matched_name = match_result[0]
        # Us matched district ka corresponding Row filter karke ID nikalna
        matched_row = master_unique_df[master_unique_df['DISTRICT'].astype(str) == matched_name]
        if not matched_row.empty:
            return format_id(matched_row.iloc[0]['City ID/District ID'])
            
    return "NA"


#  SIDEBAR NAVIGATION 
st.sidebar.markdown('<p class="sidebar-heading">Navigation Menu</p>', unsafe_allow_html=True)
page = st.sidebar.radio("Go to:", ["Data Upload", "Image And Docs Converted", "MSG Conversion", "ARS Check Updation" ,"I bridge Allocation","About Tool"])


if page == "Data Upload":
    st.markdown('<p class="main-title">Data CleanUp Dashboard</p>', unsafe_allow_html=True)
    st.write("Upload your raw CSV file and Pincode Master file to instantly generate clean data.")

    # Empty State Guide 
    st.info("Welcome! Please upload both required files below to trigger the automated data cleaning pipeline.")

    col1, col2 = st.columns(2)
    
    # with col1:
    #     st.subheader("1. Uber Raw Data")
    #     uber_file = st.file_uploader("Upload Uber CSV File", type=["csv"], key="uber_file")

    with col1:
        st.markdown('<p class="section-header">Raw Data Input</p>', unsafe_allow_html=True)
        my_file = st.file_uploader("Upload CSV File", type=["csv"], key="my_file", label_visibility="collapsed")

    with col2:
        st.markdown('<p class="section-header">Pincode Master Database</p>', unsafe_allow_html=True)
        master_file = st.file_uploader("Upload Pincode Master File", type=["xlsx", "xls"], key="master_file", label_visibility="collapsed")

    if my_file is not None and master_file is not None:
        # Clear button layout with custom style
        st.markdown("---")
        if st.button("Reset System & Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        try:
            with st.spinner("Processing your data smart Fuzzy Matching... Please wait..."):
                # Load Files
                df = pd.read_csv(my_file, encoding="latin1")
                master_df = pd.read_excel(master_file, sheet_name='Sheet1')
                master_df.columns = master_df.columns.str.strip()

                # APPLY CLEANING 
                df['Candidate Name'] = df.iloc[:, 1].apply(clean_text_proper)
                df['Father Name'] = df.iloc[:, 2].apply(clean_text_proper)
                df['Cleaned_Address'] = df.iloc[:, 4].apply(clean_address)
                df['PIN_Extracted'] = df['Cleaned_Address'].apply(extract_pin)

                # Name Split logic
                df[['First', 'Middle', 'Last']] = df['Candidate Name'].apply(lambda x: pd.Series(split_name(x)))

                # MAPPING & VLOOKUP 
                df['PIN_Extracted'] = df['PIN_Extracted'].astype(str).str.strip()
                master_df['PIN CODE'] = master_df['PIN CODE'].astype(str).str.strip()
                master_unique = master_df.drop_duplicates(subset=['PIN CODE'])

                df = df.merge(
                    master_unique[['PIN CODE', 'DISTRICT', 'City ID/District ID']], 
                    left_on='PIN_Extracted', right_on='PIN CODE', how='left'
                )

                # EXACT FINAL OUTPUT STRUCTURE 
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

                
                # --- NEW SMART INTELLIGENT FUZZY RE-CORRECTION LAYER ---
                fuzzy_counter = 0
                # Unique Master references file array targeting
                master_district_unique = master_df.drop_duplicates(subset=['DISTRICT'])
                
                for idx, row in final.iterrows():
                    # Agar pincode missing ya unmapped tha jisse City ID 'NA' ho gayi
                    if row['City'] == 'NA' or row['City'] == '':
                        # Address field se text nikal kar closest match dekhna
                        address_str = str(row['Complete_Address'])
                        
                        # Master unique directory se check karna
                        for m_dist in master_district_unique['DISTRICT'].dropna().astype(str):
                            if m_dist.lower() in address_str.lower():
                                # Direct string keyword match hit ho gaya!
                                matched_row = master_district_unique[master_district_unique['DISTRICT'] == m_dist]
                                final.at[idx, 'City'] = format_id(matched_row.iloc[0]['City ID/District ID'])
                                fuzzy_counter += 1
                                break
                            

                final['Priority'] = ""

                #  Pin Code Fallback 
                # missing_mask = (final['City'] == 'NA') & ((final['Pin_Code'] == '') | (final['Pin_Code'].isna()))
                # final.loc[missing_mask, 'City'] = '8440'

                # Pin Code Fallback Logic
                missing_mask = (final['City'] == 'NA') & ((final['Pin_Code'] == '') | (final['Pin_Code'].isna()))
                fallback_count = missing_mask.sum()
                final.loc[missing_mask, 'City'] = '8440'

                # Remove illegal characters from final structure
                final = final.map(remove_illegal_chars)

            st.success("Process Completed Successfully! All Data Compiled.")

            # Live Metric Cards
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.metric(label="Total Input Records", value=f"{len(final)} rows")
            with m_col2:
                mapped_pins = final['Pin_Code'].transform(lambda x: 1 if x != '' else 0).sum()
                st.metric(label="Extracted Pincodes", value=f"{mapped_pins} items")
            with m_col3:
                st.metric(label="Fallback Swaps (8440)", value=f"{fallback_count} rows")

# Show live preview of processed data
            st.markdown('<p class="section-header">Live Processed Preview (Top 5 Rows)</p>', unsafe_allow_html=True)
            st.dataframe(final.head(5), use_container_width=True)
    
            # # Show live preview of processed data
            # st.subheader("Preview of Processed Output (Top 5 Rows)")
            # st.dataframe(final.head(5))

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
            
    elif my_file is not None and master_file is None:
        st.info(" Please upload the Pincode Master file to process automatic City & City ID mapping.")

#  IMAGE & DOCS CONVERTED (ZIP + AUTO-ROTATE ENABLED) 
elif page == "Image And Docs Converted":
    import zipfile  # Create a Zip folder for inbuilt module
    from PIL import ImageOps  # Automate rotation images
    
    st.markdown('<p class="main-title">Document & Image to PDF Converter Hub</p>', unsafe_allow_html=True)
    st.write("Convert single images with auto-rotation, merge multiple images, or bulk-transform Word files into PDFs with a single 'Download All' Zip option.")

    tab1, tab2, tab3 = st.tabs(["Single Image to PDF", "Bulk Merge to One PDF", "Word Docs to PDF"])

    #  SINGLE IMAGE TO SINGLE PDF (WITH ZIP & AUTO-ROTATE) 
    with tab1:
        st.subheader("Convert Individual Images to Separate PDFs")
        single_images = st.file_uploader("Upload Images (Individual Conversion)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="single_key")
        
        # if single_images:
        #     st.info(f"Total {len(single_images)} image(s) uploaded.")

        if single_images:
            st.success(f"Total {len(single_images)} image(s) uploaded successfully.")
            
            # If there is only 1 image then show normal download button
            if len(single_images) == 1:
                try:
                    uploaded_img = single_images[0]
                    img_data = io.BytesIO(uploaded_img.read())
                    img = Image.open(img_data)
                    
                    # Auto-Orientation 
                    img = ImageOps.exif_transpose(img)
                    img = img.convert('RGB')
                    
                    # Resolution correction to Standard A4 Layout (Vertical / Portrait)
                    img.thumbnail((1240, 1754), Image.Resampling.LANCZOS)
                    
                    pdf_buffer = io.BytesIO()
                    img.save(pdf_buffer, format="PDF")
                    pdf_bytes = pdf_buffer.getvalue()
                    
                    st.download_button(
                        label=f"Download PDF: {uploaded_img.name}.pdf",
                        data=pdf_bytes,
                        file_name=f"{uploaded_img.name.split('.')[0]}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
                    
            # Show "Download All" zip button if there are more than 1 images
            else:
                if st.button("Process All Images & Create Zip", key="process_img_zip"):
                    try:
                        with st.spinner("Fixing resolution, orientation and creating Zip..."):
                            zip_buffer = io.BytesIO()
                            
                            # Create a Zip folder in memory
                            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                                for idx, uploaded_img in enumerate(single_images):
                                    img_data = io.BytesIO(uploaded_img.read())
                                    img = Image.open(img_data)
                                    
                                    # Auto-rotate fix for flipped dimensions (E.g. 1166x1600 rotation)
                                    img = ImageOps.exif_transpose(img)
                                    img = img.convert('RGB')
                                    img.thumbnail((1240, 1754), Image.Resampling.LANCZOS)
                                    
                                    pdf_buffer = io.BytesIO()
                                    img.save(pdf_buffer, format="PDF")
                                    
                                    # Put files inside the zip
                                    clean_name = f"{uploaded_img.name.split('.')[0]}.pdf"
                                    zip_file.writestr(clean_name, pdf_buffer.getvalue())
                                    
                            st.success("All Images Converted successfully!")
                            st.download_button(
                                label="Download All PDFs in One Click (ZIP)",
                                data=zip_buffer.getvalue(),
                                file_name="All_Images_PDFs.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Zip Creation Failed: {e}")
                        
    # MULTIPLE IMAGES TO ONE MERGE PDF 
    with tab2:
        st.subheader("Compile Multiple Images into a Single Candidate PDF Report")
        bulk_images = st.file_uploader("Upload Multiple Images (All will be merged into a single PDF)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="bulk_key")
        
        if bulk_images:
            st.success(f"Total {len(bulk_images)} images uploaded for merging.")
            if st.button("Merge All Images into 1 PDF", key="merge_btn"):
                try:
                    with st.spinner("Compiling all images with auto-rotation check..."):
                        img_list = []
                        for uploaded_img in bulk_images:
                            img_data = io.BytesIO(uploaded_img.read())
                            img = Image.open(img_data)
                            # Rotation and resolution check for merge list
                            img = ImageOps.exif_transpose(img)
                            img = img.convert('RGB')
                            img.thumbnail((1240, 1754), Image.Resampling.LANCZOS)
                            img_list.append(img)
                        
                        if img_list:
                            pdf_buffer = io.BytesIO()
                            img_list[0].save(pdf_buffer, format="PDF", save_all=True, append_images=img_list[1:])
                            pdf_data = pdf_buffer.getvalue()
                            
                            st.success("Multi-page PDF Compiled!")
                            st.download_button(
                                label="Download Compiled PDF",
                                data=pdf_data,
                                file_name="Bulk_Merged_file.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                except Exception as e:
                    st.error(f"Merge failed: {e}")

  #  UNIVERSAL WORD DOCS TO PDF (EXACT MIRROR COPY) 
    with tab3:
        st.markdown('<p class="section-header">Direct Word Document (.docx) to PDF Bulk Converter</p>', unsafe_allow_html=True)
        word_files = st.file_uploader("Upload Word Documents (.docx)", type=["docx"], accept_multiple_files=True, key="word_key")
        
        if word_files:
            from docx import Document
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
            from reportlab.lib import colors
            
            st.success(f"{len(word_files)} docx file(s) staged for universal format conversion.")
            
            # DYNAMIC UNIVERSAL CONVERSION ENGINE 
            def universal_docx_to_pdf_story(doc, styles):
                story = []
                align_map = {0: TA_LEFT, 1: TA_CENTER, 2: TA_RIGHT, 3: TA_JUSTIFY}
                normal_style = styles['Normal']
                
                # Function that removes inner formatting of text (Bold, Italic, Underline, Checkbox)
                def get_clean_html_text(para):
                    text_html = ""
                    for run in para.runs:
                        text = run.text
                        if not text:
                            continue
                        # XML characters escape logic to prevent crashes
                        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        # Universal checkbox character rendering
                        text = text.replace('☐', '<font name="Helvetica" size="11">&#9633;</font>')
                        
                        if run.bold:
                            text = f"<b>{text}</b>"
                        if run.italic:
                            text = f"<i>{text}</i>"
                        if run.underline:
                            text = f"<u>{text}</u>"
                        text_html += text
                    return text_html

                body_elements = doc.element.body
                element_index = 0
                
                for child in body_elements:
                    # 1. PARAGRAPH PROCESSING (Universal Rules)
                    if child.tag.endswith('p'):
                        from docx.text.paragraph import Paragraph as DocxParagraph
                        para = DocxParagraph(child, doc)
                        raw_text = para.text.strip()
                        
                        if not raw_text:
                            story.append(Spacer(1, 6))
                            continue
                        
                        # if there are large tabs/spaces between text (compatible with every client)
                        if "\t" in para.text or "   " in para.text:
                            parts = [p.strip() for p in re.split(r'\t+|\s{3,}', para.text) if p.strip()]
                            if len(parts) >= 2:
                                key_text = parts[0]
                                value_text = " ".join(parts[1:])
                                
                                k_style = ParagraphStyle(name=f'UniK_{element_index}', parent=normal_style, fontSize=9.5, leading=13, fontName="Helvetica-Bold")
                                v_style = ParagraphStyle(name=f'UniV_{element_index}', parent=normal_style, fontSize=9.5, leading=13)
                                
                                row_data = [[Paragraph(key_text, k_style), Paragraph(value_text, v_style)]]
                                kv_table = Table(row_data, colWidths=[180, 324])
                                kv_table.setStyle(TableStyle([
                                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                    ('TOPPADDING', (0,0), (-1,-1), 3),
                                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                                    ('LEFTPADDING', (0,0), (-1,-1), 0),
                                    ('RIGHTPADDING', (0,0), (-1,-1), 0),
                                ]))
                                story.append(kv_table)
                                element_index += 1
                                continue

                        text_html = get_clean_html_text(para)
                        p_align = align_map.get(para.alignment, TA_LEFT) if para.alignment is not None else TA_LEFT
                        
                        # It will dynamically scale according to the size/style selected by the user in the Word file.
                        p_style = ParagraphStyle(
                            name=f'UniversalPara_{element_index}',
                            parent=normal_style,
                            alignment=p_align,
                            fontSize=9.5,
                            leading=14,
                            spaceBefore=4,
                            spaceAfter=4
                        )
                        
                        story.append(Paragraph(text_html, p_style))
                        element_index += 1
                        
                    # UNIVERSAL TABLE/GRID PROCESSING
                    elif child.tag.endswith('tbl'):
                        from docx.table import Table as DocxTable
                        docx_table = DocxTable(child, doc)
                        
                        table_data = []
                        for row in docx_table.rows:
                            row_data = []
                            for cell in row.cells:
                                cell_html = ""
                                for p in cell.paragraphs:
                                    cell_html += get_clean_html_text(p)
                                
                                cell_style = ParagraphStyle(
                                    name=f'UniCell_{element_index}_{len(row_data)}',
                                    parent=normal_style,
                                    fontSize=9,
                                    leading=12
                                )
                                row_data.append(Paragraph(cell_html, cell_style))
                            table_data.append(row_data)
                        
                        if table_data:
                            num_cols = len(table_data[0])
                            # Auto-adjust column width based on columns count (Standard for any client table)
                            col_widths = [504 / num_cols] * num_cols
                            
                            pdf_table = Table(table_data, colWidths=col_widths, repeatRows=1)
                            pdf_table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F9FAFB')), # clean header
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('TOPPADDING', (0, 0), (-1, -1), 5),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')), # Standard corporate borders
                            ]))
                            story.append(Spacer(1, 6))
                            story.append(pdf_table)
                            story.append(Spacer(1, 6))
                        element_index += 1
                        
                return story

            # Single Word Document Execution
            if len(word_files) == 1:
                doc_file = word_files[0]
                if st.button(f"Convert & Process {doc_file.name}", key="single_word_btn", use_container_width=True):
                    try:
                        doc = Document(doc_file)
                        pdf_buffer = io.BytesIO()
                        doc_template = SimpleDocTemplate(
                            pdf_buffer, 
                            pagesize=letter,
                            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
                        )
                        styles = getSampleStyleSheet()
                        story = universal_docx_to_pdf_story(doc, styles)
                        doc_template.build(story)
                        
                        st.success("Document converted with universal layout styling!")
                        st.download_button(
                            label="Download Converted PDF",
                            data=pdf_buffer.getvalue(),
                            file_name=f"{doc_file.name.split('.')[0]}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Conversion Error: {e}")
            
            # Bulk Processing Archiver (Multiple Files with ZIP)
            else:
                if st.button("Bulk Convert All Docs & Archive to ZIP", key="bulk_word_zip_btn", use_container_width=True):
                    try:
                        with st.spinner("Processing documents map to ZIP..."):
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                                for idx, doc_file in enumerate(word_files):
                                    doc = Document(doc_file)
                                    pdf_buffer = io.BytesIO()
                                    doc_template = SimpleDocTemplate(
                                        pdf_buffer, 
                                        pagesize=letter,
                                        rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
                                    )
                                    styles = getSampleStyleSheet()
                                    story = universal_docx_to_pdf_story(doc, styles)
                                    doc_template.build(story)
                                    
                                    clean_name = f"{doc_file.name.split('.')[0]}.pdf"
                                    zip_file.writestr(clean_name, pdf_buffer.getvalue())
                                    
                            st.success("Bulk documents universally packed into ZIP!")
                            st.download_button(
                                label="Download Processed PDF Package (ZIP)",
                                data=zip_buffer.getvalue(),
                                file_name="All_Word_PDFs.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Bulk engine failure: {e}")

# PLACEHOLDERS FOR FUTURE WORK 
# elif page == "MSG Conversion":
    # st.markdown('<p class="main-title">Message Conversion Dashboard</p>', unsafe_allow_html=True)
    # st.info("Work in progress...This route will be used for message formatting and log conversion.")
# ----------------- PAGE: MSG CONVERSION TO PDF SUITE -----------------
    elif page =="MSG Conversion":
        import extract_msg
        import zipfile
        from email.message import EmailMessage
        from email.utils import formatdate
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        st.markdown('<p class="main-title">Premium MSG & EML Automation </p>', unsafe_allow_html=True)
        st.write("Upload Outlook .msg files to instantly unpack text structures, map attachments, and download complete compiled PDF bundles.")

        uploaded_msg = st.file_uploader("Upload Outlook Email Document (.msg)", type=["msg"], key="msg_file_uploader")

        if uploaded_msg is not None:
            try:
                # --- STEP 1: CONVERT MSG TO EML IN MEMORY ---
                with st.spinner("Decoding Outlook MSG binary data streams..."):
                    msg = extract_msg.Message(uploaded_msg)
                    
                    # Create EML Structure
                    email_msg = EmailMessage()
                    email_msg["From"] = msg.sender or "Unknown Sender"
                    email_msg["To"] = msg.to or "Unknown Receiver"
                    email_msg["Subject"] = msg.subject or "No Subject"
                    email_msg["Date"] = formatdate(localtime=True)
                    email_msg.set_content(msg.body or "")
                    
                    eml_bytes = email_msg.as_bytes()
                    base_name = uploaded_msg.name.split('.')[0]
                
                # Instant Flash Popup for EML Conversion Success
                st.toast(f"🎉 EML Conversion Successful for: {base_name}", icon="🚀")
                st.success("✨ Outlook Message file compiled to EML standards successfully!")

                # Provide direct intermediate EML download option if required
                st.download_button(
                    label="📥 Download Converted EML File",
                    data=eml_bytes,
                    file_name=f"{base_name}.eml",
                    mime="message/rfc822",
                    use_container_width=True
                )

                st.markdown("---")
                st.markdown('<p class="section-header">📁 Attachment Inventory & Metadata Tracker</p>', unsafe_allow_html=True)

                # --- STEP 2: SCAN AND INVENTORY ATTACHMENTS ---
                valid_attachments = []
                if msg.attachments:
                    for att in msg.attachments:
                        f_name = att.longFilename or att.shortFilename
                        if f_name:
                            # Split name and check extension compatibility
                            ext = f_name.split('.')[-1].lower() if '.' in f_name else ''
                            if ext in ['pdf', 'docx']:
                                valid_attachments.append({"name": f_name, "type": ext.upper(), "raw_data": att.data})

                # Display Attachment Metrics UI Grid
                if valid_attachments:
                    st.info(f"🔍 Found total {len(valid_attachments)} actionable document attachment(s) inside this email.")
                    
                    # Create a clean DataFrame Grid to show user what files exist
                    att_df = pd.DataFrame(valid_attachments)[["name", "type"]]
                    att_df.columns = ["File Name", "Document Type"]
                    st.dataframe(att_df, use_container_width=True)
                else:
                    st.warning("⚠️ No valid structural document attachments (.pdf/.docx) detected inside this email structure.")

                st.markdown("---")
                
                # --- STEP 3: CONVERT EMAIL BODY & ATTACHMENTS TO PDF BUNDLE ---
                if st.button("⚙️ Compile Full Email Package (Body + All Attachments) to PDF ZIP", use_container_width=True):
                    with st.spinner("Executing dynamic PDF rendering algorithms... Please wait..."):
                        zip_buffer = io.BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            # A. Convert Email Body Text to PDF
                            body_pdf_buffer = io.BytesIO()
                            doc_template = SimpleDocTemplate(body_pdf_buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
                            styles = getSampleStyleSheet()
                            
                            story = []
                            # Email Metadata Header Block
                            story.append(Paragraph(f"<b>From:</b> {email_msg['From']}", styles['Normal']))
                            story.append(Paragraph(f"<b>To:</b> {email_msg['To']}", styles['Normal']))
                            story.append(Paragraph(f"<b>Subject:</b> {email_msg['Subject']}", styles['Normal']))
                            story.append(Paragraph(f"<b>Date:</b> {email_msg['Date']}", styles['Normal']))
                            story.append(Spacer(1, 15))
                            story.append(Paragraph("<b>--- EMAIL BODY TEXT ---</b>", styles['Normal']))
                            story.append(Spacer(1, 10))
                            
                            # Clean and break email lines safely
                            email_body_raw = msg.body or ""
                            for line in email_body_raw.split('\n'):
                                clean_line = line.strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                if clean_line:
                                    story.append(Paragraph(clean_line, styles['Normal']))
                                else:
                                    story.append(Spacer(1, 6))
                                    
                            doc_template.build(story)
                            zip_file.writestr("Email_Body_Text.pdf", body_pdf_buffer.getvalue())

                            # B. Process and convert all attachments to PDF structure
                            for att_node in valid_attachments:
                                file_name = att_node['name']
                                file_ext = att_node['type'].lower()
                                binary_data = att_node['raw_data']
                                
                                # Case I: Attachment is already a PDF (Direct bypass to zip)
                                if file_ext == 'pdf':
                                    zip_file.writestr(file_name, binary_data)
                                    
                                # Case II: Attachment is a Word Document (Universal .docx to PDF execution)
                                elif file_ext == 'docx':
                                    from docx import Document
                                    word_stream = io.BytesIO(binary_data)
                                    doc_obj = Document(word_stream)
                                    
                                    word_pdf_buffer = io.BytesIO()
                                    word_template = SimpleDocTemplate(word_pdf_buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
                                    word_story = []
                                    
                                    for para in doc_obj.paragraphs:
                                        text_html = ""
                                        for run in para.runs:
                                            text = run.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                            if run.bold: text = f"<b>{text}</b>"
                                            if run.italic: text = f"<i>{text}</i>"
                                            if run.underline: text = f"<u>{text}</u>"
                                            text_html += text
                                            
                                        if text_html.strip():
                                            p_style = ParagraphStyle(name=f"AttPara_{file_name}", parent=styles['Normal'], fontSize=9.5, leading=14)
                                            word_story.append(Paragraph(text_html, p_style))
                                        else:
                                            word_story.append(Spacer(1, 6))
                                            
                                    word_template.build(word_story)
                                    clean_pdf_name = f"{file_name.split('.')[0]}.pdf"
                                    zip_file.writestr(clean_pdf_name, word_pdf_buffer.getvalue())

                        # Trigger Success Layout
                        st.success("🎉 Full Package Compiled! Email body and all document templates packed securely.")
                        st.download_button(
                            label="📥 Download Complete Converted PDF Package (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=f"{base_name}_Full_PDF_Package.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

            except Exception as e:
                st.error(f"Pipeline Conversion Failed: {e}")

elif page == "ARS Check Updation":
    st.markdown('<p class="main-title"> ARS Check Updation</p>', unsafe_allow_html=True)
    st.info("Work in progress... This route is a placeholder for the background verification portal automation.")

elif page == "I bridge Allocation":
    st.markdown('<p class="main-title"> I bridge Allocation</p>', unsafe_allow_html=True)
    st.info("Work in progress....")


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

    #### 2. Image And Docs Converted Hub
    - **Multi-File Batch Processing:** Upload multiple formats (`.png`, `.jpg`, `.jpeg`, `.docx`) concurrently.
    - **Smart Auto-Orientation (EXIF Fix):** Automatically detects if an uploaded document scan is flipped upside down or sideways (e.g., rotated dimensions like 1166x1600) and auto-rotates it back to an upright portrait position.
    - **Standardized A4 Resolution Scaling:** Resizes skewed image sizes to a clean, uniform A4 layout using advanced LANCZOS resampling to prevent text stretching.
    - **Bulk Merge to One PDF:** Flattens and groups multiple images into a single multi-page compiled PDF report for a candidate.
    - **One-Click Bulk ZIP Archiving:** Processes bulk standalone conversions in background memory and packs them into a single downloadable `.zip` file, saving manual click time.
    - **Cloud-Friendly Word Docs to PDF Converter:** Uses a hybrid parsing engine (`python-docx` & `ReportLab`) to dynamically read Word files and render them as high-quality PDFs on the fly without needing external system tools.

    #### 3. Future Pipeline Modules
    - **MSG Conversion & ARS Check Updation:** Dedicated pipelines currently reserved as placeholders for downstream integration of communication logs and automated portal verification mappings.
    """)
    
