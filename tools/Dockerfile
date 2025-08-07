FROM alpine AS builder

# set a directory for build icu
WORKDIR /home/icu

# copy all the files to the container
COPY tools/icu .

# install python dependencies
RUN apk update
RUN apk add build-base
RUN apk add pkgconf
RUN apk add icu-dev
RUN apk add sqlite-dev

RUN gcc -shared icu.c -g -o libsqliteicu.so -fPIC `pkg-config --libs --cflags icu-uc icu-io`

#
# Build final image
#

FROM alpine 

# set a directory for the app
WORKDIR /home/nnmbot

# copy all the files to the container
COPY . .
COPY --from=builder /home/icu/libsqliteicu.so .
# install python dependencies
RUN apk update
RUN apk add python3
RUN apk add py3-pip
RUN apk add icu-libs
RUN python3 -m venv /home/nnmbot/venv
RUN . /home/nnmbot/venv/bin/activate
ENV PATH=/home/nnmbot/venv/bin:$PATH
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pysocks

