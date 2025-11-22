FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir locust

COPY locustfile.py .

EXPOSE 8089

CMD ["locust", "-f", "locustfile.py", "--host=http://api_gateway:8080"]
