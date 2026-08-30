FROM mcr.microsoft.com/playwright/python:v1.46.0-focal

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY . .

# Use shell form so $PORT is properly substituted
CMD gunicorn webserver:app --bind 0.0.0.0:$PORT
