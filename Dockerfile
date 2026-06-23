FROM python:3.12-slim

RUN set -eux; \
    . /etc/os-release; \
    for file in /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources; do \
      if [ -f "$file" ]; then sed -i 's/Components: main/Components: main contrib non-free-firmware/' "$file"; fi; \
    done; \
    apt-get update; \
    apt-get install -y --no-install-recommends zfsutils-linux; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY unifi_metrics ./unifi_metrics
COPY README.md ./

EXPOSE 9130
CMD ["python", "-m", "unifi_metrics"]
