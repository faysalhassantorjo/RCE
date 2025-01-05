# FROM python:3.10-slim

# # RUN apt-get update && apt-get install -y build-essential
# # RUN pip install --no-cache-dir flask
# WORKDIR /realtime_code_editor

# CMD ["sleep", "infinity"]


# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for Django
EXPOSE 8000

# Start the application
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "realtime_code_editor.asgi:application"]

