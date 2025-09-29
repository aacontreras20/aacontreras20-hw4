"""
Test suite for csv_to_sqlite.py

This test suite was created with assistance from Claude AI (Anthropic).
"""

import pytest
import sqlite3
import os
import tempfile
import csv
from pathlib import Path
import subprocess
import sys

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def sample_csv(temp_dir):
    """Create a sample CSV file for testing"""
    csv_path = os.path.join(temp_dir, "test_data.csv")
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'name', 'value'])
        writer.writerow(['1', 'test1', '10.5'])
        writer.writerow(['2', 'test2', '20.3'])
        writer.writerow(['3', 'test3', '30.1'])
    return csv_path

@pytest.fixture
def empty_csv(temp_dir):
    """Create an empty CSV file for testing"""
    csv_path = os.path.join(temp_dir, "empty.csv")
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['col1', 'col2'])
    return csv_path

def run_csv_to_sqlite(db_path, csv_path):
    """Run the csv_to_sqlite.py script and return the result"""
    result = subprocess.run([
        sys.executable, 'csv_to_sqlite.py', db_path, csv_path
    ], capture_output=True, text=True)
    return result

class TestCSVToSQLite:

    def test_successful_import(self, temp_dir, sample_csv):
        """Test successful CSV import"""
        db_path = os.path.join(temp_dir, "test.db")

        result = run_csv_to_sqlite(db_path, sample_csv)

        assert result.returncode == 0
        assert "Successfully imported 3 rows into table 'test_data'" in result.stdout
        assert os.path.exists(db_path)

        # Verify database contents
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='test_data'")
        schema = cursor.fetchone()[0]
        assert "id TEXT" in schema
        assert "name TEXT" in schema
        assert "value TEXT" in schema

        # Check row count
        cursor.execute("SELECT COUNT(*) FROM test_data")
        count = cursor.fetchone()[0]
        assert count == 3

        # Check specific data
        cursor.execute("SELECT * FROM test_data WHERE id = '1'")
        row = cursor.fetchone()
        assert row == ('1', 'test1', '10.5')

        conn.close()

    def test_table_recreation(self, temp_dir, sample_csv):
        """Test that tables are dropped and recreated"""
        db_path = os.path.join(temp_dir, "test.db")

        # First import
        result1 = run_csv_to_sqlite(db_path, sample_csv)
        assert result1.returncode == 0

        # Second import should recreate table
        result2 = run_csv_to_sqlite(db_path, sample_csv)
        assert result2.returncode == 0

        # Verify still only 3 rows (not 6)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_data")
        count = cursor.fetchone()[0]
        assert count == 3
        conn.close()

    def test_empty_csv(self, temp_dir, empty_csv):
        """Test handling of CSV with headers but no data"""
        db_path = os.path.join(temp_dir, "test.db")

        result = run_csv_to_sqlite(db_path, empty_csv)

        assert result.returncode == 0
        assert "Successfully imported 0 rows into table 'empty'" in result.stdout

        # Verify table exists but is empty
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM empty")
        count = cursor.fetchone()[0]
        assert count == 0
        conn.close()

    def test_nonexistent_csv(self, temp_dir):
        """Test error handling for nonexistent CSV file"""
        db_path = os.path.join(temp_dir, "test.db")
        nonexistent_csv = os.path.join(temp_dir, "nonexistent.csv")

        result = run_csv_to_sqlite(db_path, nonexistent_csv)

        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_no_arguments(self):
        """Test error handling when no arguments provided"""
        result = subprocess.run([
            sys.executable, 'csv_to_sqlite.py'
        ], capture_output=True, text=True)

        assert result.returncode == 1
        assert "Usage:" in result.stderr

    def test_one_argument(self):
        """Test error handling when only one argument provided"""
        result = subprocess.run([
            sys.executable, 'csv_to_sqlite.py', 'test.db'
        ], capture_output=True, text=True)

        assert result.returncode == 1
        assert "Usage:" in result.stderr

    def test_complex_headers(self, temp_dir):
        """Test with various column name types"""
        csv_path = os.path.join(temp_dir, "complex.csv")
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['simple', 'with_underscore', 'CamelCase', 'number123'])
            writer.writerow(['a', 'b', 'c', 'd'])

        db_path = os.path.join(temp_dir, "test.db")
        result = run_csv_to_sqlite(db_path, csv_path)

        assert result.returncode == 0

        # Verify all columns exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='complex'")
        schema = cursor.fetchone()[0]
        assert "simple TEXT" in schema
        assert "with_underscore TEXT" in schema
        assert "CamelCase TEXT" in schema
        assert "number123 TEXT" in schema
        conn.close()

    def test_assignment_schema_zip_county(self, temp_dir):
        """Test with actual assignment schema for zip_county"""
        csv_path = os.path.join(temp_dir, "zip_county.csv")
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['zip', 'default_state', 'county', 'county_state',
                           'state_abbreviation', 'county_code', 'zip_pop',
                           'zip_pop_in_county', 'n_counties', 'default_city'])
            writer.writerow(['02138', 'MA', 'Middlesex County', 'MA', 'MA',
                           '017', '29000', '29000', '1', 'Cambridge'])

        db_path = os.path.join(temp_dir, "test.db")
        result = run_csv_to_sqlite(db_path, csv_path)

        assert result.returncode == 0

        # Verify schema matches assignment expectations
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='zip_county'")
        schema = cursor.fetchone()[0]

        expected_columns = ['zip', 'default_state', 'county', 'county_state',
                          'state_abbreviation', 'county_code', 'zip_pop',
                          'zip_pop_in_county', 'n_counties', 'default_city']

        for col in expected_columns:
            assert f"{col} TEXT" in schema

        conn.close()

    def test_assignment_schema_county_health_rankings(self, temp_dir):
        """Test with actual assignment schema for county_health_rankings"""
        csv_path = os.path.join(temp_dir, "county_health_rankings.csv")
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['state', 'county', 'state_code', 'county_code', 'year_span',
                           'measure_name', 'measure_id', 'numerator', 'denominator',
                           'raw_value', 'confidence_interval_lower_bound',
                           'confidence_interval_upper_bound', 'data_release_year', 'fipscode'])
            writer.writerow(['MA', 'Middlesex County', '25', '017', '2020-2022',
                           'Adult obesity', '11', '60771.02', '263078', '0.23',
                           '0.22', '0.24', '2023', '25017'])

        db_path = os.path.join(temp_dir, "test.db")
        result = run_csv_to_sqlite(db_path, csv_path)

        assert result.returncode == 0

        # Verify schema matches assignment expectations
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='county_health_rankings'")
        schema = cursor.fetchone()[0]

        expected_columns = ['state', 'county', 'state_code', 'county_code', 'year_span',
                          'measure_name', 'measure_id', 'numerator', 'denominator',
                          'raw_value', 'confidence_interval_lower_bound',
                          'confidence_interval_upper_bound', 'data_release_year', 'fipscode']

        for col in expected_columns:
            assert f"{col} TEXT" in schema

        conn.close()