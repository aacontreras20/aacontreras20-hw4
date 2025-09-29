"""
Simple API test suite using httpx directly

This test suite was created with assistance from Claude AI (Anthropic).
"""

import pytest
import sqlite3
import tempfile
import os
import httpx
import csv
import time
import subprocess
import sys
import signal

@pytest.fixture(scope="session")
def test_db():
    """Create a test database with sample data"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    # Create database with test data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create zip_county table
    cursor.execute("""
        CREATE TABLE zip_county (
            zip TEXT, default_state TEXT, county TEXT, county_state TEXT,
            state_abbreviation TEXT, county_code TEXT, zip_pop TEXT,
            zip_pop_in_county TEXT, n_counties TEXT, default_city TEXT
        )
    """)

    # Insert test zip data
    zip_data = [
        ('02138', 'MA', 'Middlesex County', 'MA', 'MA', '017', '29000', '29000', '1', 'Cambridge'),
        ('02139', 'MA', 'Middlesex County', 'MA', 'MA', '017', '15000', '15000', '1', 'Cambridge'),
        ('10001', 'NY', 'New York County', 'NY', 'NY', '061', '21000', '21000', '1', 'New York'),
        ('90210', 'CA', 'Los Angeles County', 'CA', 'CA', '037', '25000', '25000', '1', 'Beverly Hills')
    ]
    cursor.executemany("""
        INSERT INTO zip_county VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, zip_data)

    # Create county_health_rankings table
    cursor.execute("""
        CREATE TABLE county_health_rankings (
            state TEXT, county TEXT, state_code TEXT, county_code TEXT,
            year_span TEXT, measure_name TEXT, measure_id TEXT,
            numerator TEXT, denominator TEXT, raw_value TEXT,
            confidence_interval_lower_bound TEXT, confidence_interval_upper_bound TEXT,
            data_release_year TEXT, fipscode TEXT
        )
    """)

    # Insert test health data
    health_data = [
        ('MA', 'Middlesex County', '25', '017', '2020-2022', 'Adult obesity', '11',
         '60771.02', '263078', '0.23', '0.22', '0.24', '2023', '25017'),
        ('MA', 'Middlesex County', '25', '017', '2020-2022', 'Violent crime rate', '43',
         '850', '263078', '3.2', '3.0', '3.4', '2023', '25017'),
        ('NY', 'New York County', '36', '061', '2020-2022', 'Adult obesity', '11',
         '45000', '180000', '0.25', '0.24', '0.26', '2023', '36061'),
        ('CA', 'Los Angeles County', '06', '037', '2020-2022', 'Adult obesity', '11',
         '2500000', '10000000', '0.25', '0.24', '0.26', '2023', '06037'),
        ('CA', 'Los Angeles County', '06', '037', '2020-2022', 'Unemployment', '23',
         '120000', '2800000', '4.3', '4.1', '4.5', '2023', '06037')
    ]
    cursor.executemany("""
        INSERT INTO county_health_rankings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, health_data)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass

@pytest.fixture(scope="session")
def api_server(test_db):
    """Start API server for testing"""
    # Copy test database to data.db
    import shutil
    shutil.copy2(test_db, "data.db")

    # Start the server
    process = subprocess.Popen([
        sys.executable, "-c",
        "import uvicorn; from main import app; uvicorn.run(app, host='127.0.0.1', port=8001, log_level='error')"
    ])

    # Wait for server to start
    time.sleep(2)

    # Check if server is running
    try:
        response = httpx.get("http://127.0.0.1:8001/")
        if response.status_code != 200:
            raise Exception("Server failed to start")
    except Exception as e:
        process.kill()
        raise e

    yield "http://127.0.0.1:8001"

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

    # Remove test data.db
    try:
        os.unlink("data.db")
    except OSError:
        pass

class TestAPIEndpoints:

    def test_root_endpoint(self, api_server):
        """Test the root health check endpoint"""
        response = httpx.get(f"{api_server}/")
        assert response.status_code == 200
        assert response.json() == {"message": "County Health Data API is running"}

    def test_valid_request_adult_obesity(self, api_server):
        """Test valid request for adult obesity data"""
        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity"
        })

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

        record = data[0]
        assert record["state"] == "MA"
        assert record["county"] == "Middlesex County"
        assert record["measure_name"] == "Adult obesity"
        assert record["raw_value"] == "0.23"

    def test_teapot_behavior(self, api_server):
        """Test HTTP 418 teapot behavior"""
        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity",
            "coffee": "teapot"
        })

        assert response.status_code == 418
        assert response.json() == {"detail": {"error": "I'm a teapot"}}

    def test_missing_required_fields(self, api_server):
        """Test HTTP 400 for missing required fields"""
        response = httpx.post(f"{api_server}/county_data", json={})
        assert response.status_code == 400
        assert "Missing required fields" in response.json()["detail"]

    def test_invalid_zip_format(self, api_server):
        """Test HTTP 400 for invalid ZIP code format"""
        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "123",
            "measure_name": "Adult obesity"
        })
        assert response.status_code == 400
        assert "ZIP code must be exactly 5 digits" in response.json()["detail"]

    def test_invalid_measure_name(self, api_server):
        """Test HTTP 404 for invalid measure name"""
        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Invalid Measure"
        })

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_zip_not_found(self, api_server):
        """Test HTTP 404 for ZIP code not in database"""
        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "99999",
            "measure_name": "Adult obesity"
        })

        assert response.status_code == 404
        assert "ZIP code 99999 not found" in response.json()["detail"]

    def test_violent_crime_rate(self, api_server):
        """Test valid request for violent crime rate"""
        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Violent crime rate"
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["measure_name"] == "Violent crime rate"
        assert data[0]["raw_value"] == "3.2"

    def test_json_response_structure(self, api_server):
        """Test that JSON response has correct structure"""
        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity"
        })

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        record = data[0]
        expected_fields = [
            "state", "county", "state_code", "county_code", "year_span",
            "measure_name", "measure_id", "numerator", "denominator",
            "raw_value", "confidence_interval_lower_bound",
            "confidence_interval_upper_bound", "data_release_year", "fipscode"
        ]

        for field in expected_fields:
            assert field in record

class TestSQLInjectionProtection:
    """Test SQL injection protection"""

    def test_sql_injection_in_zip(self, api_server):
        """Test SQL injection attempts in zip parameter"""
        malicious_zip = "02138'; DROP TABLE county_health_rankings; --"

        response = httpx.post(f"{api_server}/county_data", json={
            "zip": malicious_zip,
            "measure_name": "Adult obesity"
        })

        # Should fail validation (not 5 digits) rather than execute SQL
        assert response.status_code == 400

        # Verify tables still exist by making a valid request
        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity"
        })
        assert response.status_code == 200

    def test_sql_injection_in_measure_name(self, api_server):
        """Test SQL injection attempts in measure_name parameter"""
        malicious_measure = "Adult obesity'; DROP TABLE zip_county; --"

        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "02138",
            "measure_name": malicious_measure
        })

        # Should fail validation (not in valid measures list)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

        # Verify tables still exist
        response = httpx.post(f"{api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity"
        })
        assert response.status_code == 200