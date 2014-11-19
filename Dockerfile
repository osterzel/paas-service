FROM ubuntu-debootstrap:1404

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get install python-pip
RUN pip install -r requirements.txt

RUN mkdir -p /app/paas
ADD * /app/paas/

CMD /app/paas/bin/app


