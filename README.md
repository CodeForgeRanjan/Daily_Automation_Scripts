# 🚗 Multi-Utility Automation Pipeline Tool

A high-performance, secure automation hub built using **Python (Streamlit & Pandas)** designed to eliminate manual data-entry bottlenecks and optimize (BGV) operations.

---

## 🛠️ Key Core Modules

### 📈 1. Bridge Workload Allocator (Smart Queue Distribution)
This module automates the manual dispatching of cases among team members, ensuring strict adherence to SLA timelines.
- **⚡ Dynamic File Ingestion:** Auto-detects and parses raw input streams seamlessly from both `.csv` (handling broken lines/tab fallbacks) and `.xlsx` structures.
- **🧹 Duplicate Clean-Up Layer:** Automatically scans the incoming queue, flags repetitive records, and retains exactly **1 unique case** per applicant to prevent double allocation.
- **🚫 Restricted Series Filtering:** Instantly detects and purges restricted case sequences (e.g., blocking rows starting with **`2304` series**) based on operational compliance rules.
- **⏳ SLA-First Smart Sorting:** Automatically converts ageing indicators or hour matrices into numeric formats and sorts the entire queue in **Descending Order** (highest ageing hours first) to secure urgent cases.
- **👥 Multi-Slot Workload Balancing:** Distributes rows dynamically into customized slices based on user-defined slot names and case limits.
- **📊 Dual-Sheet Tracker Output:** Generates a professional, production-ready `.xlsx` file using `openpyxl` with two distinct sheets:
  1. `Allocation_List`: Clean mapping of *Allocated User Name* and *No*.
  2. `Allocation_Tracker`: Live operational summary showing exact *Case Counts* per user.

### 🧹 2. BGC Data CleanUp Dashboard
- **Data Ingestion Alignment:** Maps and re-orders raw data rows directly into target portal schemas.
- **Name & Address Sanitization:** Auto-purges system-breaking phrases (e.g., *Aadhar Address, DL-, Present Address, Agreement*) using intelligent regex, applying standard Proper Title Case.
- **Smart Pincode Regex Extraction:** Isolates 6-digit postal codes instantly, even when compressed inside stuck text frames.
- **Automated Master Mapping:** Performs an in-memory VLOOKUP merge against the Master Database to auto-populate City Names and District System IDs.
- **Conditional Data Fallback:** Automatically replaces missing references with the system default fallback code **`8440`** to guarantee 100% ingestion success.

### 📄 3. Bulk Image to PDF Converter Hub
- **Multi-File Batch Processing:** Accepts parallel uploads of `.png`, `.jpg`, `.jpeg`, and `.docx` files.
- **🔄 Smart Auto-Orientation (EXIF Fix):** Detects if a document scan is flipped upside down or sideways and automatically restores it to an upright portrait position.
- **📐 Standardized A4 Layout Scaling:** Automatically scales skewed document images into a clean, uniform A4 profile using advanced LANCZOS resampling.
- **📦 One-Click ZIP Archiving:** Compiles standalone file transforms in background memory and packs them into a single downloadable `.zip` package.

---

## 🏗️ Tech Stack & Architecture

* **🖥️ UI / Frontend Framework:** `Streamlit` (Interactive Web Architecture)
* **⚙️ Core Engine:** `Python Pandas` & `NumPy` (Vectorized Data Manipulation)
* **🗄️ Excel Automation:** `OpenPyXL` (Multi-Sheet Matrix Formatting)
* **🔍 String Pattern Engine:** `Advanced Regular Expressions (Regex)`
* **🖼️ Image Processing:** `Pillow (PIL)` & `ImageOps` (EXIF Alignment & A4 Resampling)

---

## 🌐 Local Setup & Zero-Dependency Deployment

### 🛡️ Core Infrastructure Strategy
This application is architected under a Local-First / Offline-First Server Model (http://localhost:8501). By executing data processing workflows entirely within the local machine's volatile memory (RAM) and local CPU, the tool eliminates external network dependency. This Client-Side execution design guarantees zero data exposure, ensures strict compliance with corporate Data Loss Prevention (DLP) frameworks, and guarantees high-speed data processing without relying on external cloud endpoints.

### 1. Requirements
Ensure Python is installed on your local machine.

### 2. Installation
Clone this repository to your local directory and install the necessary dependencies:

```bash
py -m pip install streamlit pandas openpyxl rapidfuzz pillow python-docx reportlab extract_msg
