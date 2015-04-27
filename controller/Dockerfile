FROM ubuntu:14.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -fy python-pip python-dev
ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

RUN mkdir -p /app/paas
COPY . /app/paas/

WORKDIR /app/paas

EXPOSE 80

CMD /app/paas/bin/app
