FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and database
COPY . .

# Expose port (default 8000, but can be overridden)
EXPOSE 8000

# Start command that uses PORT environment variable
CMD ["python", "run.py"]