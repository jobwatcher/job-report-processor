# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /report-processor

ADD images/dev/start.sh start.sh
RUN chmod +x start.sh

COPY src/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

VOLUME ["/report-processor/scrapped_data"]
VOLUME ["/report-processor/src"]

CMD ["/report-processor/start.sh"]
