"""
Live API test suite with real data

This test suite was created with assistance from Claude AI (Anthropic).
Tests the API with the actual assignment data (54,553 ZIP codes, 303,864 health records).
"""

import pytest
import httpx
import subprocess
import sys
import time
import os

@pytest.fixture(scope="session")
def ensure_database():
    """Ensure database exists with real data"""
    if not os.path.exists("data.db"):
        print("\n🔄 Creating database with real data...")
        # Create database with real data
        result1 = subprocess.run([
            sys.executable, "csv_to_sqlite.py", "data.db", "data/zip_county.csv"
        ], capture_output=True, text=True)

        result2 = subprocess.run([
            sys.executable, "csv_to_sqlite.py", "data.db", "data/county_health_rankings.csv"
        ], capture_output=True, text=True)

        if result1.returncode != 0 or result2.returncode != 0:
            raise Exception("Failed to create database with real data")

        print("✅ Database created successfully!")
    return "data.db"

@pytest.fixture(scope="session")
def live_api_server(ensure_database):
    """Start live API server with real data"""
    print("\n🚀 Starting live API server...")

    # Start the server
    process = subprocess.Popen([
        sys.executable, "-c",
        "import uvicorn; from main import app; uvicorn.run(app, host='127.0.0.1', port=8004, log_level='error')"
    ])

    # Wait for server to start
    time.sleep(3)

    # Check if server is running
    max_retries = 5
    for i in range(max_retries):
        try:
            response = httpx.get("http://127.0.0.1:8004/", timeout=5.0)
            if response.status_code == 200:
                print("✅ Live API server started successfully!")
                break
        except Exception as e:
            if i == max_retries - 1:
                process.kill()
                raise Exception(f"Server failed to start: {e}")
            time.sleep(2)

    yield "http://127.0.0.1:8004"

    # Cleanup
    print("\n🔄 Stopping live API server...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

class TestLiveAPIWithRealData:
    """Test the live API with real assignment data"""

    def test_health_check(self, live_api_server):
        """Test API health check"""
        response = httpx.get(f"{live_api_server}/")
        assert response.status_code == 200
        assert response.json() == {"message": "County Health Data API is running"}

    def test_cambridge_ma_adult_obesity(self, live_api_server):
        """Test adult obesity data for Cambridge, MA (ZIP 02138)"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity"
        }, timeout=10.0)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have multiple years and potentially multiple counties

        # Verify response structure
        record = data[0]
        expected_fields = [
            "state", "county", "state_code", "county_code", "year_span",
            "measure_name", "measure_id", "numerator", "denominator",
            "raw_value", "confidence_interval_lower_bound",
            "confidence_interval_upper_bound", "data_release_year", "fipscode"
        ]

        for field in expected_fields:
            assert field in record

        # Should include Middlesex County data
        counties = [r["county"] for r in data]
        assert "Middlesex County" in counties

    def test_nyc_violent_crime(self, live_api_server):
        """Test violent crime data for NYC (ZIP 10001)"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "10001",
            "measure_name": "Violent crime rate"
        }, timeout=10.0)

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        # Should be New York County data
        assert all(r["county"] == "New York County" for r in data)
        assert all(r["state"] == "NY" for r in data)
        assert all(r["measure_name"] == "Violent crime rate" for r in data)

    def test_beverly_hills_data(self, live_api_server):
        """Test data for Beverly Hills, CA (ZIP 90210)"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "90210",
            "measure_name": "Adult obesity"
        }, timeout=10.0)

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        # Should be Los Angeles County data
        assert all(r["county"] == "Los Angeles County" for r in data)
        assert all(r["state"] == "CA" for r in data)

    def test_multiple_measures(self, live_api_server):
        """Test multiple different measures"""
        measures_to_test = [
            "Adult obesity",
            "Violent crime rate",
            "Unemployment",
            "Physical inactivity"
        ]

        for measure in measures_to_test:
            response = httpx.post(f"{live_api_server}/county_data", json={
                "zip": "02138",  # Cambridge, MA
                "measure_name": measure
            }, timeout=10.0)

            # Should either return data (200) or no data found (404)
            assert response.status_code in [200, 404]

            if response.status_code == 200:
                data = response.json()
                assert len(data) > 0
                assert all(r["measure_name"] == measure for r in data)

    def test_historical_data_spans(self, live_api_server):
        """Test that we get multiple years of data"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity"
        }, timeout=10.0)

        assert response.status_code == 200
        data = response.json()

        # Should have multiple years of data
        year_spans = {r["year_span"] for r in data}
        assert len(year_spans) > 1  # Multiple years

        # Verify we have data across different years
        years = []
        for record in data:
            if record["year_span"]:
                years.append(record["year_span"])

        assert len(set(years)) > 1  # Multiple distinct years

    def test_middlesex_county_across_states(self, live_api_server):
        """Test that ZIP 02138 returns Middlesex County data from multiple states"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity"
        }, timeout=10.0)

        assert response.status_code == 200
        data = response.json()

        # Get unique states with Middlesex County
        states_with_middlesex = {r["state"] for r in data if r["county"] == "Middlesex County"}

        # Should have multiple states (MA, CT, NJ, VA all have Middlesex County)
        assert len(states_with_middlesex) > 1
        assert "MA" in states_with_middlesex  # Massachusetts should be included

class TestLiveAPIValidation:
    """Test validation behaviors with the live API"""

    def test_teapot_behavior(self, live_api_server):
        """Test HTTP 418 teapot behavior"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity",
            "coffee": "teapot"
        })

        assert response.status_code == 418
        assert response.json() == {"detail": {"error": "I'm a teapot"}}

    def test_missing_fields(self, live_api_server):
        """Test HTTP 400 for missing required fields"""
        response = httpx.post(f"{live_api_server}/county_data", json={})
        assert response.status_code == 400
        assert "Missing required fields" in response.json()["detail"]

    def test_invalid_zip_format(self, live_api_server):
        """Test HTTP 400 for invalid ZIP format"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "123",
            "measure_name": "Adult obesity"
        })
        assert response.status_code == 400
        assert "ZIP code must be exactly 5 digits" in response.json()["detail"]

    def test_invalid_measure_name(self, live_api_server):
        """Test HTTP 404 for invalid measure name"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Invalid Measure Name"
        })
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_zip_not_in_database(self, live_api_server):
        """Test HTTP 404 for ZIP not in database"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "99999",  # This ZIP shouldn't exist
            "measure_name": "Adult obesity"
        })
        assert response.status_code == 404
        assert "ZIP code 99999 not found" in response.json()["detail"]

class TestLiveAPIPerformance:
    """Test API performance and edge cases"""

    def test_large_result_set(self, live_api_server):
        """Test handling of queries that return many records"""
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "02138",  # This ZIP returns many records across multiple states/years
            "measure_name": "Adult obesity"
        }, timeout=15.0)  # Longer timeout for larger queries

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 10  # Should return many records

        # Verify all records are for the correct measure
        assert all(r["measure_name"] == "Adult obesity" for r in data)

    def test_response_time(self, live_api_server):
        """Test that API responds within reasonable time"""
        import time

        start_time = time.time()
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "10001",
            "measure_name": "Violent crime rate"
        })
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 5.0  # Should respond within 5 seconds

class TestSQLInjectionWithRealData:
    """Test SQL injection protection with real database"""

    def test_sql_injection_zip_parameter(self, live_api_server):
        """Test SQL injection in ZIP parameter"""
        malicious_zip = "02138'; DROP TABLE county_health_rankings; --"

        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": malicious_zip,
            "measure_name": "Adult obesity"
        })

        # Should fail validation (not 5 digits)
        assert response.status_code == 400

        # Verify database is still intact by making a valid request
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity"
        })
        assert response.status_code == 200

    def test_sql_injection_measure_parameter(self, live_api_server):
        """Test SQL injection in measure_name parameter"""
        malicious_measure = "Adult obesity'; DROP TABLE zip_county; --"

        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "02138",
            "measure_name": malicious_measure
        })

        # Should fail validation (not in whitelist)
        assert response.status_code == 404

        # Verify database is still intact
        response = httpx.post(f"{live_api_server}/county_data", json={
            "zip": "02138",
            "measure_name": "Adult obesity"
        })
        assert response.status_code == 200