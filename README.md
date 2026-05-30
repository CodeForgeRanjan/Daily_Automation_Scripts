# Multi-Utility Automation Pipeline Tool

A cloud-based automated system built using **Python (Streamlit & Pandas)** to optimize and completely eliminate manual operations in background  data pipelines. 

##  Key Features

### 1. Uber BGC Data CleanUp
- **Data Ingestion Alignment:** Maps and re-orders raw CSV inputs directly into system-compatible portal schemas.
- **Name & Address Sanitization:** Auto-strips system-breaking phrases (e.g., *Aadhar Address, DL-, Present Address, Agreement*) and applies standard title-casing.
- **Smart Pincode Regex Extraction:** Extracts 6-digit Pincodes even when fused directly with letters or words.
- **Automated Master Mapping (VLOOKUP):** Instantly merges master databases to update City Names and District System IDs.
- **Conditional Data Fallback:** Automatically replaces missing Pincodes and 'NA' Cities with system default **`8440`** to prevent ingestion failure.

### 2. Bulk Image to PDF Converter
- Accepts batch uploads of `.png`, `.jpg`, and `.jpeg`.
- Merges separate document/ID scans into a single compiled `.pdf` file.
- Handles transparent PNG backgrounds (RGBA to RGB conversion) automatically.

---

##  Tech Stack & Architecture
- **Frontend / UI:** Streamlit Web Framework
- **Data Processing Engine:** Python Pandas & NumPy
- **String Manipulation:** Advanced Regular Expressions (Regex)
- **Image Conversion Engine:** Pillow (PIL)

---

##  Local Setup and Deployment

### 1. Prerequisites
Ensure Python installed on your local machine.

### 2. Installation
Clone the repository and install the required tracking libraries:
```bash
pip install -r requirements.txt
