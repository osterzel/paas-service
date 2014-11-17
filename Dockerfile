FROM ubuntu:1404

RUN apt-get install python-pip
RUN pip install -r requirements.txt

RUN mkdir -p /app/paas
ADD * /app/paas/

CMD /app/paas/bin/app


