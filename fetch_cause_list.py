#!/usr/bin/env python3
"""
Generic High Court Cause List Fetcher

Usage:
    python fetch_cause_list_generic.py <DATE_DDMMYYYY> <SIDE> <ADVOCATE_NAME> [BASE_URL] [OPTIONS]

Arguments:
    DATE_DDMMYYYY    Date in DDMMYYYY format (e.g., 15052025)
    SIDE             Court side: "Original Side" or "Appellate Side"
    ADVOCATE_NAME    Full name of the advocate to search for
    BASE_URL         Base URL of the court website (optional, default: https://www.calcuttahighcourt.gov.in)

Options:
    --output-html FILE    Output HTML file path (default: output.html)
    --y-tolerance NUM     Y-axis tolerance for text extraction (default: 3)
    --help               Show this help message

Examples:
    python fetch_cause_list_generic.py 15052025 "Appellate Side" "Syed Nurul Arefin"
    python fetch_cause_list_generic.py 15052025 "Original Side" "John Doe" "https://www.calcuttahighcourt.gov.in" --output-html report.html
"""

import subprocess
import fitz    # PyMuPDF
import html
import sys
import argparse
from datetime import datetime

# ─── DEFAULT CONFIG ────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "https://www.calcuttahighcourt.gov.in"
DEFAULT_OUTPUT_HTML = "output.html"
DEFAULT_Y_TOLERANCE = 3
# ──────────────────────────────────────────────────────────────────────────

SIDE_INFO = {
    "Original Side":  ("OS", "clo"),
    "Appellate Side": ("AS", "cla"),
}

def fetch_pdf_bytes(date_str, side, base_url):
    """Fetch PDF bytes from the court website."""
    if side not in SIDE_INFO:
        raise ValueError(f"Invalid side '{side}'. Must be one of: {list(SIDE_INFO.keys())}")
    
    code, prefix = SIDE_INFO[side]
    url = f"{base_url}/downloads/old_cause_lists/{code}/{prefix}{date_str}.pdf"
    
    print(f"⬇ Fetching PDF… {url}", file=sys.stderr)
    try:
        data = subprocess.check_output(
            ["curl", "--insecure", "-L", url],
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download PDF: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not data.startswith(b"%PDF"):
        print("❌ Failed to fetch a valid PDF", file=sys.stderr)
        sys.exit(1)
    
    return data

def extract_rows_from_bytes(pdf_bytes, lawyer, tol=DEFAULT_Y_TOLERANCE):
    """Extract relevant rows from PDF bytes containing the lawyer's name."""
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
    """Format date string for the header."""
    try:
        dt = datetime.strptime(date_str, "%d%m%Y")
        day = dt.day
        if 11 <= day <= 13:
            suffix = 'th'
        else:
            suffix = {1:'st',2:'nd',3:'rd'}.get(day%10, 'th')
        return dt.strftime(f"%A, {day}{suffix} of %B, %Y")
    except ValueError:
        return f"Date: {date_str}"

def generate_html(entries, advocate, date_str, side):
    """Generate HTML report from extracted entries."""
    header = format_header_date(date_str)
    court_side = "Appellate Jurisdiction" if side == "Appellate Side" else "Original Jurisdiction"
    
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
        "  .summary{background:#e8f4fd;padding:1rem;border-left:4px solid #0055a5;margin:1rem 0}",
        "</style>",
        "</head><body>",
        "  <h1>In The High Court at Calcutta</h1>",
        f"  <h2>{court_side}</h2>",
        "  <hr>",
        f"  <h3 class='title'>Daily Supplementary List Of Cases For Hearing On {html.escape(header)}</h3>",
        "  <hr>",
    ]
    
    if entries:
        parts.append(f"  <div class='summary'>")
        parts.append(f"    <strong>🔎 Found {len(entries)} match(es) for \"{html.escape(advocate)}\"</strong>")
        parts.append(f"  </div>")
        
        for pg, lines in entries:
            parts.append(f"  <h3>Page {pg}</h3>")
            parts.append("  <pre>")
            parts.extend(html.escape(ln) for ln in lines)
            parts.append("  </pre>")
    else:
        parts.append(f"  <div class='summary'>")
        parts.append(f"    <strong>❌ No matches found for \"{html.escape(advocate)}\"</strong>")
        parts.append(f"  </div>")
    
    parts.append("</body></html>")
    return "\n".join(parts)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch and search High Court Cause Lists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 15052025 "Appellate Side" "Syed Nurul Arefin"
  %(prog)s 15052025 "Original Side" "John Doe" "https://www.calcuttahighcourt.gov.in"
  %(prog)s 15052025 "Appellate Side" "Jane Smith" --output-html report.html
        """
    )
    
    parser.add_argument('date', metavar='DATE_DDMMYYYY',
                        help='Date in DDMMYYYY format (e.g., 15052025)')
    parser.add_argument('side', metavar='SIDE',
                        choices=['Original Side', 'Appellate Side'],
                        help='Court side: "Original Side" or "Appellate Side"')
    parser.add_argument('advocate', metavar='ADVOCATE_NAME',
                        help='Full name of the advocate to search for')
    parser.add_argument('base_url', metavar='BASE_URL', nargs='?',
                        default=DEFAULT_BASE_URL,
                        help=f'Base URL of the court website (default: {DEFAULT_BASE_URL})')
    
    parser.add_argument('--output-html', metavar='FILE',
                        default=DEFAULT_OUTPUT_HTML,
                        help=f'Output HTML file path (default: {DEFAULT_OUTPUT_HTML})')
    parser.add_argument('--y-tolerance', metavar='NUM', type=int,
                        default=DEFAULT_Y_TOLERANCE,
                        help=f'Y-axis tolerance for text extraction (default: {DEFAULT_Y_TOLERANCE})')
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_arguments()
    
    # Validate date format
    try:
        datetime.strptime(args.date, "%d%m%Y")
    except ValueError:
        print(f"❌ Invalid date format '{args.date}'. Expected DDMMYYYY format.", file=sys.stderr)
        sys.exit(1)
    
    # Fetch PDF
    pdf_bytes = fetch_pdf_bytes(args.date, args.side, args.base_url)
    
    # Extract entries
    entries = extract_rows_from_bytes(pdf_bytes, args.advocate, args.y_tolerance)
    
    if not entries:
        print(f"❌ No entries found for '{args.advocate}'", file=sys.stderr)
    else:
        print(f"✅ Found {len(entries)} entries for '{args.advocate}'", file=sys.stderr)
    
    # Generate HTML
    html_out = generate_html(entries, args.advocate, args.date, args.side)
    
    # Output to stdout
    print(html_out)
    
    # Save to file
    try:
        with open(args.output_html, "w", encoding="utf-8") as fh:
            fh.write(html_out)
        print(f"✅ HTML also saved to {args.output_html}", file=sys.stderr)
    except IOError as e:
        print(f"❌ Failed to save HTML file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
