FROM ubuntu:xenial
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-setuptools git curl wget locales && \
    pip3 install pipenv

# Set the locale
RUN locale-gen en_US.UTF-8

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Set up data directory
RUN mkdir -p /data
WORKDIR /data
COPY . .

# Set up user
RUN adduser --disabled-password --gecos "" azuracast

USER azuracast
RUN pipenv install

CMD ["pipenv", "shell"]