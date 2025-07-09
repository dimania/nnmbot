FROM alpine

# set a directory for the app
WORKDIR /home/nnmbot

# copy all the files to the container
COPY . .

# install dependencies
RUN apk update
RUN apk add python3
RUN apk add py3-pip
RUN python3 -m venv /home/nnmbot/venv
RUN . /home/nnmbot/venv/bin/activate
ENV PATH=/home/nnmbot/venv/bin:$PATH
#RUN . /home/nnmbot/venv/bin/activate ;  pip install --no-cache-dir -r requirements.txt ; pip install --no-cache-dir pysocks
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pysocks
#RUN mkdir /home/nnmbot/etc
#RUN mkdir /home/nnmbot/data
#RUN mkdir /home/nnmbot/logs

#VOLUME /home/nnmbot/etc
# tell the port number the container should expose
#EXPOSE 5000
#-v /my/own/datadir:/var/lib/mysql -v /my/own/myconfig.py:/home/nnmbot/myconfig.py
# run the command
#CMD ["python", "./frontend_nnmbot.py"]
