#!/bin/sh

echo "Installing requirements and launching report processor in dir ${PWD}"
ls -lsa 
ls -lsa src
ls -lsa scrapped_data
pip install -r src/requirements.txt
python3 ./src/main.py
