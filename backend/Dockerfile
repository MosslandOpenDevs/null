FROM python:3.12-slim

WORKDIR /app

RUN pip install "poetry==2.4.1" && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --no-interaction --no-ansi --no-root --only main

COPY . .
RUN poetry install --no-interaction --no-ansi --only main

EXPOSE 3301

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3301/health/ready', timeout=4)"

CMD ["uvicorn", "null_engine.main:app", "--host", "0.0.0.0", "--port", "3301"]
