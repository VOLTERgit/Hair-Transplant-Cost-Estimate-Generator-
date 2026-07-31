# Hair_Transplant_Estimate_Generator_Enhanced.py
# Zeeva Clinic - Hair Transplant Estimate Generator
# Enhanced version with editable prices, custom notes and
# a single-page branded PDF (Zeeva design: navy / teal / light-blue).

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase.pdfmetrics import stringWidth
import os
import sys
import csv
from pathlib import Path

# ──────────────────────────────────────────────────────────────────
#  ZEEVA BRAND PALETTE  (taken from the sample budget PDF)
# ──────────────────────────────────────────────────────────────────
NAVY        = colors.HexColor('#152A41')   # dark banner background
NAVY_TEXT   = colors.HexColor('#1F2D3D')   # headings / dark text
GRAY_TEXT   = colors.HexColor('#7C8794')   # secondary text
TEAL        = colors.HexColor('#14B8A6')   # accent (numbers, dots)
LIGHT_BLUE  = colors.HexColor('#EEF2FB')   # light row / stat background
HEADER_BLUE = colors.HexColor('#E4EBF5')   # pricing-card header band
MINT_BG     = colors.HexColor('#E2F6F4')   # "not included" box
BORDER_GRAY = colors.HexColor('#D9E0EA')   # thin card borders


def inr(n):
    """Format a number with Indian digit grouping: 125000 -> 1,25,000"""
    n = int(round(n))
    sign = '-' if n < 0 else ''
    s = str(abs(n))
    if len(s) <= 3:
        return sign + s
    head, last3 = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return sign + ','.join(parts) + ',' + last3


def rs_range(vmin, vmax):
    """Rs. 1,20,000 - 1,50,000  (single value if min == max)"""
    if int(vmin) == int(vmax):
        return f"Rs. {inr(vmin)}"
    return f"Rs. {inr(vmin)} - {inr(vmax)}"


def fit_font(text, font, size, max_width, min_size=5.5):
    """Shrink font size until text fits max_width."""
    while size > min_size and stringWidth(text, font, size) > max_width:
        size -= 0.25
    return size


def _addon_card(c, x, y, w, h, title, value, value_color, subtext):
    """Draws one OPTIONAL ADD-ON card (white box, title / value / subtext)."""
    c.setFillColor(colors.white)
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.7)
    c.roundRect(x, y - h, w, h, 2, stroke=1, fill=1)
    c.setFillColor(NAVY_TEXT)
    c.setFont('Helvetica-Bold', fit_font(title, 'Helvetica-Bold', 9.5, w - 20))
    c.drawString(x + 10, y - 13, title)
    c.setFillColor(value_color)
    c.setFont('Helvetica-Bold', fit_font(value, 'Helvetica-Bold', 9.5, w - 20))
    c.drawString(x + 10, y - 25, value)
    c.setFillColor(GRAY_TEXT)
    c.setFont('Helvetica', fit_font(subtext, 'Helvetica', 7, w - 20))
    c.drawString(x + 10, (y - h) + 7, subtext)


def draw_addon_section(c, x0, y, width, addons, rh=38, gap_after=12):
    """
    Draws the OPTIONAL ADD-ON section. One row per selected therapy:
    therapy card (left) + LLLT card (right). Returns the new y cursor.

    addons : list of (name, price) e.g. [('GFC', 8000.0), ('PRP', 8000.0)]
    """
    if not addons:
        return y
    c.setFillColor(GRAY_TEXT)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(x0, y - 8, 'OPTIONAL ADD-ON')
    y -= 14

    gap = 8
    cw = (width - gap) / 2.0
    row_gap = 6
    for name, price in addons:
        _addon_card(c, x0, y, cw, rh,
                    f'{name} Therapy', f'Rs. {inr(price)}', TEAL,
                    '1 session · maintenance of existing hair')
        _addon_card(c, x0 + cw + gap, y, cw, rh,
                    'LLLT Therapy', 'Included', TEAL,
                    f'Combined with {name} session')
        y -= rh + row_gap
    return y - (gap_after - row_gap)


def followup_stat(text):
    """Compact follow-up value for the top stat box: '1-Year' -> '1 Yr',
    '18 Months' -> '18 Mo'. Falls back to '1 Yr' when empty."""
    if not text or not text.strip():
        return '1 Yr'
    num, started = '', False
    for ch in text:
        if ch.isdigit():
            num += ch
            started = True
        elif started:
            break
    unit = 'Mo' if 'month' in text.lower() else 'Yr'
    if num:
        return f'{num} {unit}'
    return text.strip()[:7]


def draw_estimate_pdf(fname, logo_path, name, age, sex, contact, tech_label,
                      techniques, scalp_grafts, beard_data, anaes, anaes_unit,
                      date, notes, inclusions, gst_included, addons=None,
                      followup_label=None):
    """
    Draws the whole estimate on ONE A4 page in the Zeeva sample style.

    inclusions   : list of (title, description) for items marked "Yes"
    gst_included : True  -> GST rows + totals incl. GST shown in pricing cards
                   False -> GST listed under NOT INCLUDED (charged extra)
    """
    PW, PH = A4                       # 595 x 842 pt
    M = 36                            # page margin
    CW = PW - 2 * M                   # content width
    c = pdfcanvas.Canvas(fname, pagesize=A4)
    y = PH - M                        # running cursor (top -> bottom)

    # Adaptive vertical density — shrink gaps when the page is content-heavy
    # so everything always stays on ONE page.
    _cards = (len(techniques) if (scalp_grafts and techniques) else 0) + (1 if beard_data else 0)
    _arows = len(addons) if addons else 0
    _irows = (len(inclusions) + 1) // 2 if inclusions else 0
    ULTRA = (_cards >= 4) or (_cards + _arows + _irows >= 9)
    COMPACT = ULTRA or (_cards >= 3) or (_irows >= 4) or (_cards + _arows >= 4) or \
              (_cards + _arows + _irows >= 6)
    G        = 6 if ULTRA else (8 if COMPACT else 12)   # gap between sections
    STAT_H   = 38 if COMPACT else 42
    INCL_RH  = 33 if COMPACT else 35   # cell stays tall enough for 2 clean lines
    ADDON_RH = 40 if COMPACT else 42
    DISC_GAP = 16 if ULTRA else (24 if COMPACT else 30)

    # ── 1. Header: brand left, logo right ─────────────────────────
    c.setFillColor(NAVY_TEXT)
    c.setFont('Helvetica-Bold', 17)
    c.drawString(M, y - 16, 'ZEEVA HAIR RESTORATION')
    c.setFillColor(GRAY_TEXT)
    c.setFont('Helvetica', 9)
    c.drawString(M, y - 30, 'Zeeva Treatment Proposal')

    if logo_path and os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            iw, ih = img.getSize()
            lh = 40.0
            lw = lh * iw / float(ih)
            if lw > 150:
                lw = 150.0
                lh = lw * ih / float(iw)
            c.drawImage(img, PW - M - lw, y - lh, width=lw, height=lh,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    y -= 48

    # ── 2. Navy title banner ──────────────────────────────────────
    bh = 46
    c.setFillColor(NAVY)
    c.roundRect(M, y - bh, CW, bh, 3, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(M + 14, y - 20, f'{tech_label} - Hair Transplant Estimate')
    c.setFillColor(colors.HexColor('#A9C2D8'))
    c.setFont('Helvetica', 8)
    c.drawString(M + 14, y - 34, 'Doctor-Led  ·  Zero Scar  ·  Choi Implanter Pen Technique')
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(colors.white)
    c.drawRightString(M + CW - 14, y - 20, f'Date: {date}')
    y -= bh + 8

    # ── 3. Patient strip ──────────────────────────────────────────
    ph = 22
    c.setFillColor(LIGHT_BLUE)
    c.roundRect(M, y - ph, CW, ph, 3, stroke=0, fill=1)
    c.setFillColor(NAVY_TEXT)
    c.setFont('Helvetica-Bold', 9)
    c.drawString(M + 14, y - 15, 'Patient:')
    c.setFont('Helvetica', 9)
    ptxt = f'{name}   ·   {age} / {sex}   ·   {contact}'
    c.setFont('Helvetica', fit_font(ptxt, 'Helvetica', 9, CW - 80))
    c.drawString(M + 56, y - 15, ptxt)
    y -= ph + 10

    # ── 4. Stats row (fixed, as in sample) ────────────────────────
    sh = STAT_H
    gap = 8
    sw = (CW - 2 * gap) / 3.0
    stats = [('12+', 'Years of doctor experience'),
             ('5,000+', 'Successful surgeries'),
             (followup_stat(followup_label), 'Follow-up included')]
    for i, (big, small) in enumerate(stats):
        x = M + i * (sw + gap)
        c.setFillColor(LIGHT_BLUE)
        c.roundRect(x, y - sh, sw, sh, 3, stroke=0, fill=1)
        c.setFillColor(TEAL)
        c.setFont('Helvetica-Bold', 15)
        c.drawCentredString(x + sw / 2, y - 18, big)
        c.setFillColor(GRAY_TEXT)
        c.setFont('Helvetica', 7.5)
        c.drawCentredString(x + sw / 2, y - 31, small)
    y -= sh + G

    # ── 5. WHAT'S INCLUDED (dynamic, from GUI) ────────────────────
    if inclusions:
        c.setFillColor(GRAY_TEXT)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(M, y - 8, "WHAT'S INCLUDED")
        y -= 14
        rh = INCL_RH
        colw = (CW - gap) / 2.0
        rows = (len(inclusions) + 1) // 2
        for idx, (title, desc) in enumerate(inclusions):
            r, col = divmod(idx, 2)
            x = M + col * (colw + gap)
            ry = y - r * rh
            c.setFillColor(colors.white)
            c.setStrokeColor(BORDER_GRAY)
            c.setLineWidth(0.7)
            c.roundRect(x, ry - rh + 3, colw, rh - 3, 2, stroke=1, fill=1)
            c.setFillColor(TEAL)
            c.circle(x + 12, ry - 13, 3, stroke=0, fill=1)
            c.setFillColor(NAVY_TEXT)
            c.setFont('Helvetica-Bold', 8.5)
            c.drawString(x + 22, ry - 12, title)
            c.setFillColor(GRAY_TEXT)
            c.setFont('Helvetica', 7)
            c.drawString(x + 22, ry - 23, desc)
        y -= rows * rh + G

    # ── 6. PRICING BREAKDOWN (dynamic cards) ──────────────────────
    cards = []   # (header, sub, grafts(min,max), rate, duration)
    if scalp_grafts and techniques:
        smin, smax = scalp_grafts
        for tname, trate, tdur in techniques:
            cards.append((f'{tname} · Scalp', tdur, smin, smax, trate))
    if beard_data:
        bmin, bmax, bprice, bdur = beard_data
        cards.append(('DHT · Beard', bdur, bmin, bmax, bprice))

    if cards:
        gmin, gmax = cards[0][2], cards[0][3]
        glabel = f'{inr(gmin)} - {inr(gmax)}' if gmin != gmax else inr(gmin)
        gst_note = 'GST @ 5% INCLUDED' if gst_included else 'GST @ 5% EXTRA'
        c.setFillColor(GRAY_TEXT)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(M, y - 8, f'PRICING BREAKDOWN  ·  {glabel} GRAFTS  ·  {gst_note}')
        y -= 14

        n = len(cards)
        cgap = 8
        cw = (CW - (n - 1) * cgap) / float(n)
        hdr_h, row_h, tot_h = 20, 14, 28
        rows_n = 4 if gst_included else 3
        ch = hdr_h + rows_n * row_h + tot_h

        for i, (title, dur, mn, mx, rate) in enumerate(cards):
            x = M + i * (cw + cgap)
            sub_min, sub_max = mn * rate, mx * rate
            gst_min, gst_max = sub_min * 0.05, sub_max * 0.05
            if gst_included:
                tot_min, tot_max = sub_min + gst_min, sub_max + gst_max
            else:
                tot_min, tot_max = sub_min, sub_max

            # card frame
            c.setFillColor(colors.white)
            c.setStrokeColor(BORDER_GRAY)
            c.setLineWidth(0.7)
            c.roundRect(x, y - ch, cw, ch, 2, stroke=1, fill=1)
            # header band
            c.setFillColor(HEADER_BLUE)
            c.rect(x, y - hdr_h, cw, hdr_h, stroke=0, fill=1)
            c.setFillColor(NAVY_TEXT)
            fs = fit_font(title, 'Helvetica-Bold', 9, cw - 60)
            c.setFont('Helvetica-Bold', fs)
            c.drawString(x + 8, y - 13, title)
            c.setFillColor(GRAY_TEXT)
            c.setFont('Helvetica', 7)
            c.drawRightString(x + cw - 8, y - 13, dur)

            grafts_txt = f'{inr(mn)} - {inr(mx)}' if mn != mx else inr(mn)
            rows = [('Number of grafts', grafts_txt),
                    ('Rate per graft', f'Rs. {rate:g}'),
                    ('Subtotal', rs_range(sub_min, sub_max))]
            if gst_included:
                rows.append(('GST @ 5%', rs_range(gst_min, gst_max)))

            ry = y - hdr_h
            for j, (lab, val) in enumerate(rows):
                if j % 2 == 1:
                    c.setFillColor(LIGHT_BLUE)
                    c.rect(x, ry - row_h, cw, row_h, stroke=0, fill=1)
                c.setFillColor(GRAY_TEXT)
                c.setFont('Helvetica', 7.5)
                c.drawString(x + 8, ry - 10, lab)
                c.setFillColor(NAVY_TEXT)
                vfs = fit_font(val, 'Helvetica-Bold', 7.5, cw - 16 - stringWidth(lab, 'Helvetica', 7.5) - 6)
                c.setFont('Helvetica-Bold', vfs)
                c.drawRightString(x + cw - 8, ry - 10, val)
                ry -= row_h

            # total band (label on top, value below — never overlaps)
            c.setFillColor(LIGHT_BLUE)
            c.rect(x, ry - tot_h, cw, tot_h, stroke=0, fill=1)
            c.setFillColor(NAVY_TEXT)
            c.setFont('Helvetica-Bold', 7.5)
            tlabel = 'Total (incl. GST)' if gst_included else 'Total'
            c.drawString(x + 8, ry - 11, tlabel)
            tval = rs_range(tot_min, tot_max)
            c.setFillColor(TEAL)
            tfs = fit_font(tval, 'Helvetica-Bold', 10, cw - 16)
            c.setFont('Helvetica-Bold', tfs)
            c.drawRightString(x + cw - 8, ry - 23, tval)

        y -= ch + G

    # ── 6b. OPTIONAL ADD-ON (dynamic) ─────────────────────────────
    y = draw_addon_section(c, M, y, CW, addons, rh=ADDON_RH, gap_after=G)

    # ── 7. Advance payment navy banner ────────────────────────────
    ah = 40
    c.setFillColor(NAVY)
    c.roundRect(M, y - ah, CW, ah, 3, stroke=0, fill=1)
    c.setFillColor(colors.HexColor('#A9C2D8'))
    c.setFont('Helvetica', 8)
    c.drawString(M + 14, y - 14, 'Advance Payment (Date Booking)')
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(M + 14, y - 30, 'Rs. 10,000')
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#A9C2D8'))
    c.drawRightString(M + CW - 14, y - 24, 'Non-refundable  ·  Advance to confirm your slot')
    y -= ah + G

    # ── 8. NOT INCLUDED box ───────────────────────────────────────
    excl = []
    if not gst_included:
        excl.append('GST @ 5% — charged extra on transplant charges')
    if anaes and anaes > 0:
        excl.append(f'Anaesthetic charges — Rs. {inr(anaes)} ({anaes_unit})')
    excl.append('Pre-procedure blood test — at actuals')
    excl.append('Post-op immediate medication — prescribed at actuals')

    nh = 16 + len(excl) * 11 + 6
    c.setFillColor(MINT_BG)
    c.rect(M, y - nh, CW, nh, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(M, y - nh, 3, nh, stroke=0, fill=1)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(M + 14, y - 13, 'NOT INCLUDED')
    c.setFillColor(NAVY_TEXT)
    c.setFont('Helvetica', 8)
    ly = y - 25
    for item in excl:
        c.drawString(M + 14, ly, u'\u2022  ' + item)
        ly -= 11
    y -= nh + G

    # ── 9. Custom notes (optional) ────────────────────────────────
    if notes:
        note_lines = []
        for raw in notes.split('\n'):
            words, line = raw.split(), ''
            for w in words:
                t = (line + ' ' + w).strip()
                if stringWidth(t, 'Helvetica', 8) > CW - 80:
                    note_lines.append(line)
                    line = w
                else:
                    line = t
            note_lines.append(line)
        note_lines = [l for l in note_lines if l] or ['']
        nth = 10 + len(note_lines) * 10 + 6
        c.setFillColor(LIGHT_BLUE)
        c.rect(M, y - nth, CW, nth, stroke=0, fill=1)
        c.setFillColor(NAVY_TEXT)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(M + 14, y - 12, 'NOTES:')
        c.setFont('Helvetica', 8)
        ly = y - 12
        for i, l in enumerate(note_lines):
            c.drawString(M + 56 if i == 0 else M + 14, ly, l)
            ly -= 10
        y -= nth + G

    # ── 10-12. Disclaimers + signature flow right after the content
    # (small consistent gap); the footer line stays pinned at the page
    # bottom. On very heavy pages the block clamps so nothing overlaps.
    fy = M + 14                       # footer line (pinned to bottom)
    min_bt = fy + 18 + 54             # lowest the block may sit (keeps it above footer)
    bt = max(y - 16, min_bt)          # block top: flows after content, else clamps
    # Last-resort safety for impossible overflow: never overlap content.
    if bt > y - 6:
        bt = max(y - 6, fy + 18 + 54 - 8)

    c.setFillColor(GRAY_TEXT)
    c.setFont('Helvetica-Oblique', 7.5)
    c.drawString(M, bt, '*  This budget and graft estimate may vary during in-person consultation.')
    c.drawString(M, bt - 10, '** Subject to change as per hair follicle diameter, density and scalp width.')

    c.setFillColor(NAVY_TEXT)
    c.setFont('Helvetica', 9)
    c.drawString(M, bt - 28, 'Yours Sincerely,')
    c.setFont('Helvetica-Bold', 11)
    c.drawString(M, bt - 42, 'Krishna Vora')
    c.setFillColor(GRAY_TEXT)
    c.setFont('Helvetica', 8.5)
    c.drawString(M, bt - 54, 'Manager')

    c.setFillColor(GRAY_TEXT)
    c.setFont('Helvetica', 8.5)
    c.drawRightString(M + CW, bt - 28, '+91 93133 14270   ·   info@zeevaclinic.com')
    c.drawRightString(M + CW, bt - 40, '303-304, Indraprastha Business House,')
    c.drawRightString(M + CW, bt - 52, 'Ahmedabad-380009 INDIA')

    # Footer line + terms (pinned to bottom)
    c.setStrokeColor(BORDER_GRAY)
    c.setLineWidth(0.7)
    c.line(M, fy, M + CW, fy)
    c.setFillColor(GRAY_TEXT)
    c.setFont('Helvetica', 7)
    c.drawCentredString(PW / 2, fy - 10,
                        'Terms & conditions apply  ·  Pricing valid for quoted case  ·  '
                        'Subject to consultation  ·  ZEEVA HAIR RESTORATION')

    c.showPage()
    c.save()


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

        # ── Scalp Techniques ─────────────────────────────────────────
        ttk.Label(main_frame, text="Scalp Techniques", style='Bold.TLabel', foreground='blue').grid(
            row=row, column=0, columnspan=4, sticky=tk.W, pady=(0,2))
        row += 1

        # Column headers for techniques
        hdr = ttk.Frame(main_frame)
        hdr.grid(row=row, column=0, columnspan=4, sticky=tk.W)
        ttk.Label(hdr, text="", width=6).grid(row=0, column=0)
        ttk.Label(hdr, text="Per Graft Rs", style='Normal.TLabel', width=13).grid(row=0, column=1)
        ttk.Label(hdr, text="Duration", style='Normal.TLabel', width=10).grid(row=0, column=2)
        row += 1

        # DHT
        dht_frame = ttk.Frame(main_frame)
        dht_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=2)
        self.dht_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dht_frame, text="DHT", variable=self.dht_var,
                        command=self.toggle_techniques, width=5).grid(row=0, column=0, sticky=tk.W)
        self.dht_price = ttk.Entry(dht_frame, width=8)
        self.dht_price.insert(0, "60")
        self.dht_price.grid(row=0, column=1, padx=(4,8))
        self.dht_dur = ttk.Entry(dht_frame, width=10)
        self.dht_dur.insert(0, "Day 1")
        self.dht_dur.grid(row=0, column=2)
        row += 1

        # FUE
        fue_frame = ttk.Frame(main_frame)
        fue_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=2)
        self.fue_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(fue_frame, text="FUE", variable=self.fue_var,
                        command=self.toggle_techniques, width=5).grid(row=0, column=0, sticky=tk.W)
        self.fue_price = ttk.Entry(fue_frame, width=8)
        self.fue_price.insert(0, "50")
        self.fue_price.grid(row=0, column=1, padx=(4,8))
        self.fue_dur = ttk.Entry(fue_frame, width=10)
        self.fue_dur.insert(0, "Day 1")
        self.fue_dur.grid(row=0, column=2)
        row += 1

        # Scalp grafts
        scalp_frame = ttk.Frame(main_frame)
        scalp_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=3)
        self.scalp_enable = tk.BooleanVar(value=False)
        ttk.Checkbutton(scalp_frame, text="Scalp Grafts", variable=self.scalp_enable,
                        command=self.toggle_scalp).grid(row=0, column=0, sticky=tk.W)
        self.scalp_min = ttk.Entry(scalp_frame, width=8, state='disabled')
        self.scalp_min.grid(row=0, column=1, padx=(5,2))
        ttk.Label(scalp_frame, text="-").grid(row=0, column=2)
        self.scalp_max = ttk.Entry(scalp_frame, width=8, state='disabled')
        self.scalp_max.grid(row=0, column=3, padx=(2,5))
        self.scalp_total = ttk.Label(scalp_frame, text="", style='Normal.TLabel')
        self.scalp_total.grid(row=0, column=4, padx=(8,0))
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=6)
        row += 1

        # ── Beard (DHT only, own price + duration) ───────────────────
        ttk.Label(main_frame, text="Beard (DHT)", style='Bold.TLabel', foreground='blue').grid(
            row=row, column=0, columnspan=4, sticky=tk.W, pady=(0,2))
        row += 1

        beard_frame = ttk.Frame(main_frame)
        beard_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=2)
        self.beard_enable = tk.BooleanVar(value=False)
        ttk.Checkbutton(beard_frame, text="Enable", variable=self.beard_enable,
                        command=self.toggle_beard).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(beard_frame, text="Grafts:", style='Normal.TLabel').grid(row=0, column=1, padx=(8,4))
        self.beard_min = ttk.Entry(beard_frame, width=7, state='disabled')
        self.beard_min.grid(row=0, column=2)
        ttk.Label(beard_frame, text="-").grid(row=0, column=3)
        self.beard_max = ttk.Entry(beard_frame, width=7, state='disabled')
        self.beard_max.grid(row=0, column=4, padx=(0,8))
        ttk.Label(beard_frame, text="@ Rs:", style='Normal.TLabel').grid(row=0, column=5, padx=(0,4))
        self.beard_price = ttk.Entry(beard_frame, width=7, state='disabled')
        self.beard_price.insert(0, "70")
        self.beard_price.grid(row=0, column=6, padx=(0,8))
        ttk.Label(beard_frame, text="Dur:", style='Normal.TLabel').grid(row=0, column=7, padx=(0,4))
        self.beard_dur = ttk.Entry(beard_frame, width=8, state='disabled')
        self.beard_dur.insert(0, "Day 1")
        self.beard_dur.grid(row=0, column=8)
        row += 1

        self.beard_total = ttk.Label(main_frame, text="", style='Normal.TLabel')
        self.beard_total.grid(row=row, column=0, columnspan=4, sticky=tk.W, padx=(8,0))
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=6)
        row += 1

        # ── Optional Add-On (PRP / GFC) ──────────────────────────────
        ttk.Label(main_frame, text="Optional Add-On", style='Bold.TLabel', foreground='blue').grid(
            row=row, column=0, columnspan=4, sticky=tk.W, pady=(0,2))
        row += 1

        addon_frame = ttk.Frame(main_frame)
        addon_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=2)
        self.addon_enable = tk.BooleanVar(value=False)
        ttk.Checkbutton(addon_frame, text="Include PRP/GFC Add-On Details",
                        variable=self.addon_enable, command=self.toggle_addon).grid(
            row=0, column=0, columnspan=6, sticky=tk.W)
        row += 1

        sub_frame = ttk.Frame(main_frame)
        sub_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=2)
        # GFC
        self.gfc_var = tk.BooleanVar(value=False)
        self.gfc_chk = ttk.Checkbutton(sub_frame, text="GFC", variable=self.gfc_var, width=6, state='disabled')
        self.gfc_chk.grid(row=0, column=0, sticky=tk.W)
        ttk.Label(sub_frame, text="@ Rs:", style='Normal.TLabel').grid(row=0, column=1, padx=(8,4))
        self.gfc_price = ttk.Entry(sub_frame, width=10, state='disabled')
        self.gfc_price.insert(0, "8000")
        self.gfc_price.grid(row=0, column=2, padx=(0,20))
        # PRP
        self.prp_var = tk.BooleanVar(value=False)
        self.prp_chk = ttk.Checkbutton(sub_frame, text="PRP", variable=self.prp_var, width=6, state='disabled')
        self.prp_chk.grid(row=0, column=3, sticky=tk.W)
        ttk.Label(sub_frame, text="@ Rs:", style='Normal.TLabel').grid(row=0, column=4, padx=(8,4))
        self.prp_price = ttk.Entry(sub_frame, width=10, state='disabled')
        self.prp_price.insert(0, "8000")
        self.prp_price.grid(row=0, column=5)
        row += 1

        # Calculate button
        ttk.Button(main_frame, text="Calculate", command=self.calculate_charges, width=15).grid(
            row=row, column=0, columnspan=4, pady=8)
        row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=4, sticky='ew', pady=8)
        row += 1

        # Inclusions Section
        ttk.Label(main_frame, text="What's Included (Yes/No)", style='Bold.TLabel', foreground='blue').grid(
            row=row, column=0, columnspan=4, sticky=tk.W, pady=(0,6))
        row += 1

        # Row 1: Doctor-Led Surgery | Zero Scar Technique
        incl_frame1 = ttk.Frame(main_frame)
        incl_frame1.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(incl_frame1, text="Doctor-Led Surgery", width=20).grid(row=0, column=0, sticky=tk.W)
        self.surgery_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame1, textvariable=self.surgery_var, values=["Yes", "No"],
                    width=8, state='readonly').grid(row=0, column=1, sticky=tk.W)
        ttk.Label(incl_frame1, text="Zero Scar Technique", width=20).grid(row=0, column=2, padx=(15,0), sticky=tk.W)
        self.zeroscar_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame1, textvariable=self.zeroscar_var, values=["Yes", "No"],
                    width=8, state='readonly').grid(row=0, column=3, sticky=tk.W)
        row += 1

        # Row 2: Artistic Hairline Design | Medicines During Surgery
        incl_frame2 = ttk.Frame(main_frame)
        incl_frame2.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(incl_frame2, text="Artistic Hairline", width=20).grid(row=0, column=0, sticky=tk.W)
        self.hairline_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame2, textvariable=self.hairline_var, values=["Yes", "No"],
                    width=8, state='readonly').grid(row=0, column=1, sticky=tk.W)
        ttk.Label(incl_frame2, text="Medicines during s..", width=20).grid(row=0, column=2, padx=(15,0), sticky=tk.W)
        self.medicines_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame2, textvariable=self.medicines_var, values=["Yes", "No"],
                    width=8, state='readonly').grid(row=0, column=3, sticky=tk.W)
        row += 1

        # Row 3: Lunch + Beverages | Dressing & Head Wash
        incl_frame3 = ttk.Frame(main_frame)
        incl_frame3.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(incl_frame3, text="Lunch + Beverages", width=20).grid(row=0, column=0, sticky=tk.W)
        self.lunch_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame3, textvariable=self.lunch_var, values=["Yes", "No"],
                    width=8, state='readonly').grid(row=0, column=1, sticky=tk.W)
        ttk.Label(incl_frame3, text="Dressing & head wa..", width=20).grid(row=0, column=2, padx=(15,0), sticky=tk.W)
        self.dressing_var = tk.StringVar(value="Yes")
        ttk.Combobox(incl_frame3, textvariable=self.dressing_var, values=["Yes", "No"],
                    width=8, state='readonly').grid(row=0, column=3, sticky=tk.W)
        row += 1

        # Row 4: Low Level Laser Therapy | Follow-Up (text period)
        incl_frame4 = ttk.Frame(main_frame)
        incl_frame4.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(incl_frame4, text="Low Level Laser Th..", width=20).grid(row=0, column=0, sticky=tk.W)
        self.lllt_var = tk.StringVar(value="No")
        ttk.Combobox(incl_frame4, textvariable=self.lllt_var, values=["Yes", "No"],
                    width=8, state='readonly').grid(row=0, column=1, sticky=tk.W)
        ttk.Label(incl_frame4, text="Follow-Up:", width=20).grid(row=0, column=2, padx=(15,0), sticky=tk.W)
        self.followup_entry = ttk.Entry(incl_frame4, width=10)
        self.followup_entry.insert(0, "1-Year")
        self.followup_entry.grid(row=0, column=3, sticky=tk.W)
        row += 1

        ttk.Label(main_frame, text="(Follow-Up: type the period e.g. '1-Year', '2-Year'. Leave blank to omit.)",
                  foreground='gray', font=('Arial', 8)).grid(row=row, column=0, columnspan=4, sticky=tk.W)
        row += 1

        # GST checkbox — when ticked, totals include 5% GST (as in sample)
        gst_frame = ttk.Frame(main_frame)
        gst_frame.grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=(6,2))
        self.gst_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(gst_frame, text="Add 5% GST  (totals shown include GST)",
                        variable=self.gst_var).grid(row=0, column=0, sticky=tk.W)
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
        ttk.Entry(anaes_frame, textvariable=self.unit_var, width=14).grid(row=0, column=3, padx=(5,0))
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
        if not self.scalp_enable.get():
            self.scalp_min.delete(0, tk.END)
            self.scalp_max.delete(0, tk.END)
            self.scalp_total.config(text="Rs. 0 - Rs. 0")

    def toggle_techniques(self):
        # No-op: checkboxes are always enabled; just a hook if needed
        pass

    def get_selected_techniques(self):
        """Returns list of (name, per_graft_price, duration) for checked techniques."""
        selected = []
        if self.dht_var.get():
            try:
                price = float(self.dht_price.get())
            except ValueError:
                price = 60.0
            selected.append(("DHT", price, self.dht_dur.get().strip() or "Day 1"))
        if self.fue_var.get():
            try:
                price = float(self.fue_price.get())
            except ValueError:
                price = 50.0
            selected.append(("FUE", price, self.fue_dur.get().strip() or "Day 1"))
        return selected

    def toggle_beard(self):
        state = 'normal' if self.beard_enable.get() else 'disabled'
        self.beard_min.config(state=state)
        self.beard_max.config(state=state)
        self.beard_price.config(state=state)
        self.beard_dur.config(state=state)
        if not self.beard_enable.get():
            self.beard_min.delete(0, tk.END)
            self.beard_max.delete(0, tk.END)
            self.beard_total.config(text="")
            self.beard_total.config(text="Rs. 0 - Rs. 0")

    def toggle_addon(self):
        state = 'normal' if self.addon_enable.get() else 'disabled'
        self.gfc_chk.config(state=state)
        self.prp_chk.config(state=state)
        self.gfc_price.config(state=state)
        self.prp_price.config(state=state)
        if not self.addon_enable.get():
            self.gfc_var.set(False)
            self.prp_var.set(False)

    def calculate_charges(self):
        techniques = self.get_selected_techniques()
        if not techniques and not self.beard_enable.get():
            messagebox.showerror("Error", "Select at least one Technique or enable Beard")
            return

        if self.scalp_enable.get() and techniques:
            try:
                smin = int(self.scalp_min.get())
                smax = int(self.scalp_max.get())
                # Show preview using first technique price
                avg_price = techniques[0][1]
                self.scalp_total.config(text=f"Preview @ Rs.{avg_price:.0f}: Rs.{int(smin*avg_price):,} – Rs.{int(smax*avg_price):,}")
            except ValueError:
                messagebox.showerror("Error", "Invalid Scalp graft values")
                return

        if self.beard_enable.get():
            try:
                bmin = int(self.beard_min.get())
                bmax = int(self.beard_max.get())
                bprice = float(self.beard_price.get())
                self.beard_total.config(text=f"Rs. {int(bmin*bprice):,} – Rs. {int(bmax*bprice):,}")
            except ValueError:
                messagebox.showerror("Error", "Invalid Beard values")
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
        self.dht_var.set(False)
        self.fue_var.set(False)
        self.dht_price.delete(0, tk.END); self.dht_price.insert(0, "60")
        self.fue_price.delete(0, tk.END); self.fue_price.insert(0, "50")
        self.dht_dur.delete(0, tk.END); self.dht_dur.insert(0, "Day 1")
        self.fue_dur.delete(0, tk.END); self.fue_dur.insert(0, "Day 1")
        self.scalp_enable.set(False); self.toggle_scalp()
        self.beard_enable.set(False); self.toggle_beard()
        self.beard_price.delete(0, tk.END); self.beard_price.insert(0, "70")
        self.beard_dur.delete(0, tk.END); self.beard_dur.insert(0, "Day 1")
        self.gfc_price.config(state='normal'); self.gfc_price.delete(0, tk.END); self.gfc_price.insert(0, "8000")
        self.prp_price.config(state='normal'); self.prp_price.delete(0, tk.END); self.prp_price.insert(0, "8000")
        self.addon_enable.set(False); self.toggle_addon()
        self.anaesthetic.delete(0, tk.END); self.anaesthetic.insert(0, "0")
        self.date_day.delete(0, tk.END); self.date_day.insert(0, "DD")
        self.date_month.delete(0, tk.END); self.date_month.insert(0, "MM")
        self.date_year.delete(0, tk.END); self.date_year.insert(0, "YYYY")
        self.surgery_var.set("Yes")
        self.zeroscar_var.set("Yes")
        self.hairline_var.set("Yes")
        self.medicines_var.set("Yes")
        self.lunch_var.set("Yes")
        self.dressing_var.set("Yes")
        self.lllt_var.set("No")
        self.followup_entry.delete(0, tk.END); self.followup_entry.insert(0, "1-Year")
        self.gst_var.set(False)
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

        techniques = self.get_selected_techniques()
        beard_data = None  # (bmin, bmax, bprice, bdur) or None

        if self.beard_enable.get():
            try:
                bmin = int(self.beard_min.get())
                bmax = int(self.beard_max.get())
                bprice = float(self.beard_price.get())
                bdur = self.beard_dur.get().strip() or "Day 1"
                beard_data = (bmin, bmax, bprice, bdur)
            except:
                messagebox.showerror("Error", "Invalid Beard graft values")
                return

        if not techniques and not beard_data:
            messagebox.showerror("Error", "Select at least one Scalp Technique or enable Beard")
            return

        if techniques and not self.scalp_enable.get() and not beard_data:
            messagebox.showerror("Error", "You selected Scalp Techniques but didn't enable Scalp Grafts")
            return

        scalp_grafts = None
        if self.scalp_enable.get():
            if not techniques:
                messagebox.showerror("Error", "Select at least one Technique (DHT/FUE) for Scalp")
                return
            try:
                smin = int(self.scalp_min.get())
                smax = int(self.scalp_max.get())
                scalp_grafts = (smin, smax)
            except:
                messagebox.showerror("Error", "Invalid Scalp graft values")
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

        # Optional PRP/GFC add-on (only when master checkbox is ticked)
        addons = []
        if self.addon_enable.get():
            if self.gfc_var.get():
                try:
                    gp = float(self.gfc_price.get())
                except ValueError:
                    gp = 8000.0
                addons.append(("GFC", gp))
            if self.prp_var.get():
                try:
                    pp = float(self.prp_price.get())
                except ValueError:
                    pp = 8000.0
                addons.append(("PRP", pp))
            if not addons:
                messagebox.showerror("Error", "Add-On is enabled but neither PRP nor GFC is selected.")
                return

        fname = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                                            initialfile=f"Estimate_{name.replace(' ','_')}.pdf")
        if not fname:
            return

        tech_label = " + ".join(t[0] for t in techniques) if techniques else "DHT"
        self.create_pdf(fname, name, age, sex, contact, tech_label, techniques,
                       scalp_grafts, beard_data, anaes, date, notes, addons)

        # Save to CSV
        self.save_to_csv(name, age, sex, contact, tech_label, scalp_grafts, beard_data, anaes, date, notes)

    def save_to_csv(self, name, age, sex, contact, tech, scalp_grafts, beard_data, anaes, date, notes):
        """Save patient data to CSV file"""
        try:
            csv_file = "Data_of_HT_Estimate_Generator.csv"
            file_exists = os.path.isfile(csv_file)

            scalp_info = f"{scalp_grafts[0]}-{scalp_grafts[1]}" if scalp_grafts else ""
            beard_info = f"{beard_data[0]}-{beard_data[1]} @Rs.{beard_data[2]}" if beard_data else ""

            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['Date', 'Name', 'Age', 'Sex', 'Contact', 'Techniques',
                                     'Scalp_Grafts', 'Beard_Grafts', 'Anaesthetic_Charges', 'Custom_Notes'])
                writer.writerow([date, name, age, sex, contact, tech,
                                 scalp_info, beard_info, int(anaes), notes if notes else ""])
            print(f"Data saved to {csv_file}")
        except Exception as e:
            print(f"Error saving to CSV: {e}")

    def create_pdf(self, fname, name, age, sex, contact, tech, techniques, scalp_grafts, beard_data, anaes, date, notes, addons=None):
        try:
            # Build the dynamic "WHAT'S INCLUDED" list from the GUI Yes/No fields
            # (order matches the sample layout)
            inclusions = []
            if self.surgery_var.get() == 'Yes':
                inclusions.append(('Doctor-Led Surgery', 'Included — no technicians at any stage'))
            if self.zeroscar_var.get() == 'Yes':
                inclusions.append(('Zero Scar Technique', 'Choi implanter pen — no linear scar'))
            if self.hairline_var.get() == 'Yes':
                inclusions.append(('Artistic Hairline Design', 'Crafted for a natural, aesthetic look'))
            if self.medicines_var.get() == 'Yes':
                inclusions.append(('Medicines During Surgery', 'Included on the day of procedure'))
            if self.lunch_var.get() == 'Yes':
                inclusions.append(('Lunch + Beverages', 'Included on surgery day'))
            if self.dressing_var.get() == 'Yes':
                inclusions.append(('Dressing & Head Wash', 'After procedure · head wash Day 7-10'))
            if self.lllt_var.get() == 'Yes':
                inclusions.append(('Low Level Laser Therapy', 'Combined with GFC session for best results'))
            followup = self.followup_entry.get().strip()
            if followup:
                inclusions.append((f'{followup} Follow-Up', 'Post-surgery care included at no extra cost'))

            # GST checkbox: ticked -> totals include 5% GST (shown in pricing cards);
            #               unticked -> listed under NOT INCLUDED (charged extra)
            gst_included = bool(self.gst_var.get())

            draw_estimate_pdf(fname, self.logo_path, name, age, sex, contact,
                              tech, techniques, scalp_grafts, beard_data,
                              anaes, self.unit_var.get(), date, notes,
                              inclusions, gst_included, addons,
                              followup_label=followup)

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
