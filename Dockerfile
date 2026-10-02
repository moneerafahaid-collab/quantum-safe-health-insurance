FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV QSHIELD_HOST=0.0.0.0
EXPOSE 8080

CMD ["sh", "-c", "python -m qshield serve --host 0.0.0.0 --port ${PORT:-8080}"]
