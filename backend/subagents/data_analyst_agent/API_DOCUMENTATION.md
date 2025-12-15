# Data Analyst Agent API

## Overview
FastAPI-based REST API for the Data Analyst Agent that generates interactive HTML dashboards from CSV/Excel files.

## Features
- **File Upload Support**: Accept CSV, XLS, and XLSX files
- **Intelligent Column Validation**: Automatic validation and rewriting of user requests to match dataset columns
- **Multi-format Output**: Returns HTML, CSS, and JSON data
- **Batch Analysis**: Support for analyzing the same dataset with multiple requests
- **Error Handling**: Detailed error messages and validation warnings

## API Endpoints

### 1. Health Check
```
GET /health
```
Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "Data Analyst Agent API"
}
```

---

### 2. Analyze Dataset
```
POST /analyze
```
Upload a file and generate an interactive dashboard.

**Parameters:**
- `file` (required): CSV or Excel file (multipart/form-data)
- `user_request` (required): Description of the analysis needed (string)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@sample_data.csv" \
  -F "user_request=Create an EDA dashboard with salary analysis"
```

**Response:**
```json
{
  "success": true,
  "message": "Dashboard generated successfully",
  "data": {
    "html": "<html>...</html>",
    "css": "body { ... }",
    "json": {
      "status": "html_dashboard_generated"
    },
    "metadata": {
      "file_name": "sample_data.csv",
      "validated_request": "Create an EDA dashboard with salary statistics",
      "validation_columns": ["name", "age", "salary", "department", "join_year"],
      "validation_missing_columns": [],
      "validation_warnings": [],
      "logs": [...]
    }
  }
}
```

---

### 3. Batch Analyze
```
POST /batch-analyze
```
Upload one file and generate multiple dashboards with different requests.

**Parameters:**
- `file` (required): CSV or Excel file
- `requests` (required): Comma-separated list of analysis requests

**Example Request:**
```bash
curl -X POST "http://localhost:8000/batch-analyze" \
  -F "file=@sample_data.csv" \
  -F "requests=EDA dashboard, salary analysis by department, employee statistics"
```

**Response:**
```json
{
  "success": true,
  "file_name": "sample_data.csv",
  "total_requests": 3,
  "results": [
    {
      "index": 0,
      "request": "EDA dashboard",
      "success": true,
      "html": "<html>...</html>",
      "css": "...",
      "json": {...},
      "error": null
    },
    ...
  ]
}
```

---

## Running the API

### Prerequisites
```bash
pip install -r requirements.txt
```

### Start the API
```bash
# Development mode (with auto-reload)
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Production mode
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **Local**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

---

## Testing

Run the test suite:
```bash
python test_api.py
```

This script will:
1. Test the health endpoint
2. Create a sample CSV file
3. Run analysis with different user requests
4. Save the generated dashboard HTML

---

## Response Structure

All successful responses follow this structure:

```json
{
  "success": boolean,
  "message": "string",
  "data": {
    "html": "string (full HTML dashboard)",
    "css": "string (extracted CSS)",
    "json": "object (analysis data)",
    "metadata": {
      "file_name": "string",
      "validated_request": "string",
      "validation_columns": ["string"],
      "validation_missing_columns": ["string"],
      "validation_warnings": ["string"],
      "logs": ["string"]
    }
  },
  "error": "string or null"
}
```

---

## Error Handling

The API returns detailed error messages:

```json
{
  "success": false,
  "message": "Agent execution failed",
  "data": null,
  "error": "Invalid request. These columns do not exist: ['nonexistent_col']"
}
```

Common error scenarios:
- Invalid file type: 400 Bad Request
- Missing parameters: 400 Bad Request
- File read errors: 400 Bad Request
- Agent execution failures: 200 OK with success=false

---

## Integration Example

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    files={"file": open("data.csv", "rb")},
    data={"user_request": "Create an EDA dashboard"}
)

result = response.json()
if result["success"]:
    html = result["data"]["html"]
    # Use the HTML dashboard
```

### cURL
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@data.csv" \
  -F "user_request=Create an EDA dashboard" | jq '.data.html' > dashboard.html
```

### JavaScript/TypeScript
```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("user_request", "Create an EDA dashboard");

const response = await fetch("http://localhost:8000/analyze", {
  method: "POST",
  body: formData
});

const result = await response.json();
if (result.success) {
  document.getElementById("dashboard").innerHTML = result.data.html;
}
```

---

## Performance Considerations

- File size: Tested with files up to 10MB
- Processing time: Depends on LLM response time (typically 10-30 seconds)
- Concurrent requests: Use multiple worker processes for production
- Memory: Temporary files are cleaned up after processing

---

## Architecture

The API integrates with:
1. **Validator Agent**: Validates user requests against dataset columns
2. **Data Analyst Agent**: Generates Python code and executes analysis
3. **Sandbox Runner**: Safely executes generated code
4. **FastAPI**: Web framework for REST API

Flow:
```
File Upload → Validator Agent → Code Generator → Sandbox Execution → Response
```
