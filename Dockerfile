FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# uvicorn backend.main:app --reload --host 0.0.0.0 --port 3005
CMD ["uvicorn", "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "3005"]