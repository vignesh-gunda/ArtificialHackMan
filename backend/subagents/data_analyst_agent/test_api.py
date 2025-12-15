#!/usr/bin/env python3
"""
Sample script to test the Data Analyst Agent API.
Run the API first: python -m uvicorn api:app --host 0.0.0.0 --port 8000
Then run this script in another terminal.
"""

import requests
import json
import sys
from pathlib import Path

API_BASE = "http://localhost:8000"


def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200


def test_analyze(csv_file_path: str, user_request: str = "Create a simple EDA dashboard"):
    """Test the main /analyze endpoint."""
    print(f"Testing /analyze with file: {csv_file_path}")
    print(f"Request: {user_request}\n")
    
    with open(csv_file_path, "rb") as f:
        files = {"file": f}
        data = {"user_request": user_request}
        response = requests.post(f"{API_BASE}/analyze", files=files, data=data)
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if result.get("success"):
        print("✓ Analysis successful!")
        print(f"Message: {result['message']}")
        
        if result.get("data"):
            print(f"HTML length: {len(result['data'].get('html', ''))} chars")
            print(f"CSS length: {len(result['data'].get('css', ''))} chars")
            print(f"Metadata:")
            metadata = result['data'].get('metadata', {})
            print(f"  - Validated request: {metadata.get('validated_request')}")
            print(f"  - Columns found: {len(metadata.get('validation_columns', []))}")
            print(f"  - Missing columns: {metadata.get('validation_missing_columns', [])}")
            print(f"  - Warnings: {metadata.get('validation_warnings', [])}")
            
            # Save HTML to file for inspection
            html_file = Path(csv_file_path).stem + "_dashboard.html"
            with open(html_file, "w") as f:
                f.write(result['data']['html'])
            print(f"\n✓ Dashboard saved to: {html_file}")
    else:
        print(f"✗ Analysis failed!")
        print(f"Error: {result.get('error')}")
    
    print()
    return result.get("success", False)


def create_sample_csv():
    """Create a sample CSV for testing."""
    csv_path = "sample_data.csv"
    if Path(csv_path).exists():
        return csv_path
    
    print(f"Creating sample CSV file: {csv_path}\n")
    
    sample_data = """name,age,salary,department,join_year
Alice,28,75000,Engineering,2020
Bob,34,85000,Engineering,2018
Charlie,45,120000,Management,2015
Diana,29,68000,Sales,2021
Eve,38,95000,Engineering,2019
Frank,52,130000,Management,2010
Grace,26,62000,Sales,2022
Henry,41,105000,Engineering,2017
Iris,33,78000,Marketing,2020
Jack,27,65000,Sales,2023"""
    
    with open(csv_path, "w") as f:
        f.write(sample_data)
    
    print(f"✓ Sample CSV created with 10 rows\n")
    return csv_path


if __name__ == "__main__":
    print("=" * 60)
    print("Data Analyst Agent API - Test Suite")
    print("=" * 60 + "\n")
    
    # Test 1: Health check
    if not test_health_check():
        print("✗ API is not running. Start it with:")
        print("  python -m uvicorn api:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Test 2: Create sample CSV and analyze
    csv_file = create_sample_csv()
    
    # Test basic analysis
    test_analyze(csv_file, "Create an EDA dashboard with salary analysis and department stats")
    
    # Test with different request
    test_analyze(csv_file, "Show salary distribution by department using charts")
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
