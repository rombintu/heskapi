FROM python:3.10.9-alpine3.16
COPY requirements.txt requirements.txt
RUN apk add --no-cache make build-base gcc libcurl libc-dev pkgconfig gpgme-dev python3-dev tzdata musl-locales musl-locales-lang && rm -rf /var/cache/apk/*
RUN pip install -r requirements.txt
COPY . /opt/
WORKDIR /opt
CMD ["make", "run"]