# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /report-processor

ADD start.sh start.sh
RUN chmod +x start.sh

VOLUME ["/report-processor/scrapped_data"]
VOLUME ["/report-processor/src"]

CMD ["/report-processor/start.sh"]
