#!/bin/bash

echo "Installing requirements and launching report processor in dir ${PWD}"

[[ -f "/report-processor/venv/bin/pip" && -s "/report-processor/venv/bin/pip" ]] || { 
    python3 -m venv /report-processor/venv
}

# export PATH=/report-processor/venv/bin:$PATH

/report-processor/venv/bin/pip install -r ./src/requirements.txt
# /report-processor/venv/bin/python3 ./src/main.py
/report-processor/venv/bin/python3 ./src/testbot.py