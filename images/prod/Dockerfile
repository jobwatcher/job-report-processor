# syntax=docker/dockerfile:1
FROM python:3-alpine3.20

WORKDIR /report-processor
VOLUME ["/report-processor/scrapped_data"]

ADD images/prod/start.sh start.sh
RUN chmod +x start.sh

COPY src src
RUN pip install -r src/requirements.txt

CMD ["/report-processor/start.sh"]
