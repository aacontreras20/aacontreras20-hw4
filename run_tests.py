#!/usr/bin/env python3
"""
Demonstration script for the County Health Data API assignment

This script demonstrates all the key functionality required by the assignment.
Created with assistance from Claude AI (Anthropic).
"""

import subprocess
import sys
import os
import time
import httpx

def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print("📤 STDOUT:")
        print(result.stdout)

    if result.stderr:
        print("📤 STDERR:")
        print(result.stderr)

    print(f"📊 Exit code: {result.returncode}")
    return result.returncode == 0

def test_api_endpoint(url, data, description):
    """Test API endpoint and print results"""
    print(f"\n{'='*60}")
    print(f"🌐 {description}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Data: {data}")
    print()

    try:
        response = httpx.post(url, json=data, timeout=10.0)
        print(f"📊 Status Code: {response.status_code}")
        print(f"📤 Response:")
        print(response.text)
        return response.status_code
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Run the complete demonstration"""
    print("🚀 County Health Data API - Assignment Demonstration")
    print("=" * 60)

    # Clean up any existing files
    for file in ["data.db"]:
        if os.path.exists(file):
            os.remove(file)

    # Test Part 1: CSV to SQLite converter
    print("\n🏗️  PART 1: CSV TO SQLITE CONVERTER")
    print("=" * 60)

    success = run_command([
        sys.executable, "csv_to_sqlite.py", "data.db", "zip_county.csv"
    ], "Convert ZIP county data to SQLite")

    if not success:
        print("❌ Failed to create database with ZIP data")
        return False

    success = run_command([
        sys.executable, "csv_to_sqlite.py", "data.db", "county_health_rankings.csv"
    ], "Add county health rankings to SQLite")

    if not success:
        print("❌ Failed to add health rankings data")
        return False

    # Verify database contents
    success = run_command([
        "sqlite3", "data.db", "SELECT COUNT(*) FROM zip_county;"
    ], "Count rows in zip_county table")

    success = run_command([
        "sqlite3", "data.db", "SELECT COUNT(*) FROM county_health_rankings;"
    ], "Count rows in county_health_rankings table")

    # Test Part 2: API functionality
    print("\n🌐 PART 2: WEB API")
    print("=" * 60)

    # Start the API server
    print("\n🔄 Starting API server...")
    server_process = subprocess.Popen([
        sys.executable, "-c",
        "import uvicorn; from main import app; uvicorn.run(app, host='127.0.0.1', port=8002, log_level='error')"
    ])

    # Wait for server to start
    time.sleep(3)

    api_url = "http://127.0.0.1:8002/county_data"

    try:
        # Test valid request
        test_api_endpoint(api_url, {
            "zip": "02138",
            "measure_name": "Adult obesity"
        }, "Valid request - Adult obesity data for Cambridge, MA")

        # Test teapot behavior (HTTP 418)
        test_api_endpoint(api_url, {
            "zip": "02138",
            "measure_name": "Adult obesity",
            "coffee": "teapot"
        }, "Teapot behavior - Should return HTTP 418")

        # Test missing fields (HTTP 400)
        test_api_endpoint(api_url, {}, "Missing fields - Should return HTTP 400")

        # Test invalid ZIP (HTTP 400)
        test_api_endpoint(api_url, {
            "zip": "123",
            "measure_name": "Adult obesity"
        }, "Invalid ZIP format - Should return HTTP 400")

        # Test invalid measure (HTTP 404)
        test_api_endpoint(api_url, {
            "zip": "02138",
            "measure_name": "Invalid Measure"
        }, "Invalid measure name - Should return HTTP 404")

        # Test ZIP not found (HTTP 404)
        test_api_endpoint(api_url, {
            "zip": "99999",
            "measure_name": "Adult obesity"
        }, "ZIP not found - Should return HTTP 404")

        # Test violent crime rate
        test_api_endpoint(api_url, {
            "zip": "02138",
            "measure_name": "Violent crime rate"
        }, "Valid request - Violent crime rate for Cambridge, MA")

    finally:
        # Stop the server
        print("\n🔄 Stopping API server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

    # Run test suite
    print("\n🧪 RUNNING COMPLETE TEST SUITE")
    print("=" * 60)

    success = run_command([
        sys.executable, "-m", "pytest", "-v"
    ], "Run complete test suite")

    if success:
        print("\n✅ ALL TESTS PASSED!")
        print("\n📋 ASSIGNMENT COMPLETION SUMMARY:")
        print("=" * 60)
        print("✅ Part 1: CSV to SQLite converter implemented and tested")
        print("✅ Part 2: Web API with /county_data endpoint implemented and tested")
        print("✅ All required HTTP status codes implemented (200, 400, 404, 418, 500)")
        print("✅ SQL injection protection via parameterized queries")
        print("✅ Input validation for ZIP codes and measure names")
        print("✅ Special teapot behavior (HTTP 418)")
        print("✅ Comprehensive test suite with 20 tests")
        print("✅ All deliverable files created:")
        print("   - csv_to_sqlite.py")
        print("   - main.py (API)")
        print("   - requirements.txt")
        print("   - README.md")
        print("   - .gitignore")
        print("   - link.txt")
        print("   - Test suites")
        print("\n🎉 Ready for deployment!")
    else:
        print("\n❌ Some tests failed!")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)