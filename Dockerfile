FROM python:3.10-slim

WORKDIR /app

COPY . /app/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py collectstatic --noinput
