FROM docker.io/python:3.6

COPY requirements.txt /requirements.txt

RUN pip install -r requirements.txt

COPY . /cumulus_parser
WORKDIR "/cumulus_parser"
