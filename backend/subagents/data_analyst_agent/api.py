import tempfile
import sys
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
import pathlib
from dotenv import load_dotenv

# Load environment variables
env_path = pathlib.Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add parent directory to sys.path for imports
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from data_analyst_agent.graph import run_data_analyst_agent

app = FastAPI(
    title="Data Analyst Agent API",
    description="API for generating interactive data analysis dashboards from CSV/Excel files",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Data Analyst Agent API"
    }


@app.post("/analyze", response_class=HTMLResponse)
async def analyze_dataset(
    file: UploadFile = File(..., description="CSV or Excel file"),
    user_request: str = Form(..., description="What analysis do you want?"),
):
    """
    Upload a CSV/Excel file and generate an interactive dashboard.
    
    Returns: Pure HTML dashboard
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    valid_extensions = (".csv", ".xls", ".xlsx")
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Supported: CSV, XLS, XLSX. Got: {file.filename}"
        )
    
    if not user_request or not user_request.strip():
        raise HTTPException(status_code=400, detail="user_request is required")
    
    try:
        # Save uploaded file to temporary location
        suffix = "." + file.filename.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp.flush()
            tmp_path = tmp.name
        
        # Run the data analyst agent
        final_state = run_data_analyst_agent(tmp_path, user_request.strip())
        
        # Check for errors
        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])
        
        # Extract HTML content
        html_content = final_state.get("html_content", "")
        if not html_content:
            raise HTTPException(status_code=500, detail="The agent did not produce HTML output")
        
        # Return pure HTML
        return html_content
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-analyze", response_class=HTMLResponse)
async def batch_analyze(
    file: UploadFile = File(...),
    requests: str = Form(..., description="Comma-separated list of analysis requests"),
):
    """
    Upload one file and generate multiple dashboards with different requests.
    Returns combined HTML with all dashboards.
    
    - **file**: CSV or Excel file
    - **requests**: Comma-separated analysis requests
    """
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not requests or not requests.strip():
        raise HTTPException(status_code=400, detail="At least one request is required")
    
    valid_extensions = (".csv", ".xls", ".xlsx")
    if not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Supported: CSV, XLS, XLSX"
        )
    
    try:
        # Save uploaded file
        suffix = "." + file.filename.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp.flush()
            tmp_path = tmp.name
        
        # Process each request
        request_list = [r.strip() for r in requests.split(",") if r.strip()]
        dashboards = []
        
        for idx, req in enumerate(request_list):
            final_state = run_data_analyst_agent(tmp_path, req)
            
            html_content = final_state.get("html_content", "")
            if html_content and not final_state.get("error"):
                dashboards.append(html_content)
        
        if not dashboards:
            raise HTTPException(status_code=500, detail="No dashboards were generated")
        
        # Combine all dashboards with navigation
        combined_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Analysis Results - {file.filename}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        .nav-tabs {{
            display: flex;
            border-bottom: 2px solid #e0e0e0;
            background-color: #fafafa;
            flex-wrap: wrap;
        }}
        .nav-tab {{
            padding: 12px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
        }}
        .nav-tab:hover {{
            background-color: #f0f0f0;
        }}
        .nav-tab.active {{
            color: #667eea;
            border-bottom-color: #667eea;
        }}
        .content {{
            padding: 20px;
        }}
        .dashboard {{
            display: none;
        }}
        .dashboard.active {{
            display: block;
        }}
        .dashboard iframe {{
            width: 100%;
            border: none;
            background: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Data Analysis Dashboard</h1>
            <p>File: {file.filename} | Generated Analyses: {len(request_list)}</p>
        </div>
        
        <div class="nav-tabs">
"""
        
        for idx, req in enumerate(request_list):
            active = "active" if idx == 0 else ""
            combined_html += f'            <button class="nav-tab {active}" onclick="showTab({idx})">{idx + 1}. {req[:40]}...</button>\n'
        
        combined_html += """        </div>
        
        <div class="content">
"""
        
        for idx, dashboard_html in enumerate(dashboards):
            active = "active" if idx == 0 else ""
            combined_html += f'            <div class="dashboard {active}" id="tab-{idx}">\n'
            combined_html += dashboard_html
            combined_html += '            </div>\n'
        
        combined_html += """        </div>
    </div>
    
    <script>
        function showTab(index) {
            // Hide all dashboards
            const dashboards = document.querySelectorAll('.dashboard');
            dashboards.forEach(d => d.classList.remove('active'));
            
            // Hide all tabs
            const tabs = document.querySelectorAll('.nav-tab');
            tabs.forEach(t => t.classList.remove('active'));
            
            // Show selected dashboard and tab
            document.getElementById('tab-' + index).classList.add('active');
            tabs[index].classList.add('active');
        }
    </script>
</body>
</html>"""
        
        return combined_html
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
