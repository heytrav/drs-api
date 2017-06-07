FROM ubuntu:16.04

MAINTAINER Travis Holton <wtholton at gmail dot com>


RUN apt-get update && apt-get -y install \
      language-pack-en-base \
      libmysqlclient-dev \
      libncurses5-dev \
      python3-nose2 \
      python3-pip \
      python3.5 \
      python3.5-dev \
      jq \
      && rm -rf /var/lib/apt/lists/*


WORKDIR /usr/local/domain-api
COPY requirements.txt /usr/local/domain-api
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/local/domain-api/

EXPOSE 8000
VOLUME ["/usr/local/domain-api"]

CMD ["python3", "manage.py", "test"]
