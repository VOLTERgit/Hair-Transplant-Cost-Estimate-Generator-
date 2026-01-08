# Hair_Transplant_Estimate_Generator_Enhanced.py
# Zeeva Clinic - Hair Transplant Estimate Generator
# Enhanced version with editable prices and custom notes

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Flowable, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os
import sys
import csv
from pathlib import Path

class HeaderWithLogo(Flowable):
    def __init__(self, logo_path, width, height):
        Flowable.__init__(self)
        self.logo_path = logo_path
        self.width = width
        self.height = height

    def draw(self):
        self.canv.setFont("Helvetica-Bold", 16)
        self.canv.drawCentredString(self.width / 2, self.height - 30, "Hair Transplant Estimate")
        
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo_size = 60
                logo_x = self.width - logo_size - 10
                logo_y = self.height - logo_size - 5
                self.canv.drawImage(self.logo_path, logo_x, logo_y, width=logo_size, height=logo_size,
                                    preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

class HairTransplantEstimateGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Zeeva Estimate (Compact)")
        self.root.geometry("560x720")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Normal.TLabel', font=('Arial', 10))
        style.configure('Bold.TLabel', font=('Arial', 10, 'bold'))

        self.logo_path = self.get_default_logo()
        self.create_widgets()

    def get_default_logo(self):
        try:
            if getattr(sys, 'frozen', False):
                base = Path(sys.executable).parent
            else:
                base = Path(__file__).parent
        except Exception:
            base = Path.cwd()

        for name in ['default_logo.png', 'logo.png', 'company_logo.png', 'zeeva_logo.png',
                     'default_logo.jpg', 'logo.jpg', 'company_logo.jpg']:
            p = base / name
            if p.exists():
                return str(p)
        return None

    def create_widgets(self):
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        main_frame = ttk.Frame(scrollable_frame, padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        row = 0
        
        # Date and Logo at top
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 8))
        
        date_label = ttk.Label(top_frame, text="Date:", style='Normal.TLabel')
        date_label.grid(row=0, column=0, padx=(0,5))
        self.date_day = ttk.Entry(top_frame, width=4)
        self.date_day.insert(0, "DD")
        self.date_day.grid(row=0, column=1)
        self.date_month = ttk.Entry(top_frame, width=4)
        self.date_month.insert(0, "MM")
        self.date_month.grid(row=0, column=2)
        self.date_year = ttk.Entry(top_frame, width=6)
        self.date_year.insert(0, "YYYY")
        self.date_year.grid(row=0, column=3)
        ttk.Button(top_frame, text="Today", command=self.set_today, width=8).grid(row=0, column=4, padx=(5,0))
        
        ttk.Button(top_frame, text="Select Logo", command=self.select_logo).grid(row=0, column=5, padx=(20,0))
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=8)
        row += 1

        # Patient Details Section
        ttk.Label(main_frame, text="Patient Details", style='Bold.TLabel', foreground='blue').grid(
            row=row, column=0, columnspan=4, sticky=tk.W, pady=(0,6))
        row += 1

        # Name, Age, Sex in one row
        detail_frame = ttk.Frame(main_frame)
        detail_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=3)
        ttk.Label(detail_frame, text="Name:", style='Normal.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.name_entry = ttk.Entry(detail_frame, width=28)
        self.name_entry.grid(row=0, column=1, padx=(5,15))
        ttk.Label(detail_frame, text="Age:", style='Normal.TLabel').grid(row=0, column=2, padx=(0,5))
        self.age_entry = ttk.Entry(detail_frame, width=6)
        self.age_entry.grid(row=0, column=3)
        ttk.Label(detail_frame, text="Sex:", style='Normal.TLabel').grid(row=0, column=4, padx=(8,5))
        self.sex_entry = ttk.Entry(detail_frame, width=6)
        self.sex_entry.grid(row=0, column=5)
        row += 1

        # Contact
        contact_frame = ttk.Frame(main_frame)
        contact_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=3)
        ttk.Label(contact_frame, text="Contact:", style='Normal.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.contact_entry = ttk.Entry(contact_frame, width=45)
        self.contact_entry.grid(row=0, column=1, padx=(5,0), sticky=tk.W)
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=8)
        row += 1

        # Tech and Duration
        tech_frame = ttk.Frame(main_frame)
        tech_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=3)
        ttk.Label(tech_frame, text="Tech:", style='Normal.TLabel').grid(row=0, column=0)
        self.technology_var = tk.StringVar(value="DHI")
        ttk.Combobox(tech_frame, textvariable=self.technology_var, values=["DHI", "FUE", "FUT"], 
                    width=12, state='readonly').grid(row=0, column=1, padx=(5,20))
        ttk.Label(tech_frame, text="Duration:", style='Normal.TLabel').grid(row=0, column=2)
        self.duration_entry = ttk.Entry(tech_frame, width=12)
        self.duration_entry.insert(0, "Day 1")
        self.duration_entry.grid(row=0, column=3, padx=(5,0))
        row += 1

        # Scalp Procedure
        scalp_frame = ttk.Frame(main_frame)
        scalp_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=3)
        self.scalp_enable = tk.BooleanVar(value=False)
        ttk.Checkbutton(scalp_frame, text="Scalp (Rs.60)", variable=self.scalp_enable, 
                       command=self.toggle_scalp).grid(row=0, column=0, sticky=tk.W)
        self.scalp_min = ttk.Entry(scalp_frame, width=8, state='disabled')
        self.scalp_min.grid(row=0, column=1, padx=(5,2))
        ttk.Label(scalp_frame, text="-").grid(row=0, column=2)
        self.scalp_max = ttk.Entry(scalp_frame, width=8, state='disabled')
        self.scalp_max.grid(row=0, column=3, padx=(2,5))
        ttk.Label(scalp_frame, text="@").grid(row=0, column=4, padx=2)
        self.scalp_price = ttk.Entry(scalp_frame, width=6, state='disabled')
        self.scalp_price.insert(0, "60")
        self.scalp_price.grid(row=0, column=5)
        row += 1

        # Beard Procedure
        beard_frame = ttk.Frame(main_frame)
        beard_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=3)
        self.beard_enable = tk.BooleanVar(value=False)
        ttk.Checkbutton(beard_frame, text="Beard (Rs.70)", variable=self.beard_enable, 
                       command=self.toggle_beard).grid(row=0, column=0, sticky=tk.W)
        self.beard_min = ttk.Entry(beard_frame, width=8, state='disabled')
        self.beard_min.grid(row=0, column=1, padx=(5,2))
        ttk.Label(beard_frame, text="-").grid(row=0, column=2)
        self.beard_max = ttk.Entry(beard_frame, width=8, state='disabled')
        self.beard_max.grid(row=0, column=3, padx=(2,5))
        ttk.Label(beard_frame, text="@").grid(row=0, column=4, padx=2)
        self.beard_price = ttk.Entry(beard_frame, width=6, state='disabled')
        self.beard_price.insert(0, "70")
        self.beard_price.grid(row=0, column=5)
        row += 1

        # Calculate button
        ttk.Button(main_frame, text="Calculate", command=self.calculate_charges, width=15).grid(
            row=row, column=0, columnspan=4, pady=8)
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=8)
        row += 1

        # Inclusions Section
        ttk.Label(main_frame, text="Inclusions (Yes/No)", style='Bold.TLabel', foreground='blue').grid(
            row=row, column=0, columnspan=4, sticky=tk.W, pady=(0,6))
        row += 1

        # Surgery
        incl_frame1 = ttk.Frame(main_frame)
        incl_frame1.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(incl_frame1, text="Surgery", width=20).grid(row=0, column=0, sticky=tk.W)
        self.surgery_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame1, textvariable=self.surgery_var, values=["Yes", "No"], 
                    width=8, state='readonly').grid(row=0, column=1, sticky=tk.W)
        ttk.Label(incl_frame1, text="Medicines during s..", width=20).grid(row=0, column=2, padx=(15,0), sticky=tk.W)
        self.medicines_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame1, textvariable=self.medicines_var, values=["Yes", "No"], 
                    width=8, state='readonly').grid(row=0, column=3, sticky=tk.W)
        row += 1

        # Lunch
        incl_frame2 = ttk.Frame(main_frame)
        incl_frame2.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(incl_frame2, text="Lunch + Beverages", width=20).grid(row=0, column=0, sticky=tk.W)
        self.lunch_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame2, textvariable=self.lunch_var, values=["Yes", "No"], 
                    width=8, state='readonly').grid(row=0, column=1, sticky=tk.W)
        ttk.Label(incl_frame2, text="Dressing & head wa..", width=20).grid(row=0, column=2, padx=(15,0), sticky=tk.W)
        self.dressing_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame2, textvariable=self.dressing_var, values=["Yes", "No"], 
                    width=8, state='readonly').grid(row=0, column=3, sticky=tk.W)
        row += 1

        # Follow up
        incl_frame3 = ttk.Frame(main_frame)
        incl_frame3.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(incl_frame3, text="One year follow up", width=20).grid(row=0, column=0, sticky=tk.W)
        self.followup_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame3, textvariable=self.followup_var, values=["Yes", "No"], 
                    width=8, state='readonly').grid(row=0, column=1, sticky=tk.W)
        ttk.Label(incl_frame3, text="GST @ 5%", width=20).grid(row=0, column=2, padx=(15,0), sticky=tk.W)
        self.gst_var = tk.StringVar(value="")
        ttk.Combobox(incl_frame3, textvariable=self.gst_var, values=["", "Yes", "No"], 
                    width=8, state='readonly').grid(row=0, column=3, sticky=tk.W)
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=8)
        row += 1

        # Anaesthetic
        anaes_frame = ttk.Frame(main_frame)
        anaes_frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(anaes_frame, text="Anaesthetic Charges Rs:", style='Normal.TLabel').grid(row=0, column=0, sticky=tk.W)
        self.anaesthetic = ttk.Entry(anaes_frame, width=12)
        self.anaesthetic.insert(0, "0")
        self.anaesthetic.grid(row=0, column=1, padx=(5,15))
        ttk.Label(anaes_frame, text="Unit:", style='Normal.TLabel').grid(row=0, column=2)
        self.unit_var = tk.StringVar(value="Per Day")
        ttk.Combobox(anaes_frame, textvariable=self.unit_var, values=["Per Day", "One Time", "Per Hour"], 
                    width=12, state='readonly').grid(row=0, column=3, padx=(5,0))
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=8)
        row += 1

        # Custom Notes
        ttk.Label(main_frame, text="Custom Notes (Optional):", style='Normal.TLabel').grid(
            row=row, column=0, columnspan=4, sticky=tk.W, pady=(0,4))
        row += 1

        self.custom_notes = scrolledtext.ScrolledText(main_frame, width=62, height=3, wrap=tk.WORD, font=('Arial', 9))
        self.custom_notes.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0,8))
        self.custom_notes.insert('1.0', 'Special offer, payment terms, etc.')
        self.custom_notes.bind('<FocusIn>', self.clear_placeholder)
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=8)
        row += 1

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=8)
        ttk.Button(btn_frame, text="GENERATE PDF", command=self.generate_pdf, width=18).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Reset", command=self.clear_fields, width=12).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="View CSV", command=self.open_csv, width=12).grid(row=0, column=2, padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def open_csv(self):
        """Open the CSV file"""
        csv_file = "Data_of_HT_Estimate_Generator.csv"
        if os.path.isfile(csv_file):
            try:
                if sys.platform.startswith('win'):
                    os.startfile(csv_file)
                elif sys.platform == 'darwin':
                    os.system(f'open "{csv_file}"')
                else:
                    os.system(f'xdg-open "{csv_file}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open CSV file: {e}")
        else:
            messagebox.showinfo("No Data", "No CSV file found. Generate a PDF first to create the data file.")

    def clear_placeholder(self, event):
        current_text = self.custom_notes.get('1.0', 'end-1c')
        if current_text == 'Special offer, payment terms, etc.':
            self.custom_notes.delete('1.0', tk.END)

    def toggle_scalp(self):
        state = 'normal' if self.scalp_enable.get() else 'disabled'
        self.scalp_min.config(state=state)
        self.scalp_max.config(state=state)
        self.scalp_price.config(state=state)
        if not self.scalp_enable.get():
            self.scalp_min.delete(0, tk.END)
            self.scalp_max.delete(0, tk.END)
            self.scalp_total.config(text="Rs. 0 - Rs. 0")

    def toggle_beard(self):
        state = 'normal' if self.beard_enable.get() else 'disabled'
        self.beard_min.config(state=state)
        self.beard_max.config(state=state)
        self.beard_price.config(state=state)
        if not self.beard_enable.get():
            self.beard_min.delete(0, tk.END)
            self.beard_max.delete(0, tk.END)
            self.beard_total.config(text="Rs. 0 - Rs. 0")

    def calculate_charges(self):
        if self.scalp_enable.get():
            try:
                smin = int(self.scalp_min.get())
                smax = int(self.scalp_max.get())
                sprice_str = self.scalp_price.get().strip()
                if not sprice_str:
                    messagebox.showerror("Error", "Scalp price cannot be empty")
                    return
                sprice = float(sprice_str)
                if sprice <= 0:
                    messagebox.showerror("Error", "Scalp price must be greater than 0")
                    return
                self.scalp_total.config(text=f"Rs. {int(smin*sprice):,} - Rs. {int(smax*sprice):,}")
            except ValueError:
                messagebox.showerror("Error", "Invalid Scalp values. Please enter valid numbers.")
                return
        
        if self.beard_enable.get():
            try:
                bmin = int(self.beard_min.get())
                bmax = int(self.beard_max.get())
                bprice_str = self.beard_price.get().strip()
                if not bprice_str:
                    messagebox.showerror("Error", "Beard price cannot be empty")
                    return
                bprice = float(bprice_str)
                if bprice <= 0:
                    messagebox.showerror("Error", "Beard price must be greater than 0")
                    return
                self.beard_total.config(text=f"Rs. {int(bmin*bprice):,} - Rs. {int(bmax*bprice):,}")
            except ValueError:
                messagebox.showerror("Error", "Invalid Beard values. Please enter valid numbers.")
                return

    def select_logo(self):
        f = filedialog.askopenfilename(title="Select Logo", 
                                      filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All", "*.*")])
        if f:
            self.logo_path = f
            messagebox.showinfo("Logo Selected", f"Logo updated: {os.path.basename(f)}")

    def set_today(self):
        t = datetime.now()
        self.date_day.delete(0, tk.END); self.date_day.insert(0, t.strftime("%d"))
        self.date_month.delete(0, tk.END); self.date_month.insert(0, t.strftime("%m"))
        self.date_year.delete(0, tk.END); self.date_year.insert(0, t.strftime("%Y"))

    def clear_fields(self):
        self.name_entry.delete(0, tk.END)
        self.age_entry.delete(0, tk.END)
        self.sex_entry.delete(0, tk.END)
        self.contact_entry.delete(0, tk.END)
        self.technology_var.set("DHI")
        self.duration_entry.delete(0, tk.END); self.duration_entry.insert(0, "Day 1")
        self.scalp_enable.set(False); self.toggle_scalp()
        self.scalp_price.delete(0, tk.END); self.scalp_price.insert(0, "60")
        self.beard_enable.set(False); self.toggle_beard()
        self.beard_price.delete(0, tk.END); self.beard_price.insert(0, "70")
        self.anaesthetic.delete(0, tk.END); self.anaesthetic.insert(0, "0")
        self.date_day.delete(0, tk.END); self.date_day.insert(0, "DD")
        self.date_month.delete(0, tk.END); self.date_month.insert(0, "MM")
        self.date_year.delete(0, tk.END); self.date_year.insert(0, "YYYY")
        self.surgery_var.set("Yes")
        self.medicines_var.set("Yes")
        self.lunch_var.set("Yes")
        self.dressing_var.set("Yes")
        self.followup_var.set("Yes")
        self.gst_var.set("")
        self.unit_var.set("Per Day")
        self.custom_notes.delete('1.0', tk.END)
        self.custom_notes.insert('1.0', 'Special offer, payment terms, etc.')

    def generate_pdf(self):
        name = self.name_entry.get().strip()
        age = self.age_entry.get().strip()
        sex = self.sex_entry.get().strip()
        contact = self.contact_entry.get().strip()
        
        if not all([name, age, sex, contact]):
            messagebox.showerror("Error", "Fill all required fields")
            return
        
        if self.date_day.get() == "DD" or self.date_month.get() == "MM" or self.date_year.get() == "YYYY":
            messagebox.showerror("Error", "Enter valid date")
            return
        
        if not self.scalp_enable.get() and not self.beard_enable.get():
            messagebox.showerror("Error", "Select at least one procedure")
            return

        procs = []
        if self.scalp_enable.get():
            try:
                smin = int(self.scalp_min.get())
                smax = int(self.scalp_max.get())
                sprice = float(self.scalp_price.get())
                procs.append(('Scalp', smin, smax, sprice, int(smin*sprice), int(smax*sprice)))
            except:
                messagebox.showerror("Error", "Invalid Scalp values")
                return

        if self.beard_enable.get():
            try:
                bmin = int(self.beard_min.get())
                bmax = int(self.beard_max.get())
                bprice = float(self.beard_price.get())
                procs.append(('Beard', bmin, bmax, bprice, int(bmin*bprice), int(bmax*bprice)))
            except:
                messagebox.showerror("Error", "Invalid Beard values")
                return

        try:
            anaes = float(self.anaesthetic.get())
        except:
            messagebox.showerror("Error", "Invalid anaesthetic amount")
            return

        # Get custom notes
        notes = self.custom_notes.get('1.0', 'end-1c').strip()
        if notes == 'Special offer, payment terms, etc.' or not notes:
            notes = ""

        date = f"{self.date_day.get()}-{self.date_month.get()}-{self.date_year.get()}"
        
        fname = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                                            initialfile=f"Estimate_{name.replace(' ','_')}.pdf")
        if not fname:
            return

        self.create_pdf(fname, name, age, sex, contact, self.technology_var.get(), 
                       self.duration_entry.get(), procs, anaes, date, notes)
        
        # Save to CSV
        self.save_to_csv(name, age, sex, contact, self.technology_var.get(), procs, anaes, date, notes)

    def save_to_csv(self, name, age, sex, contact, tech, procs, anaes, date, notes):
        """Save patient data to CSV file"""
        try:
            # Determine CSV file path
            csv_file = "Data_of_HT_Estimate_Generator.csv"
            file_exists = os.path.isfile(csv_file)
            
            # Prepare data
            scalp_grafts = ""
            scalp_cost = ""
            beard_grafts = ""
            beard_cost = ""
            total_min = anaes
            total_max = anaes
            
            for proc_type, gmin, gmax, rate, cmin, cmax in procs:
                if proc_type == 'Scalp':
                    scalp_grafts = f"{gmin}-{gmax}"
                    scalp_cost = f"{cmin}-{cmax}"
                    total_min += cmin
                    total_max += cmax
                elif proc_type == 'Beard':
                    beard_grafts = f"{gmin}-{gmax}"
                    beard_cost = f"{cmin}-{cmax}"
                    total_min += cmin
                    total_max += cmax
            
            total_estimate = f"{int(total_min)}-{int(total_max)} Range"
            
            # Write to CSV
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header if file is new
                if not file_exists:
                    writer.writerow([
                        'Date', 'Name', 'Age', 'Sex', 'Contact', 'Technology',
                        'Scalp_Grafts', 'Scalp_Cost', 'Beard_Grafts', 'Beard_Cost',
                        'Anaesthetic_Charges', 'Total_Estimate', 'Custom_Notes'
                    ])
                
                # Write data row
                writer.writerow([
                    date, name, age, sex, contact, tech,
                    scalp_grafts, scalp_cost, beard_grafts, beard_cost,
                    int(anaes), total_estimate, notes if notes else ""
                ])
            
            print(f"Data saved to {csv_file}")
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            # Don't show error to user - CSV is optional

    def create_pdf(self, fname, name, age, sex, contact, tech, dur, procs, anaes, date, notes):
        try:
            doc = SimpleDocTemplate(fname, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            elements = []
            pw = A4[0] - 80

            header = HeaderWithLogo(self.logo_path, pw, 60)
            elements.append(header)
            elements.append(Spacer(1, 0.25*inch))

            # Basic Info
            info = [['Name:', name], ['Age/Sex:', f"{age} / {sex}"], ['Contact Details:', contact]]
            t = Table(info, colWidths=[1.8*inch, 5.4*inch])
            t.setStyle(TableStyle([
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('PADDING', (0,0), (-1,-1), 6)
            ]))
            elements.append(t)
            elements.append(Spacer(1, 0.2*inch))

            # Procedure Table
            pdata = [['Technology', 'Duration', '', 'Number of Grafts', 'Per Graft\nCharges', 'Total Charges']]
            for i, (ptype, gmin, gmax, rate, cmin, cmax) in enumerate(procs):
                pdata.append([
                    tech if i == 0 else '',
                    dur if i == 0 else '',
                    ptype,
                    f"{gmin} - {gmax}",
                    f"Rs. {rate:.0f}/-",
                    f"Rs. {cmin:,} – {cmax:,}/-"
                ])
            
            pt = Table(pdata, colWidths=[0.9*inch, 0.7*inch, 0.7*inch, 1.2*inch, 1.0*inch, 2.7*inch])
            pt.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 6),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e6f2ff'))
            ]))
            elements.append(pt)
            elements.append(Spacer(1, 0.2*inch))

            # Inclusions
            gst_status = 'Excluded' if self.gst_var.get() in ['Yes', ''] else 'Included'
            gst_value = self.gst_var.get() if self.gst_var.get() else '-'
            
            idata = [
                ['Surgery', 'Included' if self.surgery_var.get() == 'Yes' else 'Excluded', self.surgery_var.get()],
                ['Anaesthetic Charges', 'Excluded', f'Rs. {anaes:,.2f}/-'],
                ['Medicines during surgery', 'Included' if self.medicines_var.get() == 'Yes' else 'Excluded', self.medicines_var.get()],
                ['Lunch + Beverages', 'Included' if self.lunch_var.get() == 'Yes' else 'Excluded', self.lunch_var.get()],
                ['Dressing & head wash after procedure', 'Included' if self.dressing_var.get() == 'Yes' else 'Excluded', self.dressing_var.get()],
                ['One year follow up with medical team', 'Included' if self.followup_var.get() == 'Yes' else 'Excluded', self.followup_var.get()],
                ['GST @ 5%', gst_status, gst_value]
            ]
            it = Table(idata, colWidths=[3.0*inch, 1.5*inch, 2.7*inch])
            it.setStyle(TableStyle([
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('PADDING', (0,0), (-1,-1), 6)
            ]))
            elements.append(it)
            elements.append(Spacer(1, 0.15*inch))

            # Custom Notes Section (if provided)
            if notes:
                notes_data = [['Additional Notes:', notes]]
                notes_table = Table(notes_data, colWidths=[1.8*inch, 5.4*inch])
                notes_table.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ('PADDING', (0,0), (-1,-1), 6),
                    ('BACKGROUND', (0,0), (0,0), colors.HexColor('#ffffcc')),
                    ('VALIGN', (0,0), (-1,-1), 'TOP')
                ]))
                elements.append(notes_table)
                elements.append(Spacer(1, 0.15*inch))

            # Payment
            pay = [
                ['Advanced Payment (Date Booking)', 'Rs. 10,000/- (Non Refundable)'],
                ['Date:', date]
            ]
            payt = Table(pay, colWidths=[3.6*inch, 3.6*inch])
            payt.setStyle(TableStyle([
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('PADDING', (0,0), (-1,-1), 6)
            ]))
            elements.append(payt)
            elements.append(Spacer(1, 0.15*inch))

            # Notes
            excluded_notes = [
                ['Excluded:-', 'Pre Procedure Blood Test\nPost Op Immediate Medication']
            ]
            nt = Table(excluded_notes, colWidths=[1.5*inch, 5.7*inch])
            nt.setStyle(TableStyle([
                ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 4)
            ]))
            elements.append(nt)
            elements.append(Spacer(1, 0.1*inch))

            # Disclaimer
            disc = [
                ['* This Budget and graft estimate may vary, during in-person consultation.'],
                ['** Subject to change as per hair follicle diameter, density and scalp width.']
            ]
            dt = Table(disc, colWidths=[7.2*inch])
            dt.setStyle(TableStyle([
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('TEXTCOLOR', (0,0), (-1,-1), colors.grey),
                ('PADDING', (0,0), (-1,-1), 2)
            ]))
            elements.append(dt)
            elements.append(Spacer(1, 0.15*inch))

            # Footer
            footer = [[
                'Yours Sincerely,\nKrishna Vora\nManager.',
                '+91 93133 14270\ninfo@zeevaclinic.com\n303-304, Indraprastha Business House,\nAhmedabad-380009 INDIA'
            ]]
            ft = Table(footer, colWidths=[3.6*inch, 3.6*inch])
            ft.setStyle(TableStyle([
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP')
            ]))
            elements.append(ft)

            doc.build(elements)
            messagebox.showinfo("Success", f"PDF generated!\n{fname}\n\nData saved to: Data_of_HT_Estimate_Generator.csv")
            
            try:
                if sys.platform.startswith('win'):
                    os.startfile(fname)
                else:
                    os.system(f'{"open" if sys.platform == "darwin" else "xdg-open"} "{fname}"')
            except:
                pass

        except Exception as e:
            messagebox.showerror("Error", f"PDF generation failed: {e}")

def main():
    root = tk.Tk()
    app = HairTransplantEstimateGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
