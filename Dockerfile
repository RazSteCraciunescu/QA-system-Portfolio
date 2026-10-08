FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/relayhub

RUN groupadd --system relayhub \
    && useradd --system --gid relayhub --home-dir /opt/relayhub relayhub

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN chown -R relayhub:relayhub /opt/relayhub

USER relayhub
EXPOSE 8080

CMD ["python", "-m", "uvicorn", "app.gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
