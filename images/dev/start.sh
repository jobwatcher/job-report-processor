#!/bin/sh

echo "Installing requirements and launching report processor in dir ${PWD}"

pip install -r src/requirements.txt
python3 src/main.py
