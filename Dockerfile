FROM ubuntu:16.04

MAINTAINER Travis Holton <wtholton at gmail dot com>


RUN apt-get update && apt-get -y install \
      language-pack-en-base \
      python3-nose2 \
      python3-pip \
      python3.5 \
      python3.5-dev

WORKDIR /usr/local/domain-api
COPY . /usr/local/domain-api
RUN pip3 install -r requirements.txt

WORKDIR /usr/local/domain-api/catalystinnovation

EXPOSE 8000 80 443

CMD ["python3", "manage.py", "test"]
