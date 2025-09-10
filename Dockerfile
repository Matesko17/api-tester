FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["pytest", "-v", "--html=reports/report.html", "--json-report", "--json-report-file=reports/report.json"]