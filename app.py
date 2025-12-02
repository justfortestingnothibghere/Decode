#!/usr/bin/env python3
"""
Powerful XLSX Decoder & Multi-File Reader
Automatically reads .xlsx, .txt, .csv, and other files in the directory.
Generates clean output in read.txt with metadata.
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import glob

# Configuration
INPUT_DIR = Path(".")           # Current directory
OUTPUT_FILE = INPUT_DIR / "read.txt"
SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv', '.txt', '.tsv'}
IGNORE_FILES = {'read.txt'}     # Skip output file

def log(message: str):
    """Print with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def clean_value(val):
    """Clean and format cell values for text output"""
    if pd.isna(val):
        return "NULL"
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return str(val).strip()

def read_excel_file(filepath: Path) -> str:
    """Read all sheets from an Excel file and return formatted string"""
    log(f"Reading Excel: {filepath.name}")
    try:
        xls = pd.ExcelFile(filepath)
        content = f"\n=== EXCEL FILE: {filepath.name} ===\n"
        content += f"Sheets: {', '.join(xls.sheet_names)}\n"
        content += f"Modified: {datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 60 + "\n"

        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            content += f"\n[SHEET: {sheet_name}]  Shape: {df.shape}\n"
            content += "-" * 50 + "\n"

            # Column headers
            headers = " | ".join([f"{col[:20]:<20}" for col in df.columns])
            content += headers + "\n"
            content += "-" * len(headers) + "\n"

            # Limit to first 20 rows for readability
            for _, row in df.head(20).iterrows():
                row_str = " | ".join([f"{clean_value(v):<20}" for v in row])
                content += row_str + "\n"

            if len(df) > 20:
                content += f"... (and {len(df) - 20} more rows)\n"

            content += "\n"

        return content

    except Exception as e:
        return f"\n!!! ERROR reading {filepath.name}: {str(e)}\n"

def read_text_file(filepath: Path) -> str:
    """Read plain text files"""
    log(f"Reading Text: {filepath.name}")
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        preview = "".join(lines[:50])
        more = f"\n... (and {len(lines) - 50} more lines)" if len(lines) > 50 else ""
        return f"\n=== TEXT FILE: {filepath.name} ===\n{preview}{more}\n\n"
    except Exception as e:
        return f"\n!!! ERROR reading {filepath.name}: {str(e)}\n"

def read_csv_file(filepath: Path) -> str:
    """Read CSV/TSV files"""
    log(f"Reading CSV: {filepath.name}")
    try:
        sep = ',' if filepath.suffix == '.csv' else '\t'
        df = pd.read_csv(filepath, sep=sep, nrows=20, on_bad_lines='skip')
        content = f"\n=== CSV FILE: {filepath.name} ===\n"
        content += f"Rows previewed: {len(df)} (total may be more)\n"
        content += "-" * 50 + "\n"
        content += df.to_string(index=False, max_colwidth=20) + "\n\n"
        return content
    except Exception as e:
        return f"\n!!! ERROR reading {filepath.name}: {str(e)}\n"

def main():
    log("Starting file decoding process...")
    
    # Find all supported files
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(INPUT_DIR.glob(f"*{ext}"))
    
    # Filter out ignored files
    files = [f for f in files if f.name not in IGNORE_FILES and f.is_file()]
    
    if not files:
        log("No supported files found!")
        return

    log(f"Found {len(files)} file(s) to process.")

    output_content = []
    output_content.append(f"# AUTO-GENERATED DECODE REPORT")
    output_content.append(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_content.append(f"# Directory: {INPUT_DIR.resolve()}")
    output_content.append("=" * 80 + "\n")

    for file_path in sorted(files):
        if file_path.suffix in {'.xlsx', '.xls'}:
            output_content.append(read_excel_file(file_path))
        elif file_path.suffix in {'.csv', '.tsv'}:
            output_content.append(read_csv_file(file_path))
        elif file_path.suffix == '.txt':
            output_content.append(read_text_file(file_path))

    # Write to read.txt
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_content))
        log(f"Success! Output saved to: {OUTPUT_FILE}")
    except Exception as e:
        log(f"Failed to write output: {e}")

    # Optional: Print summary
    print("\n" + "="*60)
    print("DECODING COMPLETE")
    print(f"Processed {len(files)} file(s) → {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    # Auto-install pandas if missing
    try:
        import pandas as pd
    except ImportError:
        print("pandas not found. Installing...")
        os.system("pip install pandas openpyxl xlrd")
        import pandas as pd

    main()