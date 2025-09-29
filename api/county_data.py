"""
County Health Data API endpoint
Vercel serverless function implementation.

This implementation was created with assistance from Claude AI (Anthropic).
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3
import re
import os
import csv
import tempfile

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic validation errors to 400 Bad Request"""
    missing_fields = []
    for error in exc.errors():
        if error["type"] == "missing":
            field_name = error["loc"][-1]
            missing_fields.append(field_name)

    if missing_fields:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Missing required fields: {', '.join(missing_fields)}"}
        )

    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request data"}
    )

# Valid measure names as specified in the assignment
VALID_MEASURES = {
    "Violent crime rate",
    "Unemployment",
    "Children in poverty",
    "Diabetic screening",
    "Mammography screening",
    "Preventable hospital stays",
    "Uninsured",
    "Sexually transmitted infections",
    "Physical inactivity",
    "Adult obesity",
    "Premature Death",
    "Daily fine particulate matter"
}

class CountyDataRequest(BaseModel):
    zip: str
    measure_name: str
    coffee: Optional[str] = None

def get_db_connection():
    """Get SQLite database connection"""
    # For Vercel, try to find the database file
    possible_paths = [
        "data.db",
        "../data.db",
        "/tmp/data.db",
        os.path.join(os.path.dirname(__file__), "..", "data.db"),
        os.path.join(os.path.dirname(__file__), "data.db")
    ]

    for db_path in possible_paths:
        if os.path.exists(db_path):
            return sqlite3.connect(db_path)

    raise HTTPException(
        status_code=500,
        detail="Database not found. Please ensure data.db exists."
    )

def validate_zip_code(zip_code: str) -> bool:
    """Validate ZIP code is exactly 5 digits"""
    return bool(re.match(r'^\d{5}$', zip_code))

@app.post("/")
async def get_county_data(request: CountyDataRequest):
    """
    Get county health data by ZIP code and measure name.

    Returns health ranking data for all counties that match the given ZIP code
    and measure name.
    """

    # Special teapot behavior
    if request.coffee == "teapot":
        raise HTTPException(status_code=418, detail={"error": "I'm a teapot"})

    # Note: Required field validation is handled by Pydantic and the exception handler

    # Validate ZIP code format
    if not validate_zip_code(request.zip):
        raise HTTPException(
            status_code=400,
            detail="ZIP code must be exactly 5 digits"
        )

    # Validate measure name
    if request.measure_name not in VALID_MEASURES:
        raise HTTPException(
            status_code=404,
            detail=f"Measure '{request.measure_name}' not found"
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Look up counties for the given ZIP code
        zip_query = """
            SELECT county, county_code, state_abbreviation
            FROM zip_county
            WHERE zip = ?
        """
        cursor.execute(zip_query, (request.zip,))
        counties = cursor.fetchall()

        if not counties:
            raise HTTPException(
                status_code=404,
                detail=f"ZIP code {request.zip} not found"
            )

        # Step 2: For each county, get health ranking data
        all_results = []

        for county_name, county_code, state_abbrev in counties:
            health_query = """
                SELECT State, County, State_code, County_code, Year_span,
                       Measure_name, Measure_id, Numerator, Denominator,
                       Raw_value, Confidence_Interval_Lower_Bound,
                       Confidence_Interval_Upper_Bound, Data_Release_Year, fipscode
                FROM county_health_rankings
                WHERE Measure_name = ? AND County = ?
            """
            cursor.execute(health_query, (request.measure_name, county_name))
            health_rows = cursor.fetchall()

            # Convert rows to dictionaries
            column_names = [
                "state", "county", "state_code", "county_code", "year_span",
                "measure_name", "measure_id", "numerator", "denominator",
                "raw_value", "confidence_interval_lower_bound",
                "confidence_interval_upper_bound", "data_release_year", "fipscode"
            ]

            for row in health_rows:
                result_dict = dict(zip(column_names, row))
                all_results.append(result_dict)

        # If no health data found for any county
        if not all_results:
            raise HTTPException(
                status_code=404,
                detail=f"No health data found for ZIP {request.zip} and measure '{request.measure_name}'"
            )

        return all_results

    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500,
            detail="Database error occurred"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    finally:
        if 'conn' in locals():
            conn.close()

# For Vercel serverless functions
from mangum import Mangum

handler = Mangum(app)