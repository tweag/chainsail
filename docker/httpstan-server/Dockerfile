##############################################################################
# BASE
##############################################################################
FROM python:3.10-slim as base

# up-to-date GCC
RUN echo 'deb http://deb.debian.org/debian stable main' >> /etc/apt/sources.list
RUN apt update -y
RUN apt install -y gcc build-essential

# Python package managers
RUN pip install --upgrade pip && pip install httpstan

ENV HTTPSTAN_PORT=8082

CMD python3 -m httpstan --port $HTTPSTAN_PORT
