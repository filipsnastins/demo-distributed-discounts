FROM python:3.9.13-slim-bullseye AS python
ARG VIRTUAL_ENV=/opt/venv
WORKDIR /app
RUN addgroup --gid 1001 app; \
  adduser --uid 1000 --gid 1001 app
# hadolint ignore=DL3008
RUN apt-get update; \
  apt-get install -y --no-install-recommends gcc libc-dev libpq-dev; \
  rm -rf /var/lib/apt/lists/*
ENV VIRTUAL_ENV=$VIRTUAL_ENV
ENV PATH=$VIRTUAL_ENV/bin:$PATH

FROM python AS build-base
ARG PIP_VERSION=22.1.2
ARG POETRY_VERSION=1.1.13
RUN python -m pip install --no-cache-dir -U \
  "pip==$PIP_VERSION" \
  "poetry==$POETRY_VERSION"; \
  virtualenv "$VIRTUAL_ENV"
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

FROM build-base AS dist
COPY . .
RUN chmod +x docker-entrypoint.sh; \
  poetry build; \
  poetry install --no-dev

FROM build-base AS test
RUN poetry install
COPY . .
RUN poetry install; \
  poetry run test-ci

FROM python
ARG TZ=Europe/Riga
ARG HOST=0.0.0.0
ARG PORT=5000
COPY --from=test /app/test_results ./test_results
COPY --from=dist /opt/venv /opt/venv
COPY --from=dist /app .
USER app
ENV TZ=$TZ
ENV HOST=$HOST
ENV PORT=$PORT
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "-c", "deploy/gunicorn_config.py", "app:create_app()"]
