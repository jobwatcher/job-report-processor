# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /report-processor
    
RUN <<EOF
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get -qq -y install  --no-install-recommends \
        curl  \
        rustc \
        cargo
    rm -rf /var/lib/apt/lists/*
EOF



VOLUME ["/report-processor/scrapped_data"]
VOLUME ["/report-processor/src"]
VOLUME ["/report-processor/venv"]

COPY src /report-processor/src

CMD ["/bin/bash", "/report-processor/src/start.sh"]

