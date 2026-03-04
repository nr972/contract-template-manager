FROM python:3.12-slim

WORKDIR /app

# Install git (required by GitPython)
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app/ app/
COPY data/sample/ data/sample/
COPY scripts/ scripts/

RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "ctm_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
