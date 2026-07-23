FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY pyproject.toml README.md requirements.lock /app/
COPY src /app/src
COPY scripts /app/scripts
COPY tests/fixtures /app/tests/fixtures

RUN pip install --no-cache-dir .

USER appuser

ENTRYPOINT ["python", "-m", "paccaassure_common_tools.cli.main"]
