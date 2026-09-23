FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dev/test tooling is opt-in so the runtime image stays lean.
ARG INSTALL_DEV=false

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && if [ "${INSTALL_DEV}" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi

COPY pytest.ini ./
COPY app ./app
COPY tests ./tests

RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
