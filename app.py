#!/usr/bin/env python3
"""
High Court Cause List API
Flask application that provides API access to court cause list data.
"""

import subprocess
import fitz  # PyMuPDF
import sys
import os
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, Unauthorized

app = Flask(__name__)

# Configuration
API_KEY = os.environ.get('API_KEY', 'your-secret-api-key-here')
DEFAULT_BASE_URL = "https://www.calcuttahighcourt.gov.in"
DEFAULT_Y_TOLERANCE = 3

SIDE_INFO = {
    "Original Side": ("OS", "clo"),
    "Appellate Side": ("AS", "cla"),
}

def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.json.get('api_key') if request.json else None

        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide API key in X-API-Key header or api_key field'
            }), 401

        if api_key != API_KEY:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401

        return f(*args, **kwargs)
    return decorated_function

def fetch_pdf_bytes(date_str, side, base_url=DEFAULT_BASE_URL):
    """Fetch PDF bytes from the court website."""
    if side not in SIDE_INFO:
        raise ValueError(f"Invalid side '{side}'. Must be one of: {list(SIDE_INFO.keys())}")

    code, prefix = SIDE_INFO[side]
    url = f"{base_url}/downloads/old_cause_lists/{code}/{prefix}{date_str}.pdf"

    try:
        data = subprocess.check_output(
            ["curl", "--insecure", "-L", url],
            stderr=subprocess.DEVNULL,
            timeout=30
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to download PDF: {e}")
    except subprocess.TimeoutExpired:
        raise Exception("PDF download timeout")

    if not data.startswith(b"%PDF"):
        raise Exception("Unable to fetch cause_list details due to weekends or failed to fetch cause list")

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
                top = y0 - tol
                bottom = y1 + height + tol

                band = []
                for bx0, by0, bx1, by1, btext in blocks:
                    midy = (by0 + by1) / 2
                    if top <= midy <= bottom:
                        band.append((bx0, by0, by1, btext))

                band.sort(key=lambda b: b[0])
                combined = " ".join(b[3].replace("\n", " ").strip() for b in band).lower()
                if all(tok in combined for tok in tokens):
                    lines = []
                    for _, _, _, blk in band:
                        for ln in blk.splitlines():
                            ln = ln.strip()
                            if ln:
                                lines.append(ln)
                    key = (page.number + 1, tuple(lines))
                    if key not in seen:
                        seen.add(key)
                        out.append((page.number + 1, lines))

    doc.close()
    return out

def format_output_entries(entries):
    """Format extracted entries for JSON output."""
    output = []
    for page_num, lines in entries:
        # Join all lines into a single string for each case
        case_text = "\n".join(lines)
        output.append(case_text)
    return output

def validate_date(date_str):
    """Validate date format DDMMYYYY."""
    try:
        datetime.strptime(date_str, "%d%m%Y")
        return True
    except ValueError:
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'High Court Cause List API'})

@app.route('/fetch-cause-list', methods=['POST'])
@require_api_key
def fetch_cause_list():
    """
    Fetch cause list data for a specific advocate.

    Expected JSON payload:
    {
        "date": "23052025",
        "side": "Appellate Side",
        "advocate": "Syed Nurul Arefin",
        "base_url": "https://www.calcuttahighcourt.gov.in" (optional)
    }
    """
    try:
        # Validate request
        if not request.json:
            raise BadRequest("JSON payload required")

        data = request.json

        # Required fields
        date = data.get('date')
        side = data.get('side')
        advocate = data.get('advocate')

        if not all([date, side, advocate]):
            return jsonify({
                'error': 'Missing required fields',
                'message': 'date, side, and advocate are required fields'
            }), 400

        # Optional fields
        base_url = data.get('base_url', DEFAULT_BASE_URL)

        # Validate date format
        if not validate_date(date):
            return jsonify({
                'error': 'Invalid date format',
                'message': 'Date must be in DDMMYYYY format (e.g., 23052025)'
            }), 400

        # Validate side
        if side not in SIDE_INFO:
            return jsonify({
                'error': 'Invalid side',
                'message': f'Side must be one of: {list(SIDE_INFO.keys())}'
            }), 400

        # Fetch and process data
        try:
            pdf_bytes = fetch_pdf_bytes(date, side, base_url)
            entries = extract_rows_from_bytes(pdf_bytes, advocate)

            # Format response
            response = {
                "Date": date,
                "Side": side,
                "Advocate": advocate,
                "Court_URL": base_url,
                "Output": format_output_entries(entries)
            }

            return jsonify(response)

        except Exception as e:
            error_message = str(e)

            # Check if it's a PDF fetch failure (weekends/holidays)
            if "Unable to fetch cause_list details due to weekends or failed to fetch cause list" in error_message:
                # Return successful response with error message in Output
                response = {
                    "Date": date,
                    "Side": side,
                    "Advocate": advocate,
                    "Court_URL": base_url,
                    "Output": ["Unable to fetch cause_list details due to weekends or failed to fetch cause list"]
                }
                return jsonify(response)
            else:
                # Return error response for other types of failures
                return jsonify({
                    'error': 'Processing failed',
                    'message': error_message
                }), 500

    except BadRequest as e:
        return jsonify({
            'error': 'Bad request',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The requested method is not allowed for this endpoint'
    }), 405

if __name__ == '__main__':
    # Check if API key is set
    if API_KEY == 'your-secret-api-key-here':
        print("⚠️  Warning: Using default API key. Set API_KEY environment variable for production.")

    # Run the app
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))

    print(f"🚀 Starting High Court Cause List API on port {port}")
    print(f"📋 API Key: {'Set' if API_KEY != 'your-secret-api-key-here' else 'Using default (change for production)'}")

    app.run(host='0.0.0.0', port=port, debug=debug_mode)
