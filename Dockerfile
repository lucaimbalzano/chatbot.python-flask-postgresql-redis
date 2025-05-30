FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

#CMD ["python", "run.py"]
#CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:create_app()"]
#gunicorn -c gunicorn_config.py run:app
CMD ["gunicorn", "-c", "gunicorn_config.py", "run:app"]

