# County Health Data API

This project implements a data pipeline and web API for county health rankings data.

## What this repo contains

- `csv_to_sqlite.py` - Script to convert CSV files to SQLite database tables
- `main.py` - FastAPI web application with `/county_data` endpoint
- `requirements.txt` - Python dependencies
- `data.db` - SQLite database (created by running csv_to_sqlite.py)
- `zip_county.csv` and `county_health_rankings.csv` - Test data files

## How to create the DB locally

```bash
python3 csv_to_sqlite.py data.db zip_county.csv
python3 csv_to_sqlite.py data.db county_health_rankings.csv
```

## How to run API locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at https://aacontreras20-hw4.vercel.app/

## Example curl requests

### Valid request
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"zip":"02138","measure_name":"Adult obesity"}' \
  http://localhost:8000/county_data
```

### Missing fields (returns 400)
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{}' \
  http://localhost:8000/county_data
```

### Invalid ZIP format (returns 400)
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"zip":"123","measure_name":"Adult obesity"}' \
  http://localhost:8000/county_data
```

### Teapot behavior (returns 418)
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"zip":"02138","measure_name":"Adult obesity","coffee":"teapot"}' \
  http://localhost:8000/county_data
```

## Notes about coffee=teapot behavior and expected HTTP errors

- **200**: Valid request with results
- **400**: Missing required fields or malformed ZIP code
- **404**: ZIP not found, measure not found, or no data for ZIP/measure pair
- **418**: Special teapot behavior when `coffee: "teapot"` is present
- **500**: Internal server errors

The API includes SQL injection protection via parameterized queries and validates all inputs according to the assignment specifications.

## Valid measure names

- "Violent crime rate"
- "Unemployment"
- "Children in poverty"
- "Diabetic screening"
- "Mammography screening"
- "Preventable hospital stays"
- "Uninsured"
- "Sexually transmitted infections"
- "Physical inactivity"
- "Adult obesity"
- "Premature Death"
- "Daily fine particulate matter"

## Testing

This project includes comprehensive test suites for both the CSV converter and the API.

### Run all tests
```bash
pytest
```

### Run specific test suites
```bash
# Test CSV to SQLite converter
pytest test_csv_to_sqlite.py

# Test API endpoints
pytest test_api_simple.py
```

### Test Coverage

**CSV to SQLite Tests (`test_csv_to_sqlite.py`):**
- ✅ Successful CSV import with proper schema
- ✅ Table recreation (drop and recreate)
- ✅ Empty CSV handling
- ✅ Error handling (missing files, invalid arguments)
- ✅ Complex column names
- ✅ Assignment-specific schemas (zip_county, county_health_rankings)

**API Tests (`test_api_simple.py`):**
- ✅ Valid requests returning health data
- ✅ HTTP 418 teapot behavior (`coffee: "teapot"`)
- ✅ HTTP 400 errors (missing fields, invalid ZIP format)
- ✅ HTTP 404 errors (ZIP not found, measure not found, no data)
- ✅ JSON response structure validation
- ✅ SQL injection protection
- ✅ All valid measure names acceptance

The test suite automatically creates temporary databases and starts API servers as needed, ensuring tests are isolated and reproducible.
