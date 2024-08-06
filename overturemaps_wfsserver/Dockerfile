FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    g++ \
    nano \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz | \
    tar -C /usr/local/bin -xzv

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN rm /usr/local/lib/python3.10/site-packages/gisserver/operations/wfs20.py
COPY ./workarounds/wfs20.py /usr/local/lib/python3.10/site-packages/gisserver/operations/

EXPOSE 8000

CMD ["sh", "-c", "dockerize -wait tcp://db:5432 -timeout 60s && python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

