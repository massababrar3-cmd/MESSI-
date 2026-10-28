FROM node:24-bookworm-slim AS web
WORKDIR /build
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package.json
RUN --mount=type=secret,id=build_ca if [ -f /run/secrets/build_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/build_ca; fi; npm ci
COPY frontend frontend
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend MESSI_DATA_DIR=/data
COPY backend/requirements.txt backend/requirements.txt
RUN --mount=type=secret,id=build_ca if [ -f /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca; fi; pip install --no-cache-dir --require-hashes -r backend/requirements.txt && useradd --uid 10001 --create-home messi && mkdir /data && chown messi:messi /data
COPY backend backend
COPY scripts scripts
COPY --from=web /build/frontend/dist frontend/dist
RUN chmod -R a+rX /app
USER messi
EXPOSE 8000
CMD ["python", "scripts/dev.py", "--production"]
