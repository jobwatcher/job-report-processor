# syntax=docker/dockerfile:1
ARG python=python:3.12-slim

FROM ${python} AS build

RUN python3 -m venv /report-processor/venv
ENV PATH=/report-processor/venv/bin:$PATH

COPY src/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt


FROM ${python} AS app

WORKDIR /report-processor

COPY --from=build /report-processor/venv /report-processor/venv
ENV PATH=/report-processor/venv/bin:$PATH

ADD images/dev/start.sh start.sh
RUN chmod +x start.sh

VOLUME ["/report-processor/scrapped_data"]
VOLUME ["/report-processor/src"]
VOLUME ["/report-processor/venv"]

CMD ["/report-processor/start.sh"]
