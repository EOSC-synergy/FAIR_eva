FROM ubuntu:20.04

MAINTAINER Fernando Aguilar "aguilarf@ifca.unican.es"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev git

RUN git clone https://github.com/EOSC-synergy/FAIR_eva.git

WORKDIR /FAIR_eva

RUN pip3 install -r requirements.txt

EXPOSE 5000 9090
RUN ls
CMD /FAIR_eva/web.py && /FAIR_eva/fair.py
