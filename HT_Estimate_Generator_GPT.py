import pandas as pd
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox

# ==============================================================================
# DATA PROCESSING LOGIC (Handles Excel I/O)
# Crated By Dhaval Chavda 
# 
# ==============================================================================

def load_file(path, is_receipt=False):
    """
    Helper function to load a file, prioritizing Excel (.xlsx/.xls) and 
    handling CSV as a fallback, returning None if an error occurs.
    """
    if not os.path.exists(path):
        return None

    skip_rows = 1 if is_receipt else None
    
    try:
        path_lower = path.lower()
        if path_lower.endswith(('.xlsx', '.xls')):
            # Read Excel files
            # Note: We assume data is in the first sheet. 
            df = pd.read_excel(path, skiprows=skip_rows, header=None if not is_receipt else 0)
        else:
            # Assume CSV if it's not Excel (This is kept for robust loading of messy files)
            df = pd.read_csv(path, skiprows=skip_rows, header=None if not is_receipt else 0, encoding='latin1')
            
        # Basic receipt header validation/correction (if skiprows=1 missed the header)
        if is_receipt and (df.columns[0] != 'Receipt' and 'Receipt' not in df.columns):
             # Try reloading without skipping rows to let pandas find the header naturally
             df = pd.read_excel(path) if path_lower.endswith(('.xlsx', '.xls')) else pd.read_csv(path, encoding='latin1')
             if 'Receipt' not in df.columns:
                 # If header is still missing, we assume the true header is the first data row (index 0)
                 df.columns = df.iloc[0].astype(str)
                 df = df[1:].reset_index(drop=True)


        if df is None or len(df) == 0:
            return None
            
        return df

    except Exception:
        return None


def run_update_process(receipt_path, report_path):
    """Core function to execute the data transfer and update the report."""
    
    # --- Load Data ---
    receipts_df = load_file(receipt_path, is_receipt=True)
    target_df = load_file(report_path, is_receipt=False)

    if receipts_df is None:
        return "❌ ERROR: Could not load Receipt Details file. Check file path/format."
    if target_df is None:
        return "❌ ERROR: Could not load September Report file. Check file path/format."
        
    # --- Report Header Mapping ---
    header_row_idx = 2
    headers = target_df.iloc[header_row_idx].astype(str).str.strip().tolist()
    
    try:
        col_map = {name: i for i, name in enumerate(headers) if pd.notna(name)}
        required_cols = ['Patient name', 'OPD', 'Total', 'Cash', 'Card', 'Online']
        if not all(col in col_map for col in required_cols):
             return "❌ ERROR: Report template headers (row 3) are incorrect or missing. Required: Patient name, OPD, Total, Cash, Card, Online."
    except Exception:
        return "❌ ERROR: Failed to map column headers in the report file."


    # --- Data Processing ---
    current_row = 4 # Start of data entry after 'Openning cash' row (index 3)
    
    for _, receipt in receipts_df.iterrows():
        if current_row >= len(target_df) or str(target_df.iloc[current_row, 0]).lower() == 'total':
            break
            
        # Find next empty row
        while current_row < len(target_df) and pd.notna(target_df.iloc[current_row, col_map['Patient name']]):
            current_row += 1
            
        p_name = receipt.get('Patient', '')
        amount = receipt.get('Amount', 0)
        mode = str(receipt.get('Payment Mode', '')).lower()
        
        try:
            amount = float(amount)
        except:
            amount = 0.0
            
        if not p_name or amount == 0.0:
            continue

        # --- Update columns based on user requirements ---
        target_df.iloc[current_row, col_map['Patient name']] = p_name
        target_df.iloc[current_row, col_map['OPD']] = amount
        target_df.iloc[current_row, col_map['Total']] = amount 

        # Payment Mode Allocation: Reset columns first
        target_df.iloc[current_row, col_map['Cash']] = np.nan
        target_df.iloc[current_row, col_map['Card']] = np.nan
        target_df.iloc[current_row, col_map['Online']] = np.nan
        
        if 'cash' in mode:
            target_df.iloc[current_row, col_map['Cash']] = amount
        elif 'card' in mode:
            target_df.iloc[current_row, col_map['Card']] = amount
        elif any(x in mode for x in ['online', 'google', 'paytm', 'upi', 'neft', 'rtgs']):
            target_df.iloc[current_row, col_map['Online']] = amount
        
        current_row += 1

    # --- Final Total Recalculation ---
    total_row_indices = target_df.index[target_df[0].astype(str).str.lower() == 'total'].tolist()
    if total_row_indices:
        total_idx = total_row_indices[0]
        cols_to_sum = ['OPD', 'Procedure', 'Medicine', 'Total', 'Cash', 'Card', 'Online']
        
        for col_name in cols_to_sum:
            if col_name in col_map:
                col_idx = col_map[col_name]
                subset = target_df.iloc[4:total_idx, col_idx]
                total_val = pd.to_numeric(subset, errors='coerce').fillna(0).sum()
                target_df.iloc[total_idx, col_idx] = total_val
        target_df.iloc[total_idx, 0] = 'Total'

    # --- Save Output to Excel (.xls or .xlsx) ---
    output_directory = os.path.dirname(report_path)
    report_ext = os.path.splitext(report_path)[1]
    
    base_name = os.path.splitext(os.path.basename(report_path))[0]
    output_filename = f"UPDATED_{base_name}{report_ext}"
    output_path = os.path.join(output_directory, output_filename)
    
    try:
        # Use to_excel for native Excel output
        target_df.to_excel(output_path, index=False, header=False)
        return f"✅ SUCCESS! Report updated and saved as: {output_filename}"
    except Exception as e:
         return f"❌ ERROR: Failed to save file as Excel. Ensure the target file is not open. Details: {e}"

# ==============================================================================
# TKINTER GUI SETUP
# ==============================================================================

class EODUpdaterApp:
    def __init__(self, master):
        self.master = master
        master.title("EOD Report Updater App (Excel Edition)")
        
        self.receipt_path = tk.StringVar()
        self.report_path = tk.StringVar()
        
        # --- File Path Entries ---
        
        tk.Label(master, text="1. Receipt Details File (.xlsx/.xls):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.receipt_entry = tk.Entry(master, textvariable=self.receipt_path, width=50)
        self.receipt_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(master, text="Browse", command=self.browse_receipt).grid(row=0, column=2, padx=5, pady=5)
        
        tk.Label(master, text="2. Daily Report Template (.xlsx/.xls):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.report_entry = tk.Entry(master, textvariable=self.report_path, width=50)
        self.report_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(master, text="Browse", command=self.browse_report).grid(row=1, column=2, padx=5, pady=5)
        
        # --- Run Button ---
        self.run_button = tk.Button(master, text="RUN UPDATE (Generate NEW Excel File)", command=self.run_update, bg='green', fg='white', font=('Arial', 10, 'bold'))
        self.run_button.grid(row=2, column=0, columnspan=3, pady=20)
        
        # --- Status Label ---
        self.status_label = tk.Label(master, text="Ready. Select files and click RUN.", fg='blue')
        self.status_label.grid(row=3, column=0, columnspan=3, pady=5)


    def browse_receipt(self):
        """Opens file dialog for Receipt Details file."""
        filename = filedialog.askopenfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if filename:
            self.receipt_path.set(filename)

    def browse_report(self):
        """Opens file dialog for Daily Report template."""
        filename = filedialog.askopenfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if filename:
            self.report_path.set(filename)

    def run_update(self):
        """Executes the main data processing logic."""
        
        receipt_file = self.receipt_path.get()
        report_file = self.report_path.get()
        
        if not receipt_file or not report_file:
            self.status_label.config(text="❌ ERROR: Please select both files.", fg='red')
            return

        self.status_label.config(text="Processing... Please wait...", fg='orange')
        self.master.update_idletasks()

        # Call the core processing logic
        result_message = run_update_process(receipt_file, report_file)
        
        # Update status based on result
        if result_message.startswith("✅ SUCCESS"):
            self.status_label.config(text=result_message, fg='green')
        else:
            self.status_label.config(text=result_message, fg='red')


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = EODUpdaterApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Initialization Error", f"Failed to start application. Ensure pandas and openpyxl are installed. Error: {e}")