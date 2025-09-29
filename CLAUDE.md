# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a homework assignment for building a data pipeline and web API that processes county health data. The project consists of two main components:

1. **CSV to SQLite converter** (`csv_to_sqlite.py`) - Converts CSV files to SQLite database tables
2. **Web API** - FastAPI/Flask application exposing a `/county_data` endpoint

## Development Commands

### Database Setup
```bash
# Create SQLite database from CSV files
python3 csv_to_sqlite.py data.db zip_county.csv
python3 csv_to_sqlite.py data.db county_health_rankings.csv

# Verify database contents
sqlite3 data.db
.schema zip_county
select count(*) from zip_county;
.schema county_health_rankings
select count(*) from county_health_rankings;
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run API locally
uvicorn main:app --reload
# OR use the deployment startup script
python run.py
```

### Testing
```bash
# Test missing keys (should return 400)
curl -X POST -H 'Content-Type: application/json' -d '{}' http://localhost:8000/county_data

# Test teapot behavior (should return 418)
curl -X POST -H 'Content-Type: application/json' -d '{"zip":"02138","measure_name":"Adult obesity","coffee":"teapot"}' http://localhost:8000/county_data

# Test valid request (should return 200)
curl -X POST -H 'Content-Type: application/json' -d '{"zip":"02138","measure_name":"Adult obesity"}' http://localhost:8000/county_data
```

## Architecture

### Data Model
- **zip_county table**: Maps ZIP codes to counties (zip, county, state_abbreviation, county_code, etc.)
- **county_health_rankings table**: Health measures by county (state, county, measure_name, raw_value, etc.)
- All columns stored as TEXT type for simplicity

### API Contract
- **Endpoint**: `POST /county_data`
- **Required fields**: `zip` (5-digit string), `measure_name` (from predefined list)
- **Special behavior**: `coffee: "teapot"` returns HTTP 418
- **Valid measure names**: "Adult obesity", "Violent crime rate", "Unemployment", etc. (see design doc)

### Query Logic
1. Look up ZIP code in `zip_county` table to find matching counties
2. For each county, query `county_health_rankings` for the specified measure
3. Return all matching rows as JSON array
4. Handle edge cases: ZIP maps to multiple counties, multiple years of data per county

### Security Requirements
- **SQL Injection Protection**: Always use parameterized queries (? placeholders)
- **Input Validation**: Validate ZIP format (5 digits) and measure_name against whitelist
- **Error Handling**: Return appropriate HTTP status codes (400, 404, 418, 500)

### Response Format
Returns JSON array of objects with column names matching `county_health_rankings` schema:
```json
[{
  "state": "MA",
  "county": "Middlesex County",
  "measure_name": "Adult obesity",
  "raw_value": "0.23",
  "numerator": "60771.02",
  "denominator": "263078",
  ...
}]
```

## Deployment

### File Structure
- `csv_to_sqlite.py` - Database creation script
- `requirements.txt` - Python dependencies
- `README.md` - Setup and usage instructions
- `link.txt` - Deployed API endpoint URL (https://domain.com/county_data)
- `.gitignore` - Exclude __pycache__, data.db, env files
- API source files (app.py, api/, etc.)

### Deployment Platforms
- **Recommended**: Railway (excellent PostgreSQL and SQLite support, easy GitHub integration)
- **Alternative**: Render, Fly.io (good container/SQLite support)
- Include `data.db` in repository (31MB database included)

### Deployment Files
- `railway.json` - Railway platform configuration
- `Procfile` - Process configuration for Railway/Heroku
- `Dockerfile` - Container deployment configuration
- `run.py` - Python startup script that handles PORT environment variable properly
- `start.sh` - Alternative bash startup script

### Build Process
The project includes a pre-built 31MB `data.db` file with 54,553 ZIP codes and 303,864 health records. All deployment configurations use `python run.py` which properly handles the PORT environment variable for different hosting platforms.

## Testing Checklist

### Required HTTP Status Codes
- **200**: Valid request with results
- **400**: Missing required fields or malformed ZIP
- **404**: ZIP not found, measure not found, or no data for ZIP/measure pair
- **418**: `coffee: "teapot"` present in request
- **500**: Internal server errors

### Edge Cases
- ZIP codes mapping to multiple counties
- Multiple years of data per county/measure
- SQL injection attempts (must be blocked)
- Invalid measure names
- Missing database tables

## Assignment Requirements

### Deliverables
- Working `csv_to_sqlite.py` script
- Deployed web API with `/county_data` endpoint
- All required files: README.md, requirements.txt, .gitignore, link.txt
- Code comments documenting any AI assistance used

### Grading Criteria
- CSV script works on arbitrary valid CSVs
- API implements exact specification including error codes
- SQL injection protection via parameterized queries
- Proper input validation and error handling
- Deployment accessibility and stability