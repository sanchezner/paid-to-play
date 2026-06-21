FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

COPY bronze/ bronze/
COPY silver/ silver/
COPY gold/ gold/
COPY serving/ serving/
COPY modeling/ modeling/
COPY config/ config/
COPY jobs/ jobs/
COPY artifacts/ artifacts/

ENV PYTHONUNBUFFERED=1
ENV TRACKING_URI=sqlite:////app/mlflow.db

CMD ["python", "-m", "jobs.daily_flow"]%