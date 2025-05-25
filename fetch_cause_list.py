#!/usr/bin/env python3
import subprocess
import fitz    # PyMuPDF
import html
import sys
from datetime import datetime

# ─── CONFIG ────────────────────────────────────────────────────────────────
DATE_DDMMYYYY = "23052025"             # DDMMYYYY
SIDE          = "Appellate Side"       # "Original Side" or "Appellate Side"
ADVOCATE_NAME = "Syed Nurul Arefin"    # case-insensitive full name
OUTPUT_HTML   = "output.html"
Y_TOLERANCE   = 3                       # pts to bleed above/below
# ──────────────────────────────────────────────────────────────────────────

SIDE_INFO = {
    "Original Side":  ("OS", "clo"),
    "Appellate Side": ("AS", "cla"),
}

def fetch_pdf_bytes(date_str, side):
    code, prefix = SIDE_INFO[side]
    url = (
        f"https://www.calcuttahighcourt.gov.in"
        f"/downloads/old_cause_lists/{code}/{prefix}{date_str}.pdf"
    )
    print(f"⬇ Fetching PDF… {url}", file=sys.stderr)
    data = subprocess.check_output(
        ["curl", "--insecure", "-L", url],
        stderr=subprocess.DEVNULL
    )
    if not data.startswith(b"%PDF"):
        print("❌ Failed to fetch a valid PDF", file=sys.stderr)
        sys.exit(1)
    return data

def extract_rows_from_bytes(pdf_bytes, lawyer, tol=Y_TOLERANCE):
    tokens = [w.lower() for w in lawyer.split()]
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    seen = set()
    out = []

    for page in doc:
        raw = page.get_text("blocks")
        blocks = [(b[0], b[1], b[2], b[3], b[4]) for b in raw]

        for x0, y0, x1, y1, text in blocks:
            lower = text.lower()
            if any(tok in lower for tok in tokens):
                height = y1 - y0
                top    = y0 - tol
                bottom = y1 + height + tol

                band = []
                for bx0, by0, bx1, by1, btext in blocks:
                    midy = (by0 + by1) / 2
                    if top <= midy <= bottom:
                        band.append((bx0, by0, by1, btext))

                band.sort(key=lambda b: b[0])
                combined = " ".join(b[3].replace("\n"," ").strip() for b in band).lower()
                if all(tok in combined for tok in tokens):
                    lines = []
                    for _,_,_,blk in band:
                        for ln in blk.splitlines():
                            ln = ln.strip()
                            if ln:
                                lines.append(ln)
                    key = (page.number+1, tuple(lines))
                    if key not in seen:
                        seen.add(key)
                        out.append((page.number+1, lines))
    return out

def format_header_date(date_str):
    dt = datetime.strptime(date_str, "%d%m%Y")
    day = dt.day
    if 11 <= day <= 13:
        suffix = 'th'
    else:
        suffix = {1:'st',2:'nd',3:'rd'}.get(day%10, 'th')
    return dt.strftime(f"%A, {day}{suffix} of %B, %Y")

def generate_html(entries, advocate):
    header = format_header_date(DATE_DDMMYYYY)
    parts = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'>",
        f"<title>Cause List – {html.escape(advocate)}</title>",
        "<style>",
        "  body{font-family:sans-serif;padding:2rem}",
        "  h1{font-family:'Old English Text MT',serif;font-size:2.5rem;text-align:center;margin:0}",
        "  h2{font-family:serif;font-size:1.75rem;text-align:center;margin:0.25rem 0}",
        "  h3.title{font-family:serif;font-size:1.25rem;text-align:center;margin:1rem 0}",
        "  hr{border:none;border-top:1px solid #ccc;margin:1rem 0}",
        "  pre{background:#fafafa;padding:1rem;border:1px solid #ddd;white-space:pre-wrap}",
        "  h3{margin-top:1.5rem}",
        "</style>",
        "</head><body>",
        "  <h1>In The High Court at Calcutta</h1>",
        "  <h2>Appellate Jurisdiction</h2>",
        "  <hr>",
        f"  <h3 class='title'>Daily Supplementary List Of Cases For Hearing On {html.escape(header)}</h3>",
        "  <hr>",
    ]
    for pg, lines in entries:
        parts.append(f"  <h3>Page {pg}</h3>")
        parts.append("  <pre>")
        parts.extend(html.escape(ln) for ln in lines)
        parts.append("  </pre>")
    parts.append("</body></html>")
    return "\n".join(parts)

if __name__ == '__main__':
    pdf_bytes = fetch_pdf_bytes(DATE_DDMMYYYY, SIDE)
    entries = extract_rows_from_bytes(pdf_bytes, ADVOCATE_NAME)
    if not entries:
        print(f"❌ No entries found for '{ADVOCATE_NAME}'", file=sys.stderr)
        sys.exit(0)

    html_out = generate_html(entries, ADVOCATE_NAME)

    # 1) print to stdout
    print(html_out)

    # 2) also save as output.html
    with open(OUTPUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    print(f"✅ HTML also saved to {OUTPUT_HTML}", file=sys.stderr)