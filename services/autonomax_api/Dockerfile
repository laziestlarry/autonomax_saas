FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1     APP_HOME=/app

WORKDIR $APP_HOME

# system deps for psycopg2-binary are not required, but keep image minimal
COPY services/autonomax_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir -r /app/requirements.txt

COPY services/autonomax_api /app/services/autonomax_api
COPY docs /app/docs

EXPOSE 8080
CMD ["uvicorn", "services.autonomax_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
