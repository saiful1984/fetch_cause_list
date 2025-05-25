# High Court Cause List API

A Flask API that fetches and searches High Court cause lists for specific advocates.

## Features

- 🔐 API key authentication
- 📋 Fetch cause lists from Calcutta High Court
- 🔍 Search for specific advocate names
- 📄 PDF processing and text extraction
- 🌐 RESTful JSON API
- 🗓️ Graceful handling of weekends/holidays when court data is unavailable

## Installation

1. Clone or download the project files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file and set your API key
   ```

## Configuration

Set the following environment variables:

- `API_KEY`: Your secret API key for authentication
- `FLASK_DEBUG`: Set to `True` for development (default: `False`)
- `PORT`: Port to run the server on (default: `5000`)

## Usage

### Start the server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

#### Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "High Court Cause List API"
}
```

#### Fetch Cause List
```
POST /fetch-cause-list
```

Headers:
```
Content-Type: application/json
X-API-Key: your-api-key-here
```

Request body:
```json
{
  "date": "23052025",
  "side": "Appellate Side",
  "advocate": "Syed Nurul Arefin",
  "base_url": "https://www.calcuttahighcourt.gov.in"
}
```

Response (successful case):
```json
{
  "Date": "23052025",
  "Side": "Appellate Side",
  "Advocate": "Syed Nurul Arefin",
  "Court_URL": "https://www.calcuttahighcourt.gov.in",
  "Output": [
    "72\nFMAT/330/2023\nSRI KESHOV PRASAD SHAW\nVS\nTOPSIA ANJUMAN HIYAYATUL ISLAM AND ORS.\nIA NO: CAN/1/2023, CAN/2/2024\nMR. SYED NURUL\nAREFIN",
    "132\nFAT/401/2019\nBHARATI SAHA\nVS\nARUNDHUTI SEN & ORS\nSYED NURUL AREFIN"
  ]
}
```

Response (weekend/unavailable date):
```json
{
  "Date": "24052025",
  "Side": "Appellate Side",
  "Advocate": "Syed Nurul Arefin",
  "Court_URL": "https://www.calcuttahighcourt.gov.in",
  "Output": [
    "Unable to fetch cause_list details due to weekends or failed to fetch cause list"
  ]
}
```

### Parameters

- `date` (required): Date in DDMMYYYY format (e.g., "23052025")
- `side` (required): Either "Original Side" or "Appellate Side"
- `advocate` (required): Full name of the advocate to search for
- `base_url` (optional): Base URL of the court website (defaults to Calcutta High Court)

### Weekend/Holiday Handling

When court data is unavailable (weekends, holidays, or server issues), the API will still return a successful response (HTTP 200) but with a special message in the Output field:

```json
{
  "Date": "24052025",
  "Side": "Appellate Side",
  "Advocate": "Syed Nurul Arefin",
  "Court_URL": "https://www.calcuttahighcourt.gov.in",
  "Output": [
    "Unable to fetch cause_list details due to weekends or failed to fetch cause list"
  ]
}
```

This ensures consistent API behavior and makes it easy for automation tools (like n8n) to handle both successful and unavailable scenarios.

### Authentication

The API requires authentication via API key. You can provide the API key in two ways:

1. **Header** (recommended):
   ```
   X-API-Key: your-api-key-here
   ```

2. **JSON body**:
   ```json
   {
     "api_key": "your-api-key-here",
     "date": "23052025",
     ...
   }
   ```

## Example Usage

### Using curl

```bash
curl -X POST http://localhost:5000/fetch-cause-list \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "date": "23052025",
    "side": "Appellate Side",
    "advocate": "Syed Nurul Arefin"
  }'
```

### Using Python requests

```python
import requests

url = "http://localhost:5000/fetch-cause-list"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your-api-key-here"
}
data = {
    "date": "23052025",
    "side": "Appellate Side",
    "advocate": "Syed Nurul Arefin"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid input parameters
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Endpoint not found
- `405 Method Not Allowed`: Wrong HTTP method
- `500 Internal Server Error`: Server processing error

## Dependencies

- Flask: Web framework
- PyMuPDF: PDF processing
- subprocess: For downloading PDFs via curl

## Security Notes

- Always use a strong, unique API key in production
- Consider using HTTPS in production environments
- The API key should be kept secret and not committed to version control
