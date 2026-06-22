FROM python:3.12-slim

WORKDIR /app
COPY unifi_metrics ./unifi_metrics
COPY README.md ./

EXPOSE 9130
CMD ["python", "-m", "unifi_metrics"]

