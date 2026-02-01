FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --no-root

COPY . .
RUN poetry install --no-interaction --no-ansi

EXPOSE 3301

CMD ["uvicorn", "null_engine.main:app", "--host", "0.0.0.0", "--port", "3301"]
