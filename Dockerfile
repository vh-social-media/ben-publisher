FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "mistralai-workflows[mistralai]"

COPY ben_publisher.py /app/ben_publisher.py

CMD ["python", "-m", "mistralai.workflows.worker", "ben_publisher"]
