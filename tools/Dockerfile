FROM alpine

# set a directory for the app
WORKDIR /home/nnmbot

# copy all the files to the container
COPY . .

# install python dependencies
RUN apk update
RUN apk add python3
RUN apk add py3-pip
RUN python3 -m venv /home/nnmbot/venv
RUN . /home/nnmbot/venv/bin/activate
ENV PATH=/home/nnmbot/venv/bin:$PATH
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pysocks

# compile icu extension for unicode select in sqlite 
COPY icu icu
RUN apk add build-base
RUN apk add pkgconf
RUN apk add icu-dev
RUN apk add sqlite-dev

RUN gcc -shared icu/icu.c -g -o libsqliteicu.so -fPIC `pkg-config --libs --cflags icu-uc icu-io`

RUN apk del build-base
RUN apk del icu-dev
RUN apk del sqlite-dev
RUN apk del pkgconf
