FROM python:3.12-slim
RUN pip install --no-cache-dir fastapi==0.115.12 uvicorn==0.34.2
COPY main.py /app/main.py
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
