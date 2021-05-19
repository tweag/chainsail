##############################################################################
# BASE
##############################################################################
FROM python:3.8.7-slim as base

# up-to-date GCC
RUN echo 'deb http://deb.debian.org/debian testing main' >> /etc/apt/sources.list
RUN apt update -y
RUN apt install -y gcc build-essential

# Python package managers
RUN pip install --upgrade pip && pip install httpstan

ENV HTTPSTAN_PORT=8082

CMD python3 -m httpstan --port $HTTPSTAN_PORT