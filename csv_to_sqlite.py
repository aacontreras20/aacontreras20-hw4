#!/usr/bin/env python3
"""
CSV to SQLite converter script
Converts CSV files into SQLite database tables with all columns as TEXT type.

Usage: python3 csv_to_sqlite.py <database.db> <input.csv>
"""

import sys
import csv
import sqlite3
import os
from pathlib import Path

def main():
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 csv_to_sqlite.py <database.db> <input.csv>", file=sys.stderr)
        sys.exit(1)

    database_path = sys.argv[1]
    csv_path = sys.argv[2]

    # Validate CSV file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found", file=sys.stderr)
        sys.exit(1)

    # Extract table name from CSV filename (basename without extension)
    table_name = Path(csv_path).stem

    try:
        # Connect to SQLite database (creates if doesn't exist)
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Read CSV and get headers
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            # Detect delimiter and read headers
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.reader(csvfile, delimiter=delimiter)
            headers = next(reader)

            # Validate headers are not empty
            if not headers:
                print(f"Error: No headers found in CSV file '{csv_path}'", file=sys.stderr)
                sys.exit(1)

            # Create table schema with all columns as TEXT
            columns_def = ', '.join([f"{header} TEXT" for header in headers])
            create_table_sql = f"CREATE TABLE {table_name} ({columns_def})"

            # Drop table if exists (for reproducible runs)
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

            # Create new table
            cursor.execute(create_table_sql)

            # Prepare insert statement with parameterized placeholders
            placeholders = ', '.join(['?' for _ in headers])
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

            # Read all rows and insert in batch
            rows = []
            for row in reader:
                # Pad or truncate row to match header count
                normalized_row = row[:len(headers)] + [''] * (len(headers) - len(row))
                rows.append(normalized_row)

            # Bulk insert all rows
            cursor.executemany(insert_sql, rows)

            # Commit changes
            conn.commit()

            print(f"Successfully imported {len(rows)} rows into table '{table_name}'")
            print(f"Database: {database_path}")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}", file=sys.stderr)
        sys.exit(1)
    except csv.Error as e:
        print(f"CSV error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()